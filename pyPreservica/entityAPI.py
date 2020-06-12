import uuid
from enum import Enum

import requests
import xml.etree.ElementTree
from io import IOBase


def _entity_(xml_data):
    entity_response = xml.etree.ElementTree.fromstring(xml_data)
    reference = entity_response.find('.//{http://preservica.com/XIP/v6.0}Ref')
    title = entity_response.find('.//{http://preservica.com/XIP/v6.0}Title')
    security_tag = entity_response.find('.//{http://preservica.com/XIP/v6.0}SecurityTag')
    description = entity_response.find('.//{http://preservica.com/XIP/v6.0}Description')
    parent = entity_response.find('.//{http://preservica.com/XIP/v6.0}Parent')
    if hasattr(parent, 'text'):
        parent = parent.text
    else:
        parent = None

    fragments = entity_response.findall(
        './/{http://preservica.com/EntityAPI/v6.0}Metadata/{http://preservica.com/EntityAPI/v6.0}Fragment')
    metadata = {}
    for fragment in fragments:
        metadata[fragment.text] = fragment.attrib['schema']

    return {'reference': reference.text, 'title': title.text if hasattr(title, 'text') else "",
            'description': description.text if hasattr(description, 'text') else "",
            'security_tag': security_tag.text, 'parent': parent, 'metadata': metadata}


class Thumbnail(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class EntityAPI:
    """
        A client library for the Preservica Repository web services Entity API
        https://us.preservica.com/api/entity/documentation.html


        Attributes
        ----------
        username : str
            Preservica account username, usually an email address
        password : str
            Preservica account password
        tenant : str
            Tenant name for the Preservica account
        server : str
            The URL of the Preservica instance

        Methods
        -------
        asset(reference):
            Fetches the main XIP attributes for an asset by its reference

        folder(reference):
            Fetches the main XIP attributes for a folder by its reference

        metadata(uri):
            Return the descriptive metadata attached to an entity.

        save(entity):
            Updates the title and description of an asset or folder

        create_folder(title, description, security_tag, parent=None):
            creates a new structural object in the repository

        children(reference, maximum=100, next_page=None):
            returns a list of children from the folder

        identifier(identifier_type, identifier_value):
            returns an asset or folder based on external identifiers

        add_identifier(entity, identifier_type, identifier_value):
            adds a new external identifier to an entity

        add_metadata(entity, namespace, data):
            Add new descriptive metadata to an entity

        update_metadata(entity, namespace, data):
            Update the descriptive metadata attached to an entity



        """

    def __init__(self, username, password, tenant, server):
        self.username = username
        self.password = password
        self.tenant = tenant
        self.server = server
        self.token = self.__token__()

    def __token__(self):
        response = requests.post(
            f'https://{self.server}/api/accesstoken/login?username={self.username}&password={self.password}&tenant={self.tenant}')
        if response.status_code == 200:
            return response.json()['token']
        else:
            print(f"new_token failed with error code: {response.status_code}")
            print(response.request.url)
            raise SystemExit

    class Entity:
        def __init__(self, reference, title, description, security_tag, parent, metadata):
            self.reference = reference
            self.title = title
            self.description = description
            self.security_tag = security_tag
            self.parent = parent
            self.metadata = metadata
            self.type = None

        def __str__(self):
            return f"Ref:\t\t\t{self.reference}\nTitle:\t\t\t{self.title}\nDescription:\t{self.description}" \
                   f"\nSecurity Tag:\t{self.security_tag}\nParent:\t\t\t{self.parent}\n\n"

        def __repr__(self):
            return f"Ref:\t\t\t{self.reference}\nTitle:\t\t\t{self.title}\nDescription:\t{self.description}" \
                   f"\nSecurity Tag:\t{self.security_tag}\nParent:\t\t\t{self.parent}\n\n"

    class Folder(Entity):
        def __init__(self, reference, title, description, security_tag, parent, metadata):
            super().__init__(reference, title, description, security_tag, parent, metadata)
            self.type = "SO"

    class Asset(Entity):
        def __init__(self, reference, title, description, security_tag, parent, metadata):
            super().__init__(reference, title, description, security_tag, parent, metadata)
            self.type = "IO"

    class PagedSet:
        def __init__(self, results, has_more, total, next_page):
            self.results = results
            self.has_more = has_more
            self.total = total
            self.next_page = next_page

        def __str__(self):
            return self.results.__str__()

    def download(self, entity):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/octet-stream'}
        if isinstance(entity, self.Asset):
            params = {'id': f'sdb:IO|{entity.reference}'}
        elif isinstance(entity, self.Folder):
            params = {'id': f'sdb:SO|{entity.reference}'}
        request = requests.get(f'https://{self.server}/api/content/download', params=params, headers=headers)
        if request.status_code == 200:
            return request.content
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.download(entity)
        else:
            print(f"download failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def thumbnail(self, entity, size=Thumbnail.LARGE):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/octet-stream'}
        if isinstance(entity, self.Asset):
            params = {'id': f'sdb:IO|{entity.reference}', 'size': f'{size.value}'}
        elif isinstance(entity, self.Folder):
            params = {'id': f'sdb:SO|{entity.reference}', 'size': f'{size.value}'}
        request = requests.get(f'https://{self.server}/api/content/thumbnail', params=params, headers=headers)
        if request.status_code == 200:
            return request.content
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.download(entity)
        else:
            print(f"download failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def identifier(self, identifier_type, identifier_value):
        headers = {'Preservica-Access-Token': self.token}
        payload = {'type': identifier_type, 'value': identifier_value}
        request = requests.get(f'https://{self.server}/api/entity/entities/by-identifier', params=payload,
                               headers=headers)
        if request.status_code == 200:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            entity_list = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Entity')
            result = set()
            for entity in entity_list:
                if entity.attrib['type'] == 'SO':
                    f = self.Folder(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(f)
                else:
                    a = self.Asset(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(a)
            return result
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.identifier(identifier_type, identifier_value)
        else:
            print(f"identifier failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def add_identifier(self, entity, identifier_type, identifier_value):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        xml_object = xml.etree.ElementTree.Element('Identifier', {"xmlns": "http://preservica.com/XIP/v6.0"})
        xml.etree.ElementTree.SubElement(xml_object, "Type").text = identifier_type
        xml.etree.ElementTree.SubElement(xml_object, "Value").text = identifier_value
        xml.etree.ElementTree.SubElement(xml_object, "Entity").text = entity.reference
        if isinstance(entity, self.Asset):
            end_point = f"/information-objects/{entity.reference}/identifiers"
        else:
            end_point = f"/structural-objects/{entity.reference}/identifiers"
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='UTF-8', xml_declaration=True)
        request = requests.post(f'https://{self.server}/api/entity{end_point}', data=xml_request, headers=headers)
        if request.status_code == 200:
            xml_string = str(request.content.decode("UTF-8"))
            identifier_response = xml.etree.ElementTree.fromstring(xml_string)
            aip_id = identifier_response.find('.//{http://preservica.com/XIP/v6.0}ApiId')
            if hasattr(aip_id, 'text'):
                return aip_id.text
            else:
                return None
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.add_identifier(entity, identifier_type, identifier_value)
        else:
            print(f"add_identifier failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def update_metadata(self, entity, namespace, data):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        for url in entity.metadata:
            if namespace == entity.metadata[url]:
                mref = url[url.rfind(f"{entity.reference}/metadata/") + len(f"{entity.reference}/metadata/"):]
                xml_object = xml.etree.ElementTree.Element('MetadataContainer', {"schemaUri": namespace,
                                                                                 "xmlns": "http://preservica.com/XIP/v6.0"})
                xml.etree.ElementTree.SubElement(xml_object, "Ref").text = mref
                xml.etree.ElementTree.SubElement(xml_object, "Entity").text = entity.reference
                content = xml.etree.ElementTree.SubElement(xml_object, "Content")
                if isinstance(data, str):
                    ob = xml.etree.ElementTree.fromstring(data)
                    content.append(ob)
                if isinstance(data, IOBase):
                    tree = xml.etree.ElementTree.parse(data)
                    content.append(tree.getroot())
                xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='UTF-8', xml_declaration=True)
                request = requests.put(f'{url}', data=xml_request, headers=headers)
                if request.status_code == 200:
                    if isinstance(entity, self.Asset):
                        return self.asset(entity.reference)
                    else:
                        return self.folder(entity.reference)
                elif request.status_code == 401:
                    self.token = self.__token__()
                    return self.update_metadata(entity, namespace, data)
                else:
                    print(f"update_metadata failed with error code: {request.status_code}")
                    print(request.request.url)
                    raise SystemExit

    def add_metadata(self, entity, namespace, data):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        xml_object = xml.etree.ElementTree.Element('MetadataContainer',
                                                   {"schemaUri": namespace, "xmlns": "http://preservica.com/XIP/v6.0"})
        xml.etree.ElementTree.SubElement(xml_object, "Entity").text = entity.reference
        content = xml.etree.ElementTree.SubElement(xml_object, "Content")
        if isinstance(data, str):
            ob = xml.etree.ElementTree.fromstring(data)
            content.append(ob)
        if isinstance(data, IOBase):
            tree = xml.etree.ElementTree.parse(data)
            content.append(tree.getroot())
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='UTF-8', xml_declaration=True)
        if isinstance(entity, self.Asset):
            end_point = f"/information-objects/{entity.reference}/metadata"
        else:
            end_point = f"/structural-objects/{entity.reference}/metadata"
        request = requests.post(f'https://{self.server}/api/entity{end_point}', data=xml_request, headers=headers)
        if request.status_code == 200:
            if isinstance(entity, self.Asset):
                return self.asset(entity.reference)
            else:
                return self.folder(entity.reference)
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.add_metadata(entity, namespace, data)
        else:
            print(f"add_metadata failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def save(self, entity):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        if isinstance(entity, self.Asset):
            end_point = "/information-objects"
            xml_object = xml.etree.ElementTree.Element('InformationObject', {"xmlns": "http://preservica.com/XIP/v6.0"})
        elif isinstance(entity, self.Folder):
            end_point = "/structural-objects"
            xml_object = xml.etree.ElementTree.Element('StructuralObject', {"xmlns": "http://preservica.com/XIP/v6.0"})
        else:
            return

        xml.etree.ElementTree.SubElement(xml_object, "Ref").text = entity.reference
        xml.etree.ElementTree.SubElement(xml_object, "Title").text = entity.title
        xml.etree.ElementTree.SubElement(xml_object, "Description").text = entity.description
        xml.etree.ElementTree.SubElement(xml_object, "SecurityTag").text = entity.security_tag
        if entity.parent is not None:
            xml.etree.ElementTree.SubElement(xml_object, "Parent").text = entity.parent

        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        request = requests.put(f'https://{self.server}/api/entity{end_point}/{entity.reference}', data=xml_request,
                               headers=headers)
        if request.status_code == 200:
            xml_response = str(request.content.decode('UTF-8'))
            response = _entity_(xml_response)
            if isinstance(entity, self.Asset):
                return self.Asset(response['reference'], response['title'], response['description'],
                                  response['security_tag'],
                                  response['parent'], response['metadata'])
            else:
                return self.Folder(response['reference'], response['title'], response['description'],
                                   response['security_tag'],
                                   response['parent'], response['metadata'])
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.save(entity)
        else:
            print(f"save failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def create_folder(self, title, description, security_tag, parent=None):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        structuralobject = xml.etree.ElementTree.Element('StructuralObject',
                                                         {"xmlns": "http://preservica.com/XIP/v6.0"})
        xml.etree.ElementTree.SubElement(structuralobject, "Ref").text = str(uuid.uuid4())
        xml.etree.ElementTree.SubElement(structuralobject, "Title").text = title
        xml.etree.ElementTree.SubElement(structuralobject, "Description").text = description
        xml.etree.ElementTree.SubElement(structuralobject, "SecurityTag").text = security_tag
        if parent is not None:
            xml.etree.ElementTree.SubElement(structuralobject, "Parent").text = parent

        xml_request = xml.etree.ElementTree.tostring(structuralobject, encoding='utf-8')
        request = requests.post(f'https://{self.server}/api/entity/structural-objects', data=xml_request,
                                headers=headers)
        if request.status_code == 200:
            xml_response = str(request.content.decode('UTF-8'))
            entity = _entity_(xml_response)
            f = self.Folder(entity['reference'], entity['title'], entity['description'], entity['security_tag'],
                            entity['parent'],
                            entity['metadata'])
            return f
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.create_folder(title, description, security_tag, parent=parent)
        else:
            print(f"create_folder failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def metadata(self, uri):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(uri, headers=headers)
        if request.status_code == 200:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            content = entity_response.find('.//{http://preservica.com/XIP/v6.0}Content')
            return xml.etree.ElementTree.tostring(content[0], encoding='utf8', method='xml').decode()
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.metadata(uri)
        else:
            print(f"metadata failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def asset(self, reference):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(f'https://{self.server}/api/entity/information-objects/{reference}', headers=headers)
        if request.status_code == 200:
            xml_response = str(request.content.decode('UTF-8'))
            entity = _entity_(xml_response)
            a = self.Asset(entity['reference'], entity['title'], entity['description'], entity['security_tag'],
                           entity['parent'], entity['metadata'])
            return a
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.asset(reference)
        else:
            print(f"asset failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def folder(self, reference):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(f'https://{self.server}/api/entity/structural-objects/{reference}', headers=headers)
        if request.status_code == 200:
            xml_response = str(request.content.decode('UTF-8'))
            entity = _entity_(xml_response)
            f = self.Folder(entity['reference'], entity['title'], entity['description'], entity['security_tag'],
                            entity['parent'],
                            entity['metadata'])
            return f
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.folder(reference)
        else:
            print(f"folder failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def children(self, reference, maximum=100, next_page=None):
        headers = {'Preservica-Access-Token': self.token}
        if next_page is None:
            if reference is None:
                request = requests.get(f'https://{self.server}/api/entity/root/children?start={0}&max={maximum}',
                                       headers=headers)
            else:
                request = requests.get(
                    f'https://{self.server}/api/entity/structural-objects/{reference}/children?start={0}&max={maximum}',
                    headers=headers)
        else:
            request = requests.get(next_page, headers=headers)
        if request.status_code == 200:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            childs = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Child')
            result = set()

            next_url = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}Next')
            total_hits = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}TotalResults')

            for c in childs:
                if c.attrib['type'] == 'SO':
                    f = self.Folder(c.attrib['ref'], c.attrib['title'], None, None, reference, None)
                    result.add(f)
                else:
                    a = self.Asset(c.attrib['ref'], c.attrib['title'], None, None, reference, None)
                    result.add(a)
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            ps = self.PagedSet(result, has_more, total_hits.text, url)
            return ps
        elif request.status_code == 401:
            self.token = self.__token__()
            return self.children(reference, maximum=maximum, next_page=next_page)
        else:
            print(f"children failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit
