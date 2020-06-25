import os
import uuid
from time import sleep
import requests
import xml.etree.ElementTree
from io import IOBase
from pyPreservica.common import AuthenticatedAPI, Thumbnail, CHUNK_SIZE, EntityType, entityfromstring


class EntityAPI(AuthenticatedAPI):
    """
        A client library for the Preservica Repository web services Entity API
        https://us.preservica.com/api/entity/documentation.html


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

    class Representation:
        def __init__(self, asset, rep_type, name, url):
            self.asset = asset
            self.rep_type = rep_type
            self.name = name
            self.url = url

        def __str__(self):
            return f"Type:\t\t\t{self.rep_type}\nName:\t\t\t{self.name}\nURL:\t{self.url}"

        def __repr__(self):
            return f"Type:\t\t\t{self.rep_type}\nName:\t\t\t{self.name}\nURL:\t{self.url}"

    class Bitstream:
        def __init__(self, filename, length, fixity, content_url):
            self.filename = filename
            self.length = length
            self.fixity = fixity
            self.content_url = content_url

        def __str__(self):
            return f"Filename:\t\t\t{self.filename}\nFileSize:\t\t\t{self.length}\nContent:\t{self.content_url}\nFixity:\t{self.fixity}"

        def __repr__(self):
            return f"Filename:\t\t\t{self.filename}\nFileSize:\t\t\t{self.length}\nContent:\t{self.content_url}\nFixity:\t{self.fixity}"

    class Generation:
        def __init__(self, original, active, format_group, effective_date, bitstreams):
            self.original = original
            self.active = active
            self.content_object = None
            self.format_group = format_group
            self.effective_date = effective_date
            self.bitstreams = bitstreams

        def __str__(self):
            return f"Active:\t\t\t{self.active}\nOriginal:\t\t\t{self.original}\nFormat_group:\t{self.format_group}"

        def __repr__(self):
            return f"Active:\t\t\t{self.active}\nOriginal:\t\t\t{self.original}\nFormat_group:\t{self.format_group}"

    class Entity:
        def __init__(self, reference, title, description, security_tag, parent, metadata):
            self.reference = reference
            self.title = title
            self.description = description
            self.security_tag = security_tag
            self.parent = parent
            self.metadata = metadata
            self.entity_type = None

        def __str__(self):
            return f"Ref:\t\t\t{self.reference}\nTitle:\t\t\t{self.title}\nDescription:\t{self.description}" \
                   f"\nSecurity Tag:\t{self.security_tag}\nParent:\t\t\t{self.parent}\n\n"

        def __repr__(self):
            return f"Ref:\t\t\t{self.reference}\nTitle:\t\t\t{self.title}\nDescription:\t{self.description}" \
                   f"\nSecurity Tag:\t{self.security_tag}\nParent:\t\t\t{self.parent}\n\n"

    class Folder(Entity):
        def __init__(self, reference, title, description, security_tag, parent, metadata):
            super().__init__(reference, title, description, security_tag, parent, metadata)
            self.entity_type = EntityType.FOLDER

    class Asset(Entity):
        def __init__(self, reference, title, description, security_tag, parent, metadata):
            super().__init__(reference, title, description, security_tag, parent, metadata)
            self.entity_type = EntityType.ASSET

    class ContentObject(Entity):
        def __init__(self, reference, title, description, security_tag, parent, metadata):
            super().__init__(reference, title, description, security_tag, parent, metadata)
            self.entity_type = EntityType.CONTENT_OBJECT
            self.representation_type = None
            self.asset = None

    class PagedSet:
        def __init__(self, results, has_more, total, next_page):
            self.results = results
            self.has_more = has_more
            self.total = total
            self.next_page = next_page

        def __str__(self):
            return self.results.__str__()

    def bitstream_content(self, bitstream, filename):
        headers = {'Preservica-Access-Token': self.token}
        if not isinstance(bitstream, self.Bitstream):
            return None
        with requests.get(bitstream.content_url, headers=headers, stream=True) as req:
            if req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.bitstream_content(bitstream, filename)
            elif req.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        file.flush()
                file.close()
                if os.path.getsize(filename) == bitstream.length:
                    return bitstream.length
                else:
                    return None
            else:
                print(f"bitstream_content failed with error code: {req.status_code}")
                print(req.request.url)
                raise SystemExit

    def download(self, entity, filename):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/octet-stream'}
        if isinstance(entity, self.Asset):
            params = {'id': f'sdb:IO|{entity.reference}'}
        elif isinstance(entity, self.Folder):
            params = {'id': f'sdb:SO|{entity.reference}'}
        else:
            print(f"entity must be a folder or asset")
            raise SystemExit
        with requests.get(f'https://{self.server}/api/content/download', params=params, headers=headers, stream=True) as req:
            if req.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        file.flush()
                file.close()
                return filename
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.download(entity, filename)
            else:
                print(f"download failed with error code: {req.status_code}")
                print(req.request.url)
                raise SystemExit

    def thumbnail(self, entity, filename, size=Thumbnail.LARGE):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/octet-stream'}
        if isinstance(entity, self.Asset):
            params = {'id': f'sdb:IO|{entity.reference}', 'size': f'{size.value}'}
        elif isinstance(entity, self.Folder):
            params = {'id': f'sdb:SO|{entity.reference}', 'size': f'{size.value}'}
        else:
            print(f"entity must be a folder or asset")
            raise SystemExit
        with requests.get(f'https://{self.server}/api/content/thumbnail', params=params, headers=headers) as req:
            if req.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                        file.flush()
                file.close()
                return filename
            elif req.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.thumbnail(entity, filename, size=size)
            else:
                print(f"thumbnail failed with error code: {req.status_code}")
                print(req.request.url)
                raise SystemExit

    def delete_identifiers(self, entity, identifier_type=None, identifier_value=None):
        headers = {'Preservica-Access-Token': self.token}
        if isinstance(entity, self.Asset):
            path = "information-objects"
        elif isinstance(entity, self.Folder):
            path = "structural-objects"
        request = requests.get(f'https://{self.server}/api/entity/{path}/{entity.reference}/identifiers', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            identifier_list = entity_response.findall('.//{http://preservica.com/XIP/v6.0}Identifier')
            for identifier_element in identifier_list:
                _ref = _type = _value = _aipid = None
                for identifier in identifier_element:
                    if identifier.tag == "{http://preservica.com/XIP/v6.0}Entity":
                        _ref = identifier.text
                    if identifier.tag == "{http://preservica.com/XIP/v6.0}Type" and identifier_type is not None:
                        _type = identifier.text
                    if identifier.tag == "{http://preservica.com/XIP/v6.0}Value" and identifier_value is not None:
                        _value = identifier.text
                    if identifier.tag == "{http://preservica.com/XIP/v6.0}ApiId":
                        _aipid = identifier.text
                if _ref == entity.reference and _type == identifier_type and _value == identifier_value:
                    del_req = requests.delete(
                        f'https://{self.server}/api/entity/{path}/{entity.reference}/identifiers/{_aipid}', headers=headers)
                    if del_req.status_code == requests.codes.unauthorized:
                        self.token = self.__token__()
                        return self.delete_identifier(entity, identifier_type, identifier_value)
                    if del_req.status_code == requests.codes.no_content:
                        pass
                    else:
                        return None
            return entity
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.delete_identifier(entity, identifier_type, identifier_value)
        else:
            print(f"delete_identifier failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def identifier(self, identifier_type, identifier_value):
        headers = {'Preservica-Access-Token': self.token}
        payload = {'type': identifier_type, 'value': identifier_value}
        request = requests.get(f'https://{self.server}/api/entity/entities/by-identifier', params=payload, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            entity_list = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Entity')
            result = set()
            for entity in entity_list:
                if entity.attrib['type'] == EntityType.FOLDER.value:
                    f = self.Folder(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(f)
                elif entity.attrib['type'] == EntityType.ASSET.value:
                    a = self.Asset(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(a)
                elif entity.attrib['type'] == EntityType.CONTENT_OBJECT.value:
                    c = self.ContentObject(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(c)
            return result
        elif request.status_code == requests.codes.unauthorized:
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
        elif isinstance(entity, self.Folder):
            end_point = f"/structural-objects/{entity.reference}/identifiers"
        elif isinstance(entity, self.ContentObject):
            end_point = f"/content-objects/{entity.reference}/identifiers"
        else:
            print("Unknown entity type")
            raise SystemExit
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='UTF-8', xml_declaration=True)
        request = requests.post(f'https://{self.server}/api/entity{end_point}', data=xml_request, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_string = str(request.content.decode("UTF-8"))
            identifier_response = xml.etree.ElementTree.fromstring(xml_string)
            aip_id = identifier_response.find('.//{http://preservica.com/XIP/v6.0}ApiId')
            if hasattr(aip_id, 'text'):
                return aip_id.text
            else:
                return None
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_identifier(entity, identifier_type, identifier_value)
        else:
            print(f"add_identifier failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def update_metadata(self, entity, schema, data):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        for url in entity.metadata:
            if schema == entity.metadata[url]:
                mref = url[url.rfind(f"{entity.reference}/metadata/") + len(f"{entity.reference}/metadata/"):]
                xml_object = xml.etree.ElementTree.Element('MetadataContainer', {"schemaUri": schema,
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
                if request.status_code == requests.codes.ok:
                    return self.entity(entity.entity_type, entity.reference)
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.update_metadata(entity, schema, data)
                else:
                    print(f"update_metadata failed with error code: {request.status_code}")
                    print(request.request.url)
                    raise SystemExit

    def add_metadata(self, entity, schema, data):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        xml_object = xml.etree.ElementTree.Element('MetadataContainer',
                                                   {"schemaUri": schema, "xmlns": "http://preservica.com/XIP/v6.0"})
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
        elif isinstance(entity, self.Folder):
            end_point = f"/structural-objects/{entity.reference}/metadata"
        elif isinstance(entity, self.ContentObject):
            end_point = f"/content-objects/{entity.reference}/metadata"
        else:
            print("Unknown entity type")
            raise SystemExit
        request = requests.post(f'https://{self.server}/api/entity{end_point}', data=xml_request, headers=headers)
        if request.status_code == requests.codes.ok:
            if isinstance(entity, self.Asset):
                return self.asset(entity.reference)
            elif isinstance(entity, self.Folder):
                return self.folder(entity.reference)
            elif isinstance(entity, self.ContentObject):
                return self.content_object(entity.reference)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_metadata(entity, schema, data)
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
        elif isinstance(entity, self.ContentObject):
            end_point = "/content-objects"
            xml_object = xml.etree.ElementTree.Element('ContentObject', {"xmlns": "http://preservica.com/XIP/v6.0"})
        else:
            print("Unknown entity type")
            raise SystemExit
        xml.etree.ElementTree.SubElement(xml_object, "Ref").text = entity.reference
        xml.etree.ElementTree.SubElement(xml_object, "Title").text = entity.title
        xml.etree.ElementTree.SubElement(xml_object, "Description").text = entity.description
        xml.etree.ElementTree.SubElement(xml_object, "SecurityTag").text = entity.security_tag
        if entity.parent is not None:
            xml.etree.ElementTree.SubElement(xml_object, "Parent").text = entity.parent

        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        request = requests.put(f'https://{self.server}/api/entity{end_point}/{entity.reference}', data=xml_request,
                               headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            response = entityfromstring(xml_response)
            if isinstance(entity, self.Asset):
                return self.Asset(response['reference'], response['title'], response['description'],
                                  response['security_tag'],
                                  response['parent'], response['metadata'])
            elif isinstance(entity, self.Folder):
                return self.Folder(response['reference'], response['title'], response['description'],
                                   response['security_tag'],
                                   response['parent'], response['metadata'])
            elif isinstance(entity, self.ContentObject):
                return self.ContentObject(response['reference'], response['title'], response['description'],
                                          response['security_tag'],
                                          response['parent'], response['metadata'])
        elif request.status_code == requests.codes.unauthorized:
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
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity = entityfromstring(xml_response)
            f = self.Folder(entity['reference'], entity['title'], entity['description'], entity['security_tag'],
                            entity['parent'],
                            entity['metadata'])
            return f
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.create_folder(title, description, security_tag, parent=parent)
        else:
            print(f"create_folder failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def metadata_for_entity(self, entity, schema):
        for u, s in entity.metadata.items():
            if schema == s:
                return self.metadata(u)
        return None

    def security_tag_sync(self, entity, new_tag):
        self.token = self.__token__()
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'text/plain'}
        if isinstance(entity, self.Asset):
            end_point = f"/information-objects/{entity.reference}/security-descriptor"
        elif isinstance(entity, self.Folder):
            end_point = f"/structural-objects/{entity.reference}/security-descriptor"
        else:
            print("Unknown entity type")
            raise SystemExit
        request = requests.put(f'https://{self.server}/api/entity{end_point}?includeDescendants=true', data=new_tag, headers=headers)
        if request.status_code == requests.codes.accepted:
            sleep_sec = 2
            while True:
                req = requests.get(f"https://{self.server}/api/entity/progress/{request.content.decode()}", headers=headers)
                if req.status_code == requests.codes.ok:
                    entity_response = xml.etree.ElementTree.fromstring(req.content.decode("utf-8"))
                    status = entity_response.find(".//{http://status.preservica.com}Status")
                    if hasattr(status, 'text'):
                        if status.text != "ACTIVE":
                            return self.entity(entity.entity_type, entity.reference)
                sleep(sleep_sec)
                sleep_sec = sleep_sec + 2
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.security_tag(entity, new_tag)
        else:
            print(f"security_tag failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def security_tag_async(self, entity, new_tag):
        headers = {'Preservica-Access-Token': self.token, 'Content-Type': 'text/plain'}
        if isinstance(entity, self.Asset):
            end_point = f"/information-objects/{entity.reference}/security-descriptor"
        elif isinstance(entity, self.Folder):
            end_point = f"/structural-objects/{entity.reference}/security-descriptor"
        else:
            print("Unknown entity type")
            raise SystemExit

        data = new_tag
        request = requests.put(f'https://{self.server}/api/entity{end_point}?includeDescendants=true', data=data, headers=headers)
        if request.status_code == requests.codes.accepted:
            return request.content.decode()
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.security_tag(entity, new_tag)
        else:
            print(f"security_tag failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def metadata(self, uri):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(uri, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            content = entity_response.find('.//{http://preservica.com/XIP/v6.0}Content')
            return xml.etree.ElementTree.tostring(content[0], encoding='utf8', method='xml').decode('UTF-8')
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.metadata(uri)
        else:
            print(f"metadata failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def entity(self, entity_type, reference):
        if entity_type is EntityType.CONTENT_OBJECT:
            return self.content_object(reference)
        elif entity_type is EntityType.FOLDER:
            return self.folder(reference)
        elif entity_type is EntityType.ASSET:
            return self.asset(reference)
        else:
            return None

    def asset(self, reference):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(f'https://{self.server}/api/entity/information-objects/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity = entityfromstring(xml_response)
            a = self.Asset(entity['reference'], entity['title'], entity['description'], entity['security_tag'], entity['parent'],
                           entity['metadata'])
            return a
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.asset(reference)
        elif request.status_code == requests.codes.not_found:
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        else:
            print(f"asset failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def folder(self, reference):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(f'https://{self.server}/api/entity/structural-objects/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity = entityfromstring(xml_response)
            f = self.Folder(entity['reference'], entity['title'], entity['description'], entity['security_tag'],
                            entity['parent'],
                            entity['metadata'])
            return f
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.folder(reference)
        elif request.status_code == requests.codes.not_found:
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        else:
            print(f"folder failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def content_object(self, reference):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(f'https://{self.server}/api/entity/content-objects/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity = entityfromstring(xml_response)
            c = self.ContentObject(entity['reference'], entity['title'], entity['description'], entity['security_tag'],
                                   entity['parent'], entity['metadata'])
            return c
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.content_objects(reference)
        elif request.status_code == requests.codes.not_found:
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        else:
            print(f"content_object failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def content_objects(self, representation):
        headers = {'Preservica-Access-Token': self.token}
        if not isinstance(representation, self.Representation):
            return None
        request = requests.get(f'{representation.url}', headers=headers)
        if request.status_code == requests.codes.ok:
            results = list()
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            content_objects = entity_response.findall('.//{http://preservica.com/XIP/v6.0}ContentObject')
            for co in content_objects:
                content_object = self.content_object(co.text)
                content_object.representation_type = representation.rep_type
                content_object.asset = representation.asset
                results.append(content_object)
            return results
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.content_objects(representation)
        else:
            print(f"content_objects failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def generation(self, url):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(url, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            ge = entity_response.find('.//{http://preservica.com/XIP/v6.0}Generation')
            format_group = entity_response.find('.//{http://preservica.com/XIP/v6.0}FormatGroup')
            effective_date = entity_response.find('.//{http://preservica.com/XIP/v6.0}EffectiveDate')
            bitstreams = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Bitstream')
            bitstream_list = list()
            for bit in bitstreams:
                bitstream_list.append(self.bitstream(bit.text))
            generation = self.Generation(bool(ge.attrib['original']), bool(ge.attrib['active']), format_group.text, effective_date.text,
                                         bitstream_list)
            return generation
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.generation(url)
        else:
            print(f"generation failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def bitstream(self, url):
        headers = {'Preservica-Access-Token': self.token}
        request = requests.get(url, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            filename = entity_response.find('.//{http://preservica.com/XIP/v6.0}Filename')
            filesize = entity_response.find('.//{http://preservica.com/XIP/v6.0}FileSize')
            fixity_values = entity_response.findall('.//{http://preservica.com/XIP/v6.0}Fixity')
            content = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}Content')
            fixity = dict()
            for f in fixity_values:
                fixity[f[0].text] = f[1].text
            bitstream = self.Bitstream(filename.text, filesize.text, fixity, content.text)
            return bitstream
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.bitstream(url)
        else:
            print(f"bitstream failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def generations(self, content_object):
        headers = {'Preservica-Access-Token': self.token}
        if not isinstance(content_object, self.ContentObject):
            return None
        request = requests.get(f'https://{self.server}/api/entity/content-objects/{content_object.reference}/generations', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            generations = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Generation')
            result = list()
            for g in generations:
                generation = self.generation(g.text)
                generation.content_object = content_object
                result.append(generation)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.generations(content_object)
        else:
            print(f"generations failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def representations(self, asset):
        headers = {'Preservica-Access-Token': self.token}
        if not isinstance(asset, self.Asset):
            return None
        request = requests.get(f'https://{self.server}/api/entity/information-objects/{asset.reference}/representations', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            representations = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Representation')
            result = set()
            for r in representations:
                representation = self.Representation(asset, r.attrib['type'], r.attrib['name'], r.text)
                result.add(representation)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.representations(asset)
        else:
            print(f"representations failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit

    def children(self, folder_reference, maximum=100, next_page=None):
        headers = {'Preservica-Access-Token': self.token}
        if next_page is None:
            if folder_reference is None:
                request = requests.get(f'https://{self.server}/api/entity/root/children?start={0}&max={maximum}', headers=headers)
            else:
                request = requests.get(
                    f'https://{self.server}/api/entity/structural-objects/{folder_reference}/children?start={0}&max={maximum}',
                    headers=headers)
        else:
            request = requests.get(next_page, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            children = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Child')
            result = set()
            next_url = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}Next')
            total_hits = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}TotalResults')
            for c in children:
                if c.attrib['type'] == EntityType.FOLDER.value:
                    f = self.Folder(c.attrib['ref'], c.attrib['title'], None, None, folder_reference, None)
                    result.add(f)
                else:
                    a = self.Asset(c.attrib['ref'], c.attrib['title'], None, None, folder_reference, None)
                    result.add(a)
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            ps = self.PagedSet(result, has_more, total_hits.text, url)
            return ps
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.children(folder_reference, maximum=maximum, next_page=next_page)
        else:
            print(f"children failed with error code: {request.status_code}")
            print(request.request.url)
            raise SystemExit
