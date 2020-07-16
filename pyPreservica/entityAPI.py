import uuid
from datetime import datetime, timedelta, timezone
from time import sleep
import xml.etree.ElementTree
from typing import Optional, Any

from pyPreservica.common import *


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

            content_object(reference):
                Fetches the main XIP attributes for a content_object by its reference

            entity(entity_type, reference):
                Get an entity by its type and reference

            metadata(uri):
                Return the descriptive metadata attached to an entity.

            metadata_for_entity(entity, schema):
                Return the metadata fragment for the entity by schema

            save(entity):
                Updates the title and description of an asset or folder

            create_folder(title, description, security_tag, parent=None):
                creates a new structural object in the repository

            children(reference, maximum=100, next_page=None):
                returns a list of children from the folder

            identifier(identifier_type, identifier_value):
                returns an asset or folder based on external identifiers

            identifiers_for_entity(entity):
                returns a set of identifiers on the entity

            add_identifier(entity, identifier_type, identifier_value):
                adds a new external identifier to an entity

            delete_identifier(entity, identifier_type=None, identifier_value=None):
                deletes identifiers which belong to an entity

            add_metadata(entity, namespace, data):
                Add new descriptive metadata to an entity

            update_metadata(entity, namespace, data):
                Update the descriptive metadata attached to an entity

            delete_metadata(entity, schema):
                Delete all the metadata fragments on an entity with the schema
                Tests - Yes

            download(entity, filename):
                Download the first content object of the access representation to the file given by filename

            thumbnail(entity, filename, size=Thumbnail.LARGE):
                Download the thumbnail image for an entity

            move(entity, dest_folder):
                Move an entity into the folder given by dest_folder

            bitstream_content(bitstream, filename):
                Download a bitstream and save to filename

            security_tag_async(entity, new_tag):
                Non-blocking call to change security tag

            security_tag_sync(self, entity, new_tag):
                Blocking call to change security tag

            representations(asset):
                Return a set of representations for the asset

            content_objects(representation):
                Returns an ordered list of content objects in the representation

            generations(content_object)
                Returns a list of generations for the content object

    """

    def bitstream_content(self, bitstream: Bitstream, filename: str):
        """
        Download a file represented as a Bitstream to a local filename

        Returns the number of bytes written to the file
        Returns None if the file does not contain the correct number of bytes

        :param bitstream: A Bitstream object
        :param filename: The filename to write the bytes to
        """

        if not isinstance(bitstream, Bitstream):
            raise RuntimeError("bitstream argument is not a Bitstream object")
        with requests.get(bitstream.content_url, headers={HEADER_TOKEN: self.token}, stream=True) as req:
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
                    os.remove(filename)
                    return None
            else:
                raise RuntimeError(req.status_code, "bitstream_content failed")

    def download(self, entity: Entity, filename: str):
        """
           Download a file from an asset

           Returns the filename of the new file

           :param entity: The entity containing the file
           :param filename: The filename to write the bytes to
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}
        params = {'id': f'sdb:{entity.entity_type.value}|{entity.reference}'}
        with requests.get(f'https://{self.server}/api/content/download', params=params, headers=headers,
                          stream=True) as req:
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
                raise RuntimeError(req.status_code, "download failed")

    def thumbnail(self, entity: Entity, filename: str, size=Thumbnail.LARGE):
        """
            Download the thumbnail of an asset or folder

            Returns the filename of the new thumbnail file

            :param entity: The entity containing the file
            :param filename: The filename to write the bytes to
            :param size: The size of the thumbnail
         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}
        params = {'id': f'sdb:{entity.entity_type.value}|{entity.reference}', 'size': f'{size.value}'}
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
                raise RuntimeError(req.status_code, "thumbnail failed")

    def delete_identifiers(self, entity: Entity, identifier_type: str = None, identifier_value: str = None):
        """
             Delete external identifiers from an entity

             Returns the entity

             :param entity: The entity to delete identifiers from
             :param identifier_type: The type of the identifier to delete.
             :param identifier_value: The value of the identifier to delete.
          """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(f'https://{self.server}/api/entity/{entity.path}/{entity.reference}/identifiers',
                               headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
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
                        f'https://{self.server}/api/entity/{entity.path}/{entity.reference}/identifiers/{_aipid}',
                        headers=headers)
                    if del_req.status_code == requests.codes.unauthorized:
                        self.token = self.__token__()
                        return self.delete_identifiers(entity, identifier_type, identifier_value)
                    if del_req.status_code == requests.codes.no_content:
                        pass
                    else:
                        return None
            return entity
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.delete_identifiers(entity, identifier_type, identifier_value)
        else:
            raise RuntimeError(request.status_code, "delete_identifier failed")

    def identifiers_for_entity(self, entity: Entity):
        """
             Get all external identifiers on an entity

             Returns the set of external identifiers on the entity

             :param entity: The entity
          """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(f'https://{self.server}/api/entity/{entity.path}/{entity.reference}/identifiers',
                               headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            identifier_list = entity_response.findall('.//{http://preservica.com/XIP/v6.0}Identifier')
            result = set()
            for identifier in identifier_list:
                identifier_value = identifier_type = ""
                for child in identifier:
                    if child.tag == "{http://preservica.com/XIP/v6.0}Type":
                        identifier_type = child.text
                    if child.tag == "{http://preservica.com/XIP/v6.0}Value":
                        identifier_value = child.text
                result.add(tuple((identifier_type, identifier_value)))
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.identifiers_for_entity(entity)
        else:
            raise RuntimeError(request.status_code, "identifiers_for_entity failed")

    def identifier(self, identifier_type: str, identifier_value: str):
        """
             Get all entities which have the external identifier

             Returns the set of entities which have the external identifier

             :param identifier_type: The identifier type
             :param identifier_value: The identifier value
          """
        headers = {HEADER_TOKEN: self.token}
        payload = {'type': identifier_type, 'value': identifier_value}
        request = requests.get(f'https://{self.server}/api/entity/entities/by-identifier', params=payload,
                               headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            entity_list = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Entity')
            result = set()
            for entity in entity_list:
                if entity.attrib['type'] == EntityType.FOLDER.value:
                    f = Folder(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(f)
                elif entity.attrib['type'] == EntityType.ASSET.value:
                    a = Asset(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(a)
                elif entity.attrib['type'] == EntityType.CONTENT_OBJECT.value:
                    c = ContentObject(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(c)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.identifier(identifier_type, identifier_value)
        else:
            raise RuntimeError(request.status_code, "identifier failed")

    def add_identifier(self, entity: Entity, identifier_type: str, identifier_value: str):
        """
             Add a new identifier to an entity

             Returns the internal identifier DB key

            :param entity: The Entity
            :param identifier_type: The identifier type
            :param identifier_value: The identifier value
          """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        xml_object = xml.etree.ElementTree.Element('Identifier', {"xmlns": NS_XIPV6})
        xml.etree.ElementTree.SubElement(xml_object, "Type").text = identifier_type
        xml.etree.ElementTree.SubElement(xml_object, "Value").text = identifier_value
        xml.etree.ElementTree.SubElement(xml_object, "Entity").text = entity.reference
        end_point = f"/{entity.path}/{entity.reference}/identifiers"
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8', xml_declaration=True)
        request = requests.post(f'https://{self.server}/api/entity{end_point}', data=xml_request, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_string = str(request.content.decode("utf-8"))
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
            raise RuntimeError(request.status_code, "add_identifier failed with error code")

    def delete_metadata(self, entity: Entity, schema: str) -> Entity:
        """
        Deletes all the metadata fragments on an entity which match the schema URI

        Returns The updated Entity

        :param entity: The Entity to delete metadata from
        :param schema: The schema URI to match against
        """
        headers = {HEADER_TOKEN: self.token}
        for url in entity.metadata:
            if schema == entity.metadata[url]:
                request = requests.delete(url, headers=headers)
                if request.status_code == requests.codes.no_content:
                    pass
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.delete_metadata(entity, schema)
                else:
                    raise RuntimeError(request.status_code, "delete_metadata failed with error code")
        return self.entity(entity.entity_type, entity.reference)

    def update_metadata(self, entity: Entity, schema: str, data: Any) -> Entity:
        """
        Update all existing metadata fragments which match the schema

        Returns The updated Entity

        :param data:   The updated XML as a string or as IO bytes
        :param entity: The Entity to update
        :param schema: The schema URI to match against
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        for url in entity.metadata:
            if schema == entity.metadata[url]:
                mref = url[url.rfind(f"{entity.reference}/metadata/") + len(f"{entity.reference}/metadata/"):]
                xml_object = xml.etree.ElementTree.Element('MetadataContainer',
                                                           {"schemaUri": schema, "xmlns": NS_XIPV6})
                xml.etree.ElementTree.SubElement(xml_object, "Ref").text = mref
                xml.etree.ElementTree.SubElement(xml_object, "Entity").text = entity.reference
                content = xml.etree.ElementTree.SubElement(xml_object, "Content")
                if isinstance(data, str):
                    ob = xml.etree.ElementTree.fromstring(data)
                    content.append(ob)
                elif hasattr(data, "read"):
                    tree = xml.etree.ElementTree.parse(data)
                    content.append(tree.getroot())
                else:
                    raise RuntimeError("Unknown data type")
                xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8', xml_declaration=True)
                request = requests.put(url, data=xml_request, headers=headers)
                if request.status_code == requests.codes.ok:
                    pass
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.update_metadata(entity, schema, data)
                else:
                    raise RuntimeError(request.status_code, "update_metadata failed with error code")
        return self.entity(entity.entity_type, entity.reference)

    def add_metadata(self, entity: Entity, schema: str, data) -> Entity:
        """
        Add a metadata fragment with a given namespace URI

        Returns The updated Entity

        :param data:   The new XML as a string or as IO bytes
        :param entity: The Entity to update
        :param schema: The schema URI of the XML document
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        xml_object = xml.etree.ElementTree.Element('MetadataContainer', {"schemaUri": schema, "xmlns": NS_XIPV6})
        xml.etree.ElementTree.SubElement(xml_object, "Entity").text = entity.reference
        content = xml.etree.ElementTree.SubElement(xml_object, "Content")
        if isinstance(data, str):
            ob = xml.etree.ElementTree.fromstring(data)
            content.append(ob)
        elif hasattr(data, "read"):
            tree = xml.etree.ElementTree.parse(data)
            content.append(tree.getroot())
        else:
            raise RuntimeError("Unknown data type")
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8', xml_declaration=True)
        end_point = f"/{entity.path}/{entity.reference}/metadata"
        request = requests.post(f'https://{self.server}/api/entity{end_point}', data=xml_request, headers=headers)
        if request.status_code == requests.codes.ok:
            return self.entity(entity_type=entity.entity_type, reference=entity.reference)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_metadata(entity, schema, data)
        else:
            raise RuntimeError(request.status_code, "add_metadata failed with error code")

    def save(self, entity: Entity) -> Entity:
        """
        Save the title and description of an entity

        Returns The updated Entity

        :param entity: The Entity to update
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        xml_object = xml.etree.ElementTree.Element(entity.tag, {"xmlns": NS_XIPV6})
        xml.etree.ElementTree.SubElement(xml_object, "Ref").text = entity.reference
        xml.etree.ElementTree.SubElement(xml_object, "Title").text = entity.title
        xml.etree.ElementTree.SubElement(xml_object, "Description").text = entity.description
        xml.etree.ElementTree.SubElement(xml_object, "SecurityTag").text = entity.security_tag
        if entity.parent is not None:
            xml.etree.ElementTree.SubElement(xml_object, "Parent").text = entity.parent

        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        request = requests.put(f'https://{self.server}/api/entity/{entity.path}/{entity.reference}',
                               data=xml_request, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            response = entity_from_string(xml_response)
            if isinstance(entity, Asset):
                return Asset(response['reference'], response['title'], response['description'],
                             response['security_tag'],
                             response['parent'], response['metadata'])
            elif isinstance(entity, Folder):
                return Folder(response['reference'], response['title'], response['description'],
                              response['security_tag'],
                              response['parent'], response['metadata'])
            elif isinstance(entity, ContentObject):
                return ContentObject(response['reference'], response['title'],
                                     response['description'],
                                     response['security_tag'],
                                     response['parent'], response['metadata'])
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.save(entity)
        else:
            raise RuntimeError(request.status_code, "save failed for entity: " + entity.reference)

    def move(self, entity: Entity, dest_folder: Folder) -> Entity:
        """
        Move an Entity (Asset or Folder) to a new Folder
        If dest_folder is None then the entity must be a Folder and will be moved to the root of the repository

        Returns The updated Entity

        :param entity:      The Entity to update
        :param dest_folder: The Folder which will become the new parent of this entity
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'text/plain'}
        if isinstance(entity, Asset) and dest_folder is None:
            raise RuntimeError(entity.reference, "Only folders can be moved to the root of the repository")
        if dest_folder is not None:
            data = dest_folder.reference
        else:
            data = "@root@"
        request = requests.put(f'https://{self.server}/api/entity/{entity.path}/{entity.reference}/parent-ref',
                               data=data, headers=headers)
        if request.status_code == requests.codes.accepted:
            return self.entity(entity.entity_type, entity.reference)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.move(entity, dest_folder)
        else:
            raise RuntimeError(request.status_code, "move failed for entity: " + entity.reference)

    def create_folder(self, title: str, description: str, security_tag: str, parent: str = None) -> Folder:
        """
        Create a new Folder in the repository
        If parent is None then the new Folder will be created at the root of the repository

        Returns The updated Entity

        :param title:       The title of the new folder
        :param description: The description of the new folder
        :param security_tag: The security_tag of the new folder
        :param parent:       The parent of the new folder, Can be None to create a root Folder
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        structural_object = xml.etree.ElementTree.Element('StructuralObject', {"xmlns": NS_XIPV6})
        xml.etree.ElementTree.SubElement(structural_object, "Ref").text = str(uuid.uuid4())
        xml.etree.ElementTree.SubElement(structural_object, "Title").text = title
        xml.etree.ElementTree.SubElement(structural_object, "Description").text = description
        xml.etree.ElementTree.SubElement(structural_object, "SecurityTag").text = security_tag
        if parent is not None:
            xml.etree.ElementTree.SubElement(structural_object, "Parent").text = parent

        xml_request = xml.etree.ElementTree.tostring(structural_object, encoding='utf-8')
        request = requests.post(f'https://{self.server}/api/entity/structural-objects', data=xml_request,
                                headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity = entity_from_string(xml_response)
            return Folder(entity['reference'], entity['title'], entity['description'],
                          entity['security_tag'],
                          entity['parent'],
                          entity['metadata'])
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.create_folder(title, description, security_tag, parent=parent)
        else:
            raise RuntimeError(request.status_code, "create_folder failed")

    def metadata_for_entity(self, entity: Entity, schema: str) -> Optional[str]:
        """
        Retrieve the first metadata fragment on an entity with a matching schema URI

        Returns XML document as a string

        :param entity:       The entity with the metadata
        :param schema:       The schema URI
        """
        for u, s in entity.metadata.items():
            if schema == s:
                return self.metadata(u)
        return None

    def security_tag_sync(self, entity: Entity, new_tag: str):
        """
         Change the security tag for a folder or asset

         Returns the updated entity after the security tag has been updated.

         :param entity:       The entity to change
         :param new_tag:      The new security tag
         """
        self.token = self.__token__()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'text/plain'}
        end_point = f"/{entity.path}/{entity.reference}/security-descriptor"
        request = requests.put(f'https://{self.server}/api/entity{end_point}?includeDescendants=false',
                               data=new_tag, headers=headers)
        if request.status_code == requests.codes.accepted:
            sleep_sec = 2
            while True:
                req = requests.get(f"https://{self.server}/api/entity/progress/{request.content.decode()}",
                                   headers=headers)
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
            return self.security_tag_sync(entity, new_tag)
        else:
            raise RuntimeError(request.status_code, f"security_tag_sync change failed on {entity.reference}")

    def security_tag_async(self, entity: Entity, new_tag: str):
        """
          Change the security tag for a folder or asset

          Returns a process ID asynchronous (without blocking)

          :param entity:       The entity to change
          :param new_tag:      The new security tag
          """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'text/plain'}
        end_point = f"/{entity.path}/{entity.reference}/security-descriptor"
        request = requests.put(f'https://{self.server}/api/entity{end_point}?includeDescendants=false',
                               data=new_tag, headers=headers)
        if request.status_code == requests.codes.accepted:
            return request.content.decode()
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.security_tag_async(entity, new_tag)
        else:
            raise RuntimeError(request.status_code, f"security_tag_async change failed on {entity.reference}")

    def metadata(self, uri: str) -> str:
        """
        Retrieve the metadata fragment which is referenced by the URI

        Returns XML document as a string

        :param uri:          The endpoint of the metadata fragment
        """
        request = requests.get(uri, headers={HEADER_TOKEN: self.token})
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('UTF-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            content = entity_response.find('.//{http://preservica.com/XIP/v6.0}Content')
            return xml.etree.ElementTree.tostring(content[0], encoding='utf-8', method='xml').decode('utf-8')
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.metadata(uri)
        else:
            raise RuntimeError(request.status_code, f"metadata failed for {uri}")

    def entity(self, entity_type: EntityType, reference: str) -> Entity:
        """
        Retrieve an entity by its type and reference

        Returns Entity (Asset, Folder, ContentObject)

        :param entity_type:          The type of entity to fetch
        :param reference:            The unique identifier of the entity
        """
        if entity_type is EntityType.CONTENT_OBJECT:
            return self.content_object(reference)
        if entity_type is EntityType.FOLDER:
            return self.folder(reference)
        if entity_type is EntityType.ASSET:
            return self.asset(reference)

    def asset(self, reference: str) -> Asset:
        """
         Retrieve an Asset by its reference

         Returns Asset

         :param reference:            The unique identifier of the entity
         """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(f'https://{self.server}/api/entity/{IO_PATH}/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity = entity_from_string(xml_response)
            return Asset(entity['reference'], entity['title'], entity['description'],
                         entity['security_tag'], entity['parent'],
                         entity['metadata'])
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.asset(reference)
        elif request.status_code == requests.codes.not_found:
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        else:
            raise RuntimeError(request.status_code, f"asset failed for {reference}")

    def folder(self, reference: str) -> Folder:
        """
         Retrieve an Folder by its reference

         Returns Folder

         :param reference:            The unique identifier of the entity
         """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(f'https://{self.server}/api/entity/{SO_PATH}/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity = entity_from_string(xml_response)
            return Folder(entity['reference'], entity['title'], entity['description'],
                          entity['security_tag'], entity['parent'],
                          entity['metadata'])
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.folder(reference)
        elif request.status_code == requests.codes.not_found:
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        else:
            raise RuntimeError(request.status_code, f"folder failed for {reference}")

    def content_object(self, reference: str) -> ContentObject:
        """
         Retrieve an ContentObject by its reference

         Returns ContentObject

         :param reference:            The unique identifier of the entity
         """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(f'https://{self.server}/api/entity/{CO_PATH}/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity = entity_from_string(xml_response)
            return ContentObject(entity['reference'], entity['title'], entity['description'],
                                 entity['security_tag'], entity['parent'],
                                 entity['metadata'])
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.content_object(reference)
        elif request.status_code == requests.codes.not_found:
            raise RuntimeError(reference, "The requested reference is not found in the repository")
        else:
            raise RuntimeError(request.status_code, f"content_object failed for {reference}")

    def content_objects(self, representation: Representation) -> Optional[list]:
        """
         Retrieve a list of content objects within a representation

         Returns List(ContentObject)

         :param representation:
         """
        headers = {HEADER_TOKEN: self.token}
        if not isinstance(representation, Representation):
            return None
        request = requests.get(f'{representation.url}', headers=headers)
        if request.status_code == requests.codes.ok:
            results = list()
            xml_response = str(request.content.decode('utf-8'))
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
            raise RuntimeError(request.status_code, "content_objects failed")

    def generation(self, url: str):
        """
         Retrieve a list of generation objects

         Returns List(Generation)

         :param url:
         """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(url, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            ge = entity_response.find('.//{http://preservica.com/XIP/v6.0}Generation')
            format_group = entity_response.find('.//{http://preservica.com/XIP/v6.0}FormatGroup')
            effective_date = entity_response.find('.//{http://preservica.com/XIP/v6.0}EffectiveDate')
            bitstreams = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Bitstream')
            bitstream_list = list()
            for bit in bitstreams:
                bitstream_list.append(self.bitstream(bit.text))
            return Generation(bool(ge.attrib['original']), bool(ge.attrib['active']),
                              format_group.text if hasattr(format_group, 'text') else None,
                              effective_date.text if hasattr(effective_date, 'text') else None,
                              bitstream_list)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.generation(url)
        else:
            raise RuntimeError(request.status_code, "generation failed")

    def bitstream(self, url: str):
        """
         Retrieve a bitstream by its url

         Returns Bitstream

         :param url:
         """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(url, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            filename = entity_response.find('.//{http://preservica.com/XIP/v6.0}Filename')
            filesize = entity_response.find('.//{http://preservica.com/XIP/v6.0}FileSize')
            fixity_values = entity_response.findall('.//{http://preservica.com/XIP/v6.0}Fixity')
            content = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}Content')
            fixity = dict()
            for f in fixity_values:
                fixity[f[0].text] = f[1].text
            bitstream = Bitstream(filename.text if hasattr(filename, 'text') else None,
                                  filesize.text if hasattr(filesize, 'text') else None, fixity,
                                  content.text if hasattr(content, 'text') else None)
            return bitstream
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.bitstream(url)
        else:
            print(f"bitstream failed with error code: {request.status_code}")
            print(request.request.url)
            raise RuntimeError(request.status_code, "bitstream failed")

    def generations(self, content_object: ContentObject) -> list:
        """
        Retrieve list of generations on a content object

        Returns list

        :param content_object:
        """
        headers = {HEADER_TOKEN: self.token}
        request = requests.get(
            f'https://{self.server}/api/entity/{CO_PATH}/{content_object.reference}/generations', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            generations = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Generation')
            result = list()
            for g in generations:
                if hasattr(g, 'text'):
                    generation = self.generation(g.text)
                    generation.content_object = content_object
                    result.append(generation)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.generations(content_object)
        else:
            raise RuntimeError(request.status_code, "generations failed")

    def representations(self, asset: Asset) -> Optional[set]:
        """
        Retrieve set of representations on an Asset

        Returns list

        :param asset:   The asset
        """
        headers = {HEADER_TOKEN: self.token}
        if not isinstance(asset, Asset):
            return None
        request = requests.get(f'https://{self.server}/api/entity/{asset.path}/{asset.reference}/representations',
                               headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            representations = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Representation')
            result = set()
            for r in representations:
                representation = Representation(asset, r.attrib['type'], r.attrib['name'], r.text)
                result.add(representation)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.representations(asset)
        else:
            raise RuntimeError(request.status_code, "representations failed")

    def all_descendants(self, folder_reference: str = None):
        """
         Retrieve list of entities below a folder in the repository

         Returns list

         :param folder_reference: The folder to find children of
         """
        for e in self.descendants(folder_reference=folder_reference):
            yield e
            if e.entity_type == EntityType.FOLDER:
                yield from self.all_descendants(folder_reference=e.reference)

    def descendants(self, folder_reference: str = None):
        maximum = 50
        paged_set = self.children(folder_reference, maximum=maximum, next_page=None)
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self.children(folder_reference, maximum=maximum, next_page=paged_set.next_page)
            for entity in paged_set.results:
                yield entity

    def children(self, folder_reference: str = None, maximum: int = 50, next_page: str = None) -> PagedSet:
        headers = {HEADER_TOKEN: self.token}
        data = {'start': str(0), 'max': str(maximum)}
        if next_page is None:
            if folder_reference is None:
                request = requests.get(f'https://{self.server}/api/entity/root/children', data=data, headers=headers)
            else:
                request = requests.get(
                    f'https://{self.server}/api/entity/structural-objects/{folder_reference}/children',
                    data=data, headers=headers)
        else:
            request = requests.get(next_page, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            children = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Child')
            result = set()
            next_url = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}Next')
            total_hits = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}TotalResults')
            for c in children:
                if c.attrib['type'] == EntityType.FOLDER.value:
                    f = Folder(c.attrib['ref'], c.attrib['title'], None, None, folder_reference, None)
                    result.add(f)
                else:
                    a = Asset(c.attrib['ref'], c.attrib['title'], None, None, folder_reference, None)
                    result.add(a)
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result, has_more, total_hits.text, url)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.children(folder_reference, maximum=maximum, next_page=next_page)
        else:
            raise RuntimeError(request.status_code, "children failed")

    def updated_entities(self, previous_days: int = 1):
        maximum = 50
        paged_set = self._updated_entities_page(previous_days=previous_days, maximum=maximum, next_page=None)
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self._updated_entities_page(previous_days=previous_days, maximum=maximum,
                                                    next_page=paged_set.next_page)
            for entity in paged_set.results:
                yield entity

    def _updated_entities_page(self, previous_days: int = 1, maximum: int = 50, next_page: str = None):
        headers = {HEADER_TOKEN: self.token}
        x = datetime.utcnow() - timedelta(days=previous_days)
        today = x.replace(tzinfo=timezone.utc).isoformat()
        if next_page is None:
            params = {'date': today, 'start': '0', 'max': str(maximum)}
            request = requests.get(f'https://{self.server}/api/entity/entities/updated-since',
                                   headers=headers, params=params)
        else:
            request = requests.get(next_page, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            entities = entity_response.findall('.//{http://preservica.com/EntityAPI/v6.0}Entity')
            result = list()
            for e in entities:
                if 'type' in e.attrib:
                    if e.attrib['type'] == EntityType.FOLDER.value:
                        f = Folder(e.attrib['ref'], e.attrib['title'], None, None, None, None)
                        result.append(f)
                    elif e.attrib['type'] == EntityType.ASSET.value:
                        a = Asset(e.attrib['ref'], e.attrib['title'], None, None, None, None)
                        result.append(a)
                    elif e.attrib['type'] == EntityType.CONTENT_OBJECT.value:
                        c = ContentObject(e.attrib['ref'], e.attrib['title'], None, None, None, None)
                        result.append(c)
            next_url = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}Next')
            total_hits = entity_response.find('.//{http://preservica.com/EntityAPI/v6.0}TotalResults')
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result, has_more, total_hits.text, url)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._updated_entities_page(previous_days=previous_days, maximum=maximum,
                                               next_page=next_page)
        else:
            raise RuntimeError(request.status_code, "updated_entities failed")
