import configparser
import os
import xml.etree.ElementTree
from enum import Enum
import requests

CHUNK_SIZE = 1024 * 2

NS_XIPV6 = "http://preservica.com/XIP/v6.0"
NS_ENTITY = "http://preservica.com/EntityAPI/v6.0"
namespace = {'xip': NS_XIPV6, 'v6': NS_ENTITY}
HEADER_TOKEN = "Preservica-Access-Token"

IO_PATH = "information-objects"
SO_PATH = "structural-objects"
CO_PATH = "content-objects"


def only_assets(e):
    return True if e.entity_type is EntityType.ASSET else False


def only_folders(e):
    return True if e.entity_type is EntityType.FOLDER else False


class PagedSet:
    def __init__(self, results, has_more, total, next_page):
        self.results = results
        self.has_more = bool(has_more)
        self.total = int(total)
        self.next_page = next_page

    def __str__(self):
        return self.results.__str__()


class Representation:
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
        self.__str__()


class Bitstream:
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
    def __init__(self, reference, title, description, security_tag, parent, metadata):
        super().__init__(reference, title, description, security_tag, parent, metadata)
        self.entity_type = EntityType.FOLDER
        self.path = SO_PATH
        self.tag = "StructuralObject"


class Asset(Entity):
    def __init__(self, reference, title, description, security_tag, parent, metadata):
        super().__init__(reference, title, description, security_tag, parent, metadata)
        self.entity_type = EntityType.ASSET
        self.path = IO_PATH
        self.tag = "InformationObject"


class ContentObject(Entity):
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
    reference = entity_response.find('.//xip:Ref', namespaces=namespace)
    title = entity_response.find('.//xip:Title', namespaces=namespace)
    security_tag = entity_response.find('.//xip:SecurityTag', namespaces=namespace)
    description = entity_response.find('.//xip:Description', namespaces=namespace)
    parent = entity_response.find('.//xip:Parent', namespaces=namespace)
    if hasattr(parent, 'text'):
        parent = parent.text
    else:
        parent = None

    fragments = entity_response.findall('.//v6:Metadata/v6:Fragment', namespaces=namespace)
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


class AuthenticatedAPI(object):

    def save_config(self):
        config = configparser.ConfigParser()
        config['credentials'] = {'username': self.username, 'password': self.password, 'tenant': self.tenant, 'server': self.server}
        with open('credentials.properties', 'wt') as configfile:
            config.write(configfile)

    def __token__(self):
        data = {'username': self.username, 'password': self.password, 'tenant': self.tenant}
        response = requests.post(f'https://{self.server}/api/accesstoken/login', data=data)
        if response.status_code == requests.codes.ok:
            return response.json()['token']
        else:
            print(f"new_token failed with error code: {response.status_code}")
            print(response.request.url)
            raise SystemExit

    def __init__(self, username="", password="", tenant="", server=""):
        config = configparser.ConfigParser()
        config.read('credentials.properties')

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
