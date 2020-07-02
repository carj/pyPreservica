import configparser
import os
import xml
from enum import Enum
import requests

CHUNK_SIZE = 1024 * 2

NS_XIPV6 = "http://preservica.com/XIP/v6.0"
NS_ENTITY = "http://preservica.com/EntityAPI/v6.0"
namespace = {'xip': NS_XIPV6, 'v6': NS_ENTITY}
HEADER_TOKEN = "Preservica-Access-Token"


def entityfromstring(xml_data):
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


class AuthenticatedAPI:

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
