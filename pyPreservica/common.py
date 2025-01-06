"""
Base class for authenticated API calls used by Entity, Content and Upload

Manages the authentication token lifetime and namespace versions.

author:     James Carr
licence:    Apache License 2.0

"""
import configparser
import functools
import hashlib
import json
import logging
import os
import platform
import re
import sys
import threading
import time
import unicodedata
import xml.etree.ElementTree
from enum import Enum
from pathlib import Path
import pyotp
from requests import Response, Session
from urllib3.util import Retry
import requests
from requests.adapters import HTTPAdapter

import pyPreservica

logger = logging.getLogger(__name__)

NS_XIP_ROOT = "http://preservica.com/XIP/"
NS_ENTITY_ROOT = "http://preservica.com/EntityAPI/"
NS_RM_ROOT = "http://preservica.com/RetentionManagement/"
NS_SEC_ROOT = "http://preservica.com/SecurityAPI"

NS_WORKFLOW = "http://workflow.preservica.com"

NS_ADMIN = "http://preservica.com/AdminAPI"

NS_XIP_V6 = "http://preservica.com/XIP/v6.0"
NS_ENTITY = "http://preservica.com/EntityAPI/v6.0"

HEADER_TOKEN = "Preservica-Access-Token"

IO_PATH = "information-objects"
SO_PATH = "structural-objects"
CO_PATH = "content-objects"

HASH_BLOCK_SIZE = 65536
TIME_OUT = 62
CHUNK_SIZE = 1024 * 4


class FileHash:
    """
    A wrapper around the hashlib hash algorithms that allows an entire file to
    be hashed in a chunked manner.
    """

    def __init__(self, algorithm):
        self.algorithm = algorithm

    def get_algorithm(self):
        return self.algorithm

    def __call__(self, file):
        hash_algorithm = self.algorithm()
        with open(file, 'rb') as f:
            buf = f.read(HASH_BLOCK_SIZE)
            while len(buf) > 0:
                hash_algorithm.update(buf)
                buf = f.read(HASH_BLOCK_SIZE)
        return hash_algorithm.hexdigest()


def identifiersToDict(identifiers: set) -> dict:
    """
        Convert a set of tuples to a dict
        :param identifiers:
        :return:
    """
    result = {}
    for identifier_tuple in identifiers:
        result[identifier_tuple[0]] = identifier_tuple[1]
    return result


def strtobool(val) -> bool:
    """
    Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


def _make_stored_zipfile(base_name, base_dir, owner, group, verbose=0, dry_run=0, logger=None):
    """
    Create a non compressed zip file from all the files under 'base_dir'.


    The output zip file will be named 'base_name' + ".zip".  Returns the
    name of the output zip file.
    """
    import zipfile  # late import for breaking circular dependency

    zip_filename = base_name + ".zip"
    archive_dir = os.path.dirname(base_name)

    if archive_dir and not os.path.exists(archive_dir):
        if logger is not None:
            logger.info("creating %s", archive_dir)
        if not dry_run:
            os.makedirs(archive_dir)

    if logger is not None:
        logger.info("creating '%s' and adding '%s' to it",
                    zip_filename, base_dir)

    if not dry_run:
        with zipfile.ZipFile(zip_filename, "w", compression=zipfile.ZIP_STORED) as zf:
            path = os.path.normpath(base_dir)
            if path != os.curdir:
                zf.write(path, path)
                if logger is not None:
                    logger.info("adding '%s'", path)
            for dirpath, dirnames, filenames in os.walk(base_dir):
                for name in sorted(dirnames):
                    path = os.path.normpath(os.path.join(dirpath, name))
                    zf.write(path, path)
                    if logger is not None:
                        logger.info("adding '%s'", path)
                for name in filenames:
                    path = os.path.normpath(os.path.join(dirpath, name))
                    if os.path.isfile(path):
                        zf.write(path, path)
                        if logger is not None:
                            logger.info("adding '%s'", path)

    return zip_filename


class PagedSet:
    """
    Class to represent a page of results
    The results object contains the list of objects of interest
    """

    def __init__(self, results, has_more: bool, total: int, next_page: str):
        self.results = results
        self.has_more = bool(has_more)
        self.total = int(total)
        self.next_page = next_page

    def __str__(self):
        return self.results.__str__()

    def get_results(self):
        return self.results

    def get_total(self):
        return self.total

    def has_more_pages(self):
        return self.has_more


class Sha1FixityCallBack:
    def __call__(self, filename, full_path):
        sha = FileHash(hashlib.sha1)
        return "SHA1", sha(full_path)


class Sha256FixityCallBack:
    def __call__(self, filename, full_path):
        sha = FileHash(hashlib.sha256)
        return "SHA256", sha(full_path)


class Sha512FixityCallBack:
    def __call__(self, filename, full_path):
        sha = FileHash(hashlib.sha512)
        return "SHA512", sha(full_path)


class ReportProgressConsoleCallback:

    def __init__(self, prefix='Progress:', suffix='', length=100, fill='█', printEnd="\r"):
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.fill = fill
        self.printEnd = printEnd
        self._lock = threading.Lock()
        self.print_progress_bar(0)

    def __call__(self, value):
        with self._lock:
            values = value.split(":")
            self.total = int(values[1])
            self.current = int(values[0])
            if self.total == 0:
                percentage = 100.0
            else:
                percentage = (self.current / self.total) * 100
            self.print_progress_bar(percentage)
            if int(percentage) == int(100):
                self.print_progress_bar(100.0)
                sys.stdout.write(self.printEnd)
                sys.stdout.flush()

    def print_progress_bar(self, percentage):
        filled_length = int(self.length * (percentage / 100.0))
        bar_sym = self.fill * filled_length + '-' * (self.length - filled_length)
        sys.stdout.write(
            '\r%s |%s| (%.2f%%) %s ' % (self.prefix, bar_sym, percentage, self.suffix))
        sys.stdout.flush()


class UploadProgressConsoleCallback:

    def __init__(self, filename: str, prefix='Progress:', suffix='', length=100, fill='█', printEnd="\r"):
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.fill = fill
        self.printEnd = printEnd
        self._filename = filename
        self._size = float(Path(filename).stat().st_size)
        self._seen_so_far = 0
        self.start = time.time()
        self._lock = threading.Lock()
        self.print_progress_bar(0, 0)

    def __call__(self, bytes_amount):
        with self._lock:
            seconds = time.time() - self.start
            if seconds == 0:
                seconds = 1.0
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * float(100.0)
            rate = (self._seen_so_far / (1024 * 1024)) / seconds
            self.print_progress_bar(percentage, rate)
            if int(self._seen_so_far) == int(self._size):
                self.print_progress_bar(100.0, rate)
                sys.stdout.write(self.printEnd)
                sys.stdout.flush()

    def print_progress_bar(self, percentage, rate):
        filled_length = int(self.length * (percentage / 100.0))
        bar_sym = self.fill * filled_length + '-' * (self.length - filled_length)
        sys.stdout.write(
            '\r%s |%s| (%.2f%%) (%.2f %s) %s ' % (self.prefix, bar_sym, percentage, rate, "Mb/s", self.suffix))
        sys.stdout.flush()


class UploadProgressCallback:
    """
    Default implementation of a callback class to show upload progress of a file
    """

    def __init__(self, filename: str):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write("\r%s  %s / %s  (%.2f%%)" % (self._filename, self._seen_so_far, self._size, percentage))
            sys.stdout.flush()


class RelationshipDirection(Enum):
    FROM = "From"
    TO = "To"


class EntityType(Enum):
    """
    Enumeration of the Entity Types
    """
    ASSET = "IO"
    FOLDER = "SO"
    CONTENT_OBJECT = "CO"


class HTTPException(Exception):
    """
     Custom Exception non 404 errors
     """

    def __init__(self, reference, http_status_code, url, method_name, message):
        self.reference = reference
        self.url = url
        self.method_name = method_name
        self.http_status_code = http_status_code
        self.msg = message
        Exception.__init__(self, self.reference, self.http_status_code, self.url, self.msg)

    def __str__(self):
        return f"Calling method {self.method_name}() {self.url} returned HTTP {self.http_status_code}. {self.msg}"


class ReferenceNotFoundException(Exception):
    """
    Custom Exception for failed lookups by reference 404 Errors
    """

    def __init__(self, reference, http_status_code, url, method_name):
        self.reference = reference
        self.url = url
        self.method_name = method_name
        self.http_status_code = http_status_code
        self.msg = f"The requested reference {self.reference} is not found in the repository"
        Exception.__init__(self, self.reference, self.http_status_code, self.url, self.msg)

    def __str__(self):
        return f"Calling method {self.method_name}() {self.url} returned HTTP {self.http_status_code}. {self.msg}"


class Relationship:
    DCMI_hasFormat = "http://purl.org/dc/terms/hasFormat"
    DCMI_isFormatOf = "http://purl.org/dc/terms/isFormatOf"
    DCMI_hasPart = "http://purl.org/dc/terms/hasPart"
    DCMI_isPartOf = "http://purl.org/dc/terms/isPartOf"
    DCMI_hasVersion = "http://purl.org/dc/terms/hasVersion"
    DCMI_isVersionOf = "http://purl.org/dc/terms/isVersionOf"
    DCMI_isReferencedBy = "http://purl.org/dc/terms/isReferencedBy"
    DCMI_references = "http://purl.org/dc/terms/references"
    DCMI_isReplacedBy = "http://purl.org/dc/terms/isReplacedBy"
    DCMI_replaces = "http://purl.org/dc/terms/replaces"
    DCMI_isRequiredBy = "http://purl.org/dc/terms/isRequiredBy"
    DCMI_requires = "http://purl.org/dc/terms/requires"
    DCMI_conformsTo = "http://purl.org/dc/terms/conformsTo"

    def __init__(self, relationship_id: str, relationship_type: str, direction: RelationshipDirection, other_ref: str,
                 title: str, entity_type: EntityType, this_ref: str, api_id: str):
        self.api_id = api_id
        self.this_ref = this_ref
        self.entity_type = entity_type
        self.title = title
        self.other_ref = other_ref
        self.direction = direction
        self.relationship_type = relationship_type
        self.relationship_id = relationship_id

    def __str__(self):
        if self.direction == RelationshipDirection.FROM:
            return f"{self.this_ref} {self.relationship_type} {self.other_ref}"
        else:
            return f"{self.other_ref} {self.relationship_type} {self.this_ref}"


class IntegrityCheck:
    """
    Class to hold information about completed integrity checks
    """

    def __init__(self, check_type, success, date, adapter, fixed, reason):
        self.check_type = check_type
        self.success = bool(success)
        self.date = date
        self.adapter = adapter
        self.fixed = bool(fixed)
        self.reason = reason

    def __str__(self):
        return f"Type:\t\t\t{self.check_type}\n" \
               f"Success:\t\t\t{self.success}\n" \
               f"Date:\t{self.date}\n" \
               f"Storage Adapter:\t{self.adapter}\n"

    def __repr__(self):
        return self.__str__()

    def get_adapter(self):
        return self.adapter

    def get_success(self):
        return self.success


class Bitstream:
    """
        Class to represent the Bitstream Object or digital file in the Preservica data model
    """

    def __init__(self, filename: str, length: int, fixity: dict, content_url: str):
        self.filename = filename
        self.length = int(length)
        self.fixity = fixity
        self.content_url = content_url

    def __str__(self):
        return f"""
           Filename:       {self.filename}
           File Length:    {self.length}
           Fixity:         {self.fixity}
        """

    def __repr__(self):
        return self.__str__()


class Generation:
    """
         Class to represent the Generation Object in the Preservica data model
    """

    def __init__(self, original: bool, active: bool, format_group: str, effective_date: str, bitstreams: list):
        self.original = bool(original)
        self.active = bool(active)
        self.content_object = None
        self.format_group = format_group
        self.effective_date = effective_date
        self.bitstreams = bitstreams
        self.properties = list()
        self.formats = list()

    def __str__(self):
        return f"""
           Active:         {self.active}
           Original:       {self.original}
           Format Group:   {self.format_group}
           Effective Date: {self.effective_date}
           Formats:        {self.formats}
           Properties:     {self.properties}
           """

    def __repr__(self):
        return self.__str__()


class Entity:
    """
        Base Class of Assets, Folders and Content Objects
    """

    def __init__(self, reference: str, title: str, description: str, security_tag: str, parent: str, metadata: dict):
        self.reference = reference
        self.title = title
        self.description = description
        self.security_tag = security_tag
        self.parent = parent
        self.metadata = metadata
        self.entity_type = None
        self.path = None
        self.tag = None
        self.custom_type = None

    def __str__(self):
        return f"""
            Entity:         {self.entity_type}
            Entity Ref:     {self.reference}
            Title:          {self.title}
            Description:    {self.description}
            Security Tag:   {self.security_tag}
            Parent:         {self.parent}
            Custom Type:    {self.custom_type}
            """

    def __repr__(self):
        return self.__str__()

    def has_metadata(self) -> bool:
        return bool(self.metadata)

    def metadata_namespaces(self) -> list:
        return list(self.metadata.values())


class Folder(Entity):
    """
       Class to represent the Structural Object or Folder in the Preservica data model
    """

    def __init__(self, reference: str, title: str, description: str = None, security_tag: str = None,
                 parent: str = None, metadata: dict = None):
        super().__init__(reference, title, description, security_tag, parent, metadata)
        self.entity_type = EntityType.FOLDER
        self.path = SO_PATH
        self.tag = "StructuralObject"


class Asset(Entity):
    """
        Class to represent the Information Object or Asset in the Preservica data model
    """

    def __init__(self, reference: str, title: str, description: str = None, security_tag: str = None,
                 parent: str = None, metadata: dict = None):
        super().__init__(reference, title, description, security_tag, parent, metadata)
        self.entity_type = EntityType.ASSET
        self.path = IO_PATH
        self.tag = "InformationObject"


class ContentObject(Entity):
    """
       Class to represent the Content Object in the Preservica data model
    """

    def __init__(self, reference: str, title: str, description: str = None, security_tag: str = None,
                 parent: str = None, metadata: dict = None):
        super().__init__(reference, title, description, security_tag, parent, metadata)
        self.entity_type = EntityType.CONTENT_OBJECT
        self.representation_type = None
        self.asset = None
        self.path = CO_PATH
        self.tag = "ContentObject"


class Representation:
    """
        Class to represent the Representation Object in the Preservica data model
    """

    def __init__(self, asset: Asset, rep_type: str, name: str, url: str):
        self.asset = asset
        self.rep_type = rep_type
        self.name = name
        self.url = url

    def __str__(self):
        return f"Type:\t\t\t{self.rep_type}\n" \
               f"Name:\t\t\t{self.name}\n" \
               f"URL:\t{self.url}"

    def __repr__(self):
        return self.__str__()


def only_assets(entity: Entity):
    return bool(entity.entity_type is EntityType.ASSET)


def only_folders(entity: Entity):
    return bool(entity.entity_type is EntityType.FOLDER)


def content_api_identifier_to_type(ref: str):
    ref = ref.replace('sdb:', '')
    parts = ref.split("|")
    return tuple((EntityType(parts[0]), parts[1]))


class Thumbnail(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


def sanitize(filename) -> str:
    """
    Return a fairly safe version of the filename.

    We don't limit ourselves to ascii, because we want to keep municipality
    names, etc, but we do want to get rid of anything potentially harmful,
    and make sure we do not exceed Windows filename length limits.
    Hence, a less safe blacklist, rather than a whitelist.
    """
    blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0"]
    reserved = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    ]  # Reserved words on Windows
    filename = "".join(c for c in filename if c not in blacklist)
    # Remove all characters below code point 32
    filename = "".join(c for c in filename if 31 < ord(c))
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.rstrip(". ")  # Windows does not allow these at end
    filename = filename.strip()
    if all([x == "." for x in filename]):
        filename = "__" + filename
    if filename in reserved:
        filename = "__" + filename
    if len(filename) == 0:
        filename = "__"
    if len(filename) > 255:
        parts = re.split(r"[/\\]", filename)[-1].split(".")
        if len(parts) > 1:
            ext = "." + parts.pop()
            filename = filename[:-len(ext)]
        else:
            ext = ""
        if filename == "":
            filename = "__"
        if len(ext) > 254:
            ext = ext[254:]
        maxl = 255 - len(ext)
        filename = filename[:maxl]
        filename = filename + ext
        # Re-check last character (if there was no extension)
        filename = filename.rstrip(". ")
        if len(filename) == 0:
            filename = "__"
    return filename


class AuthenticatedAPI:
    """
        Base class for authenticated calls which need an access token
        Authenticated calls include a "Preservica-Access-Token" header in the request
    """

    def _check_if_user_has_manager_role(self):
        """
        Check if the current user has a least a manager role
        :return: None

        Throws RuntimeError if the user does not have required roles
        """
        if ('ROLE_SDB_MANAGER_USER' not in self.roles) and ('ROLE_SDB_ADMIN_USER' not in self.roles):
            logger.error(f"The AdminAPI requires the user to have ROLE_SDB_MANAGER_USER")
            raise RuntimeError(f"The API requires the user to have at least the ROLE_SDB_MANAGER_USER")

    def _find_user_roles_(self) -> list:
        """
            Get a list of roles for the user
            :return list of roles:
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f"{self.protocol}://{self.server}/api/user/details", headers=headers)
        if request.status_code == requests.codes.ok:
            roles = json.loads(str(request.content.decode('utf-8')))['roles']
            return roles
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._find_user_roles_()

    def security_tags_base(self, with_permissions: bool = False) -> dict:
        """
             Return  security tags available for the  current user

             :return: dict of security tags
             :rtype:  dict
         """

        if (self.major_version < 7) and (self.minor_version < 4) and (self.patch_version < 1):
            raise RuntimeError("security_tags API call is only available with a Preservica v6.3.1 system or higher")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        request = self.session.get(f'{self.protocol}://{self.server}/api/security/tags', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            security_tags = {}
            tags = entity_response.findall(f'.//{{{self.sec_ns}}}Tag')
            for tag in tags:
                if with_permissions:
                    permissions = []
                    for p in tag.findall(f'.//{{{self.sec_ns}}}Permission'):
                        permissions.append(p.text)
                    security_tags[tag.attrib['name']] = permissions
                else:
                    security_tags[tag.attrib['name']] = tag.attrib['name']
            return security_tags
        if request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.security_tags_base()
        else:
            logger.error(f'security_tags failed {request.status_code}')
            raise RuntimeError(request.status_code, "security_tags failed")

    def entity_from_string(self, xml_data: str) -> dict:
        """
        Create a basic entity from XML data

        :param xml_data:
        :return: dict
        """
        entity_response = xml.etree.ElementTree.fromstring(xml_data)
        reference = entity_response.find(f'.//{{{self.xip_ns}}}Ref')
        title = entity_response.find(f'.//{{{self.xip_ns}}}Title')
        security_tag = entity_response.find(f'.//{{{self.xip_ns}}}SecurityTag')
        description = entity_response.find(f'.//{{{self.xip_ns}}}Description')
        parent = entity_response.find(f'.//{{{self.xip_ns}}}Parent')
        custom_type = entity_response.find(f'.//{{{self.xip_ns}}}CustomType')

        if hasattr(parent, 'text'):
            parent = parent.text
        else:
            parent = None

        fragments = entity_response.findall(f'.//{{{self.entity_ns}}}Metadata/{{{self.entity_ns}}}Fragment')
        metadata = {}
        for fragment in fragments:
            metadata[fragment.text] = fragment.attrib['schema']

        entity_dict = {'reference': reference.text, 'title': title.text if hasattr(title, 'text') else None,
                       'description': description.text if hasattr(description, 'text') else None,
                       'security_tag': security_tag.text, 'parent': parent, 'metadata': metadata}

        if hasattr(custom_type, 'text'):
            entity_dict['CustomType'] = custom_type.text

        return entity_dict

    def edition(self) -> str:
        """
        Return the edition of this tenancy
        """
        if self.major_version < 8 and self.minor_version < 3:
            raise RuntimeError("Entitlement  API is only available when connected to a v7.3 System")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json'}

        response = self.session.get(f'{self.protocol}://{self.server}/api/entitlement/edition', headers=headers)

        if response.status_code == requests.codes.ok:
            return response.json()['edition']
        elif response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.edition()
        else:
            exception = HTTPException("", response.status_code, response.url,
                                      "edition", response.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def __version_namespace__(self):
        """
        Generate version specific namespaces from the server version
        """
        if self.major_version > 6:
            self.xip_ns = f"{NS_XIP_ROOT}v{self.major_version}.{self.minor_version}"
            self.entity_ns = f"{NS_ENTITY_ROOT}v{self.major_version}.{self.minor_version}"
            self.rm_ns = f"{NS_RM_ROOT}v{6}.{2}"
            self.sec_ns = f"{NS_SEC_ROOT}/v{self.major_version}.{self.minor_version}"
            self.admin_ns = f"{NS_ADMIN}/v{self.major_version}.{self.minor_version}"

        if self.major_version == 6:
            if self.minor_version < 2:
                self.xip_ns = NS_XIP_V6
                self.entity_ns = NS_ENTITY
            else:
                self.xip_ns = f"{NS_XIP_ROOT}v{self.major_version}.{self.minor_version}"
                self.entity_ns = f"{NS_ENTITY_ROOT}v{self.major_version}.{self.minor_version}"
                self.rm_ns = f"{NS_RM_ROOT}v{self.major_version}.{2}"
                self.sec_ns = f"{NS_SEC_ROOT}/v{self.major_version}.{self.minor_version}"
                self.admin_ns = f"{NS_ADMIN}/v{self.major_version}.{self.minor_version}"

    def __version_number__(self):
        """
        Determine the version number of the server
        """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/versiondetails/version',
                                   headers=headers)
        if request.status_code == requests.codes.ok:
            xml_ = str(request.content.decode('utf-8'))
            version = xml_[xml_.find("<CurrentVersion>") + len("<CurrentVersion>"):xml_.find("</CurrentVersion>")]
            version_numbers = version.split(".")
            self.major_version = int(version_numbers[0])
            self.minor_version = int(version_numbers[1])
            self.patch_version = int(version_numbers[2])
            return version
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.__version_number__()
        else:
            logger.error(f"version number failed with http response {request.status_code}")
            logger.error(str(request.content))
            RuntimeError(request.status_code, "version number failed")

    def __str__(self):
        return f"pyPreservica version: {pyPreservica.__version__}  (Preservica 7.0 Compatible) " \
               f"Connected to: {self.server} Preservica version: {self.version} as {self.username} " \
               f"in tenancy {self.tenant}"

    def __repr__(self):
        return self.__str__()

    def save_config(self):
        config = configparser.RawConfigParser(interpolation=None)
        config['credentials'] = {'username': self.username, 'password': self.password, 'tenant': self.tenant,
                                 'server': self.server}
        if self.two_fa_secret_key is not None:
            config['credentials']['twoFactorToken'] = self.two_fa_secret_key

        with open('credentials.properties', 'wt', encoding="utf-8") as configfile:
            config.write(configfile)

    def manager_token(self, username: str, password: str):
        data = {'username': username, 'password': password, 'tenant': self.tenant}
        response = self.session.post(f'{self.protocol}://{self.server}/api/accesstoken/login', data=data)
        if response.status_code == requests.codes.ok:
            return response.json()['token']
        else:
            msg = "Could not generate valid manager approval password"
            logger.error(msg)
            logger.error(response.status_code)
            logger.error(str(response.content))
            RuntimeError(response.status_code, "Could not generate valid manager approval token")

    def __token__(self):
        """
            Generate am API token to use to authenticate calls
            :return: API Token
        """
        logger.debug("Token Expired Requesting New Token")
        if self.shared_secret is False:
            if self.tenant is None:
                data = {'username': self.username, 'password': self.password, 'includeUserDetails': 'true'}
            else:
                data = {'username': self.username, 'password': self.password, 'tenant': self.tenant}
            response = self.session.post(f'{self.protocol}://{self.server}/api/accesstoken/login', data=data)
            if response.status_code == requests.codes.ok:
                if self.tenant is None:
                    self.tenant = response.json()['tenant']
                return response.json()['token']
            else:
                if 'message' in response.json():
                    if response.json()['message'] == "needs.2fa":
                        logger.debug("2FA Found")
                        if self.tenant is None:
                            self.tenant = response.json()['tenant']
                        if self.two_fa_secret_key:
                            totp = pyotp.TOTP(self.two_fa_secret_key)
                            data = {'username': self.username,
                                    'continuationToken': response.json()['continuationToken'],
                                    'tenant': self.tenant, 'twoFactorToken': totp.now()}
                            response_2fa = self.session.post(
                                f'{self.protocol}://{self.server}/api/accesstoken/complete-2fa',
                                data=data)
                            if response_2fa.status_code == requests.codes.ok:
                                return response_2fa.json()['token']
                            else:
                                msg = "Failed to create a 2FA authentication token. Check your credentials are correct"
                                logger.error(msg)
                                logger.error(str(response.content))
                                raise RuntimeError(response.status_code, msg)
                        else:
                            msg = "2FA twoFactorToken required to authenticate against this account using 2FA"
                            logger.error(msg)
                            logger.error(str(response.content))
                            raise RuntimeError(response.status_code, msg)
                    if response.json()['message'] == "needs.2fa.setup":
                        msg = "2FA is activated but not yet set up"
                        logger.error(msg)
                        logger.error(str(response.content))
                        raise RuntimeError(response.status_code, msg)
                msg = "Failed to create a password based authentication token. Check your credentials are correct"
                logger.error(msg)
                logger.error(str(response.content))
                raise RuntimeError(response.status_code, msg)

        if self.shared_secret is True:
            endpoint = "api/accesstoken/acquire-external"
            timestamp = int(time.time())
            to_hash = f"preservica-external-auth{timestamp}{self.username}{self.password}"
            sha1 = hashlib.sha1()
            sha1.update(to_hash.encode(encoding='utf-8'))
            data = {"username": self.username, "tenant": self.tenant, "timestamp": timestamp, "hash": sha1.hexdigest()}
            response = self.session.post(f'{self.protocol}://{self.server}/{endpoint}', data=data)
            if response.status_code == requests.codes.ok:
                return response.json()['token']
            else:
                msg = "Failed to create a shared secret authentication token. Check your credentials are correct"
                logger.error(msg)
                raise RuntimeError(response.status_code, msg)

    def __init__(self, username: str = None, password: str = None, tenant: str = None, server: str = None,
                 use_shared_secret: bool = False, two_fa_secret_key: str = None,
                 protocol: str = "https", request_hook=None, credentials_path: str = 'credentials.properties'):

        config = configparser.ConfigParser(interpolation=configparser.Interpolation())
        config.read(os.path.relpath(credentials_path), encoding='utf-8')
        self.session: Session = requests.Session()

        if request_hook is not None:
            self.session.hooks['response'].append(request_hook)

        retries = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[502, 503, 504],
            allowed_methods=Retry.DEFAULT_ALLOWED_METHODS
        )

        self.shared_secret: bool = bool(use_shared_secret)
        self.protocol = protocol
        self.two_fa_secret_key = two_fa_secret_key

        self.session.mount(f'{self.protocol}://', HTTPAdapter(max_retries=retries))

        self.session.request = functools.partial(self.session.request, timeout=TIME_OUT)

        if not two_fa_secret_key:
            two_fa_secret_key = os.environ.get('PRESERVICA_2FA_TOKEN')
            if two_fa_secret_key is None:
                try:
                    two_fa_secret_key = config['credentials']['twoFactorToken']
                except KeyError:
                    pass
        self.two_fa_secret_key = two_fa_secret_key
        if not username:
            username = os.environ.get('PRESERVICA_USERNAME')
            if username is None:
                try:
                    username = config['credentials']['username']
                except KeyError:
                    pass
        if not username:
            msg = "No valid username found in method arguments, environment variables or credentials.properties file"
            logger.error(msg)
            raise RuntimeError(msg)
        else:
            self.username = username

        if not password:
            password = os.environ.get('PRESERVICA_PASSWORD')
            if password is None:
                try:
                    password = config['credentials']['password']
                except KeyError:
                    pass
        if not password:
            msg = "No valid password found in method arguments, environment variables or credentials.properties file"
            logger.error(msg)
            raise RuntimeError(msg)
        else:
            self.password = password

        if not tenant:
            tenant = os.environ.get('PRESERVICA_TENANT')
            if tenant is None:
                try:
                    tenant = config['credentials']['tenant']
                except KeyError:
                    pass
        if not tenant:
            msg = "No valid tenant found in method arguments, environment variables or credentials.properties file"
            logger.debug(msg)
        self.tenant = tenant

        if not server:
            server = os.environ.get('PRESERVICA_SERVER')
            if server is None:
                try:
                    server = config['credentials']['server']
                except KeyError:
                    pass
        if not server:
            msg = "No valid server found in method arguments, environment variables or credentials.properties file"
            logger.error(msg)
            raise RuntimeError(msg)
        else:
            self.server = server

        self.token = self.__token__()
        self.version = self.__version_number__()
        self.__version_namespace__()
        self.roles = self._find_user_roles_()

        self.session.headers.update({'User-Agent': f'pyPreservica SDK/({pyPreservica.__version__}) '
                                                   f' ({platform.platform()}/{os.name}/{sys.platform})'})

        logger.debug(self.xip_ns)
        logger.debug(self.entity_ns)
