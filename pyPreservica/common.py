"""
Base class for authenticated API calls used by Entity, Content and Upload
"""

import configparser
import hashlib
import os
import sys
import threading
import time
import xml.etree.ElementTree
from enum import Enum
import requests

import pyPreservica

CHUNK_SIZE = 1024 * 2

NS_XIPV6 = "http://preservica.com/XIP/v6.0"
NS_XIPV61 = "http://preservica.com/XIP/v6.1"
NS_XIPV62 = "http://preservica.com/XIP/v6.2"

NS_ENTITY = "http://preservica.com/EntityAPI/v6.0"
NS_ENTITY61 = "http://preservica.com/EntityAPI/v6.1"
NS_ENTITY62 = "http://preservica.com/EntityAPI/v6.2"

namespace = {'xip': NS_XIPV6, 'v6': NS_ENTITY}
HEADER_TOKEN = "Preservica-Access-Token"

IO_PATH = "information-objects"
SO_PATH = "structural-objects"
CO_PATH = "content-objects"

HASH_BLOCKSIZE = 65536


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
        with open(file, 'rb') as afile:
            buf = afile.read(HASH_BLOCKSIZE)
            while len(buf) > 0:
                hash_algorithm.update(buf)
                buf = afile.read(HASH_BLOCKSIZE)
        return hash_algorithm.hexdigest()


def only_assets(entity):
    return bool(entity.entity_type is EntityType.ASSET)


def only_folders(entity):
    return bool(entity.entity_type is EntityType.FOLDER)


class PagedSet:
    """
    Class to represent a page of results
    The results object contains the list of objects of interest
    """

    def __init__(self, results, has_more, total, next_page):
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


class UploadProgressCallback:
    """
    Default implementation of a callback class to show upload progress of a file
    """

    def __init__(self, filename):
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


class Representation:
    """
        Class to represent the Representation Object in the Preservica data model
    """

    def __init__(self, asset, rep_type, name, url):
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


class Bitstream:
    """
        Class to represent the Bitstream Object or digital file in the Preservica data model
    """

    def __init__(self, filename, length, fixity, content_url):
        self.filename = filename
        self.length = int(length)
        self.fixity = fixity
        self.content_url = content_url

    def __str__(self):
        return f"Filename:\t\t\t{self.filename}\n" \
               f"FileSize:\t\t\t{self.length}\n" \
               f"Content:\t{self.content_url}\n" \
               f"Fixity:\t{self.fixity}"

    def __repr__(self):
        return self.__str__()


class Generation:
    """
         Class to represent the Generation Object in the Preservica data model
     """

    def __init__(self, original, active, format_group, effective_date, bitstreams):
        self.original = original
        self.active = active
        self.content_object = None
        self.format_group = format_group
        self.effective_date = effective_date
        self.bitstreams = bitstreams

    def __str__(self):
        return f"Active:\t\t\t{self.active}\n" \
               f"Original:\t\t\t{self.original}\n" \
               f"Format_group:\t{self.format_group}"

    def __repr__(self):
        return self.__str__()


class Entity:
    """
        Base Class of Assets, Folders and Content Objects
    """

    def __init__(self, reference, title, description, security_tag, parent, metadata):
        self.reference = reference
        self.title = title
        self.description = description
        self.security_tag = security_tag
        self.parent = parent
        self.metadata = metadata
        self.entity_type = None
        self.path = None
        self.tag = None

    def __str__(self):
        return f"Ref:\t\t\t{self.reference}\n" \
               f"Title:\t\t\t{self.title}\n" \
               f"Description:\t{self.description}\n" \
               f"Security Tag:\t{self.security_tag}\n" \
               f"Parent:\t\t\t{self.parent}\n\n"

    def __repr__(self):
        return self.__str__()


class Folder(Entity):
    """
       Class to represent the Structural Object or Folder in the Preservica data model
    """

    def __init__(self, reference, title, description, security_tag, parent, metadata):
        super().__init__(reference, title, description, security_tag, parent, metadata)
        self.entity_type = EntityType.FOLDER
        self.path = SO_PATH
        self.tag = "StructuralObject"


class Asset(Entity):
    """
        Class to represent the Information Object or Asset in the Preservica data model
    """

    def __init__(self, reference, title, description, security_tag, parent, metadata):
        super().__init__(reference, title, description, security_tag, parent, metadata)
        self.entity_type = EntityType.ASSET
        self.path = IO_PATH
        self.tag = "InformationObject"


class ContentObject(Entity):
    """
       Class to represent the Content Object in the Preservica data model
    """

    def __init__(self, reference, title, description, security_tag, parent, metadata):
        super().__init__(reference, title, description, security_tag, parent, metadata)
        self.entity_type = EntityType.CONTENT_OBJECT
        self.representation_type = None
        self.asset = None
        self.path = CO_PATH
        self.tag = "ContentObject"


def content_api_identifier_to_type(ref):
    ref = ref.replace('sdb:', '')
    parts = ref.split("|")
    return tuple((EntityType(parts[0]), parts[1]))


def entity_from_string(xml_data):
    entity_response = xml.etree.ElementTree.fromstring(xml_data)
    reference = entity_response.find('.//{*}Ref')
    title = entity_response.find('.//{*}Title')
    security_tag = entity_response.find('.//{*}SecurityTag')
    description = entity_response.find('.//{*}Description')
    parent = entity_response.find('.//{*}Parent')
    if hasattr(parent, 'text'):
        parent = parent.text
    else:
        parent = None

    fragments = entity_response.findall('.//{*}Metadata/{*}Fragment')
    metadata = {}
    for fragment in fragments:
        metadata[fragment.text] = fragment.attrib['schema']

    return {'reference': reference.text, 'title': title.text if hasattr(title, 'text') else None,
            'description': description.text if hasattr(description, 'text') else None,
            'security_tag': security_tag.text, 'parent': parent, 'metadata': metadata}


class Thumbnail(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class EntityType(Enum):
    ASSET = "IO"
    FOLDER = "SO"
    CONTENT_OBJECT = "CO"


class AuthenticatedAPI:
    """
    Base class for authenticated calls which need an access token
    """

    def __version_number__(self):
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(f'https://{self.server}/api/entity/versiondetails/version', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_ = str(request.content)
            return xml_[xml_.find("<CurrentVersion>") + len("<CurrentVersion>"):xml_.find("</CurrentVersion>")]
        if request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.__version_number__()
        raise RuntimeError(request.status_code, "version number failed")

    def __str__(self):
        return f"pyPreservica version: {pyPreservica.__version__}  (Preservica 6.2 Compatible) \n" \
               f"Connected to: {self.server} Preservica version: {self.version} as {self.username}\n"

    def __repr__(self):
        return self.__str__()

    def save_config(self):
        config = configparser.ConfigParser()
        config['credentials'] = {'username': self.username, 'password': self.password, 'tenant': self.tenant,
                                 'server': self.server}
        with open('credentials.properties', 'wt') as configfile:
            config.write(configfile)

    def manager_token(self, username, password):
        data = {'username': username, 'password': password, 'tenant': self.tenant}
        response = requests.post(f'https://{self.server}/api/accesstoken/login', data=data)
        if response.status_code == requests.codes.ok:
            return response.json()['token']
        raise RuntimeError(response.status_code, "Could not generate valid manager approval password")

    def __token__(self):

        if self.shared_secret is False:
            data = {'username': self.username, 'password': self.password, 'tenant': self.tenant}
            response = requests.post(f'https://{self.server}/api/accesstoken/login', data=data)
            if response.status_code == requests.codes.ok:
                return response.json()['token']

        if self.shared_secret is True:
            endpoint = "api/accesstoken/acquire-external"
            timestamp = int(time.time())
            to_hash = f"preservica-external-auth{timestamp}{self.username}{self.password}"
            sha1 = hashlib.sha1()
            sha1.update(to_hash.encode(encoding='UTF-8'))
            data = {"username": self.username, "tenant": self.tenant, "timestamp": timestamp, "hash": sha1.hexdigest()}
            response = requests.post(f'https://{self.server}/{endpoint}', data=data)
            if response.status_code == requests.codes.ok:
                return response.json()['token']

        raise RuntimeError(response.status_code, "Failed to create an authentication token. Check your credentials "
                                                 "are correct")

    def __init__(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False):
        config = configparser.ConfigParser()
        config.read('credentials.properties')

        self.shared_secret = bool(use_shared_secret)

        if not username:
            username = os.environ.get('PRESERVICA_USERNAME')
            if username is None:
                try:
                    username = config['credentials']['username']
                except KeyError:
                    pass
        if not username:
            print("No valid username found in method arguments, environment variables or credentials.properties file")
            raise SystemExit
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
            print("No valid password found in method arguments, environment variables or credentials.properties file")
            raise SystemExit
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
            print("No valid tenant found in method arguments, environment variables or credentials.properties file")
            raise SystemExit
        else:
            self.tenant = tenant

        if not server:
            server = os.environ.get('PRESERVICA_SERVER')
            if server is None:
                try:
                    server = config['credentials']['server']
                except KeyError:
                    pass
        if not server:
            print("No valid server found in method arguments, environment variables or credentials.properties file")
            raise SystemExit
        else:
            self.server = server

        self.token = self.__token__()
        self.version = self.__version_number__()
