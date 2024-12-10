"""
pyPreservica EntityAPI module definition

A client library for the Preservica Repository web services Entity API
https://us.preservica.com/api/entity/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
import hashlib
import os.path
import uuid
import xml.etree.ElementTree
from datetime import datetime, timedelta, timezone
from io import BytesIO
from time import sleep
from typing import Any, Generator, Tuple, Iterable, Union, Callable

from pyPreservica.common import *

logger = logging.getLogger(__name__)


class EntityAPI(AuthenticatedAPI):
    """
            A class for the Preservica Repository web services Entity API

            https://us.preservica.com/api/entity/documentation.html

            The EntityAPI allows users to interact with the Preservica repository


    """

    def __init__(self, username: str = None, password: str = None, tenant: str = None, server: str = None,
                 use_shared_secret: bool = False, two_fa_secret_key: str = None,
                 protocol: str = "https", request_hook: Callable = None):

        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook)

        xml.etree.ElementTree.register_namespace("oai_dc", "http://www.openarchives.org/OAI/2.0/oai_dc/")
        xml.etree.ElementTree.register_namespace("ead", "urn:isbn:1-931666-22-9")

    def user_security_tags(self, with_permissions: bool = False) -> dict:
        """
             Return  security tags available for the  current user

             :param with_permissions: Return the permissions for each security tag
             :type with_permissions: bool

             :return: dict of security tags
             :rtype:  dict
         """

        return self.security_tags_base(with_permissions=with_permissions)

    def bitstream_chunks(self, bitstream: Bitstream, chunk_size: int = CHUNK_SIZE) -> Generator:
        """
        Generator function to return bitstream chunks

        :param bitstream:   The bitstream
        :param chunk_size:  The chunk size to return
        :return:            A chunk of the requested bitstream content
        """
        if not isinstance(bitstream, Bitstream):
            logger.error("bitstream_content argument is not a Bitstream object")
            raise RuntimeError("bitstream_bytes argument is not a Bitstream object")
        with self.session.get(bitstream.content_url, headers={HEADER_TOKEN: self.token}, stream=True) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.bitstream_chunks(bitstream)
            elif request.status_code == requests.codes.ok:
                for chunk in request.iter_content(chunk_size=chunk_size):
                    yield chunk
            else:
                exception = HTTPException(bitstream.filename, request.status_code, request.url, "bitstream_content",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def bitstream_bytes(self, bitstream: Bitstream, chunk_size: int = CHUNK_SIZE) -> Union[BytesIO, None]:
        """
                Download a file represented as a Bitstream to a byteIO array

                Returns the byteIO
                Returns None if the file does not contain the correct number of bytes (default 2k)

                :param chunk_size: The buffer copy chunk size in bytes default
                :param bitstream: A Bitstream object
                :type bitstream: Bitstream

                :return: The file in bytes
                :rtype: byteIO
        """
        if not isinstance(bitstream, Bitstream):
            logger.error("bitstream_content argument is not a Bitstream object")
            raise RuntimeError("bitstream_bytes argument is not a Bitstream object")
        with self.session.get(bitstream.content_url, headers={HEADER_TOKEN: self.token}, stream=True) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.bitstream_bytes(bitstream)
            elif request.status_code == requests.codes.ok:
                file_bytes = BytesIO()
                for chunk in request.iter_content(chunk_size=chunk_size):
                    file_bytes.write(chunk)
                file_bytes.seek(0)
                if file_bytes.getbuffer().nbytes == bitstream.length:
                    logger.debug(f"Downloaded {bitstream.length} bytes from {bitstream.filename}")
                    return file_bytes
                else:
                    logger.error("Downloaded file size did not match the Preservica held value")
                    return None
            else:
                exception = HTTPException(bitstream.filename, request.status_code, request.url, "bitstream_content",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def bitstream_content(self, bitstream: Bitstream, filename: str, chunk_size: int = CHUNK_SIZE) -> Union[int, None]:
        """
        Download a file represented as a Bitstream to a local filename

        Returns the number of bytes written to the file
        Returns None if the file does not contain the correct number of bytes

        :param chunk_size: The buffer copy chunk size in bytes default
        :param bitstream: A Bitstream object
        :type bitstream: Bitstream

        :param filename: The filename to write the bytes to
        :type filename: str

        :return: The size of the file in bytes
        :rtype: int

        """

        if not isinstance(bitstream, Bitstream):
            logger.error("bitstream_content argument is not a Bitstream object")
            raise RuntimeError("bitstream_content argument is not a Bitstream object")
        with self.session.get(bitstream.content_url, headers={HEADER_TOKEN: self.token}, stream=True) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.bitstream_content(bitstream, filename)
            elif request.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in request.iter_content(chunk_size=chunk_size):
                        file.write(chunk)
                    file.flush()
                if os.path.getsize(filename) == bitstream.length:
                    logger.debug(f"Downloaded {bitstream.length} bytes into {filename}")
                    return bitstream.length
                else:
                    logger.error("Download file size did not match the Preservica held value")
                    os.remove(filename)
                    return None
            else:
                exception = HTTPException(bitstream.filename, request.status_code, request.url, "bitstream_content",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def download_opex(self, pid: str) -> str:
        """
        Download a completed OPEX export using the workflow process ID


        :param pid: A process id which identifiers the export workflow
        :type pid: str

        :return: The downloaded zip file name
        :rtype: str

        """
        headers = {HEADER_TOKEN: self.__token__(), 'Content-Type': 'application/xml;charset=UTF-8'}
        download = self.session.get(f'{self.protocol}://{self.server}/api/entity/actions/exports/{pid}/content',
                                    stream=True, headers=headers)
        if download.status_code == requests.codes.ok:
            with open(f'{pid}.zip', 'wb') as file:
                for chunk in download.iter_content(chunk_size=CHUNK_SIZE):
                    file.write(chunk)
                file.flush()
            logger.debug(f"Downloaded open package into {pid}.zip")
            return f'{pid}.zip'
        elif download.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.download_opex(pid)
        else:
            exception = HTTPException(pid, download.status_code, download.url, "download_opex",
                                      download.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def __export_opex_start__(self, entity: Entity, **kwargs) -> str:
        """
            Initiates export of the entity and downloads the opex package

            By default, includes content, metadata with the latest active generations
            and the parent hierarchy.

            Arguments are kwargs map

            IncludeContent
            IncludeMetadata
            IncludedGenerations
            IncludeParentHierarchy

        """
        if self.major_version < 7 and self.minor_version < 2:
            raise RuntimeError("export_opex API is only available when connected to a v6.2 system or above")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        include_content_options = ("Content", "NoContent")
        include_metadata_options = ("Metadata", "NoMetadata", "MetadataWithEvents")
        include_generation_options = ("LatestActive", "AllActive", "All")
        include_parent_options = ("true", "false")

        include_content = "Content"
        if 'IncludeContent' in kwargs:
            value = str(kwargs.get("IncludeContent")).strip()
            if value.casefold() in map(str.casefold, include_content_options):
                include_content = value

        include_metadata = "Metadata"
        if 'IncludeMetadata' in kwargs:
            value = str(kwargs.get("IncludeMetadata")).strip()
            if value.casefold() in map(str.casefold, include_metadata_options):
                include_metadata = value

        include_generation = "All"
        if 'IncludedGenerations' in kwargs:
            value = str(kwargs.get("IncludedGenerations")).strip()
            if value.casefold() in map(str.casefold, include_generation_options):
                include_generation = value

        include_parent = "true"
        if 'IncludeParentHierarchy' in kwargs:
            value = str(kwargs.get("IncludeParentHierarchy")).strip()
            if value.casefold() in map(str.casefold, include_parent_options):
                include_parent = value

        xml_object = xml.etree.ElementTree.Element('ExportAction', {"xmlns": self.entity_ns})
        xml.etree.ElementTree.SubElement(xml_object, "IncludeContent").text = include_content
        xml.etree.ElementTree.SubElement(xml_object, "IncludeMetadata").text = include_metadata
        xml.etree.ElementTree.SubElement(xml_object, "IncludedGenerations").text = include_generation
        xml.etree.ElementTree.SubElement(xml_object, "IncludeParentHierarchy").text = include_parent.lower()
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')

        logger.debug(xml_request)

        request = self.session.post(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/exports',
            headers=headers, data=xml_request)

        if request.status_code == requests.codes.accepted:
            return str(request.content.decode('utf-8'))
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.__export_opex_start__(entity, IncludeContent=include_content,
                                              IncludeMetadata=include_metadata, IncludedGenerations=include_generation,
                                              IncludeParentHierarchy=include_parent)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "__export_opex_start__",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def export_opex_async(self, entity: Entity, **kwargs) -> str:
        """
            Initiates export of the entity returns an id to track progress
        """
        return self.__export_opex_start__(entity, **kwargs)

    def export_opex_sync(self, entity: Entity, **kwargs) -> str:
        """
            Initiates export of the entity and downloads the opex package
            Blocks until the package is downloaded

            By default, includes content, metadata with the latest active generations
            and the parent hierarchy.

            Arguments are kwargs map

            IncludeContent
            IncludeMetadata
            IncludedGenerations
            IncludeParentHierarchy

        """
        return self.export_opex(entity, **kwargs)

    def export_opex(self, entity: Entity, **kwargs) -> str:
        """
            Initiates export of the entity and downloads the opex package
            Blocks until the package is downloaded

            By default, includes content, metadata with the latest active generations
            and the parent hierarchy.

            Arguments are kwargs map

            IncludeContent
            IncludeMetadata
            IncludedGenerations
            IncludeParentHierarchy

        """
        status = "ACTIVE"
        pid = self.__export_opex_start__(entity, **kwargs)
        while status == "ACTIVE":
            status = self.get_async_progress(pid)
            logger.debug(status)
        if status == "COMPLETED":
            return self.download_opex(pid)
        else:
            logger.error(status)
            raise RuntimeError(f"export progress failed {status}")

    def download(self, entity: Entity, filename: str) -> str:
        """
           Download a file from an asset

           Returns the filename of the new file

           :param entity: The entity containing the file
           :param filename: The filename to write the bytes to
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}
        params = {'id': f'sdb:{entity.entity_type.value}|{entity.reference}'}
        with self.session.get(f'{self.protocol}://{self.server}/api/content/download', params=params, headers=headers,
                              stream=True) as request:
            if request.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in request.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                    file.flush()
                return filename
            elif request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.download(entity, filename)
            else:
                exception = HTTPException(entity.reference, request.status_code, request.url, "download",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def has_thumbnail(self, entity: Entity) -> bool:
        """
            Does the entity have a thumbnail image attached
            Returns false if the entity has no thumbnail

            :param entity: The entity
         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}
        params = {'id': f'sdb:{entity.entity_type.value}|{entity.reference}', 'size': f'{Thumbnail.SMALL.value}'}
        with self.session.get(f'{self.protocol}://{self.server}/api/content/thumbnail', params=params,
                              headers=headers) as request:
            if request.status_code == requests.codes.ok:
                return True
            if request.status_code == requests.codes.not_found:
                return False
            elif request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.has_thumbnail(entity)
            else:
                exception = HTTPException(entity.reference, request.status_code, request.url, "has_thumbnail",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def thumbnail(self, entity: Entity, filename: str, size=Thumbnail.LARGE):
        """
            Download the thumbnail of an asset or folder

            Returns the filename of the new thumbnail file or None if the entity has no thumbnail

            :param entity: The entity containing the file
            :param filename: The filename to write the bytes to
            :param size: The size of the thumbnail
         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}
        params = {'id': f'sdb:{entity.entity_type.value}|{entity.reference}', 'size': f'{size.value}'}
        with self.session.get(f'{self.protocol}://{self.server}/api/content/thumbnail', params=params,
                              headers=headers, stream=True) as request:
            if request.status_code == requests.codes.ok:
                with open(filename, 'wb') as file:
                    for chunk in request.iter_content(chunk_size=CHUNK_SIZE):
                        file.write(chunk)
                    file.flush()
                return filename
            elif request.status_code == requests.codes.not_found:
                return None
            elif request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.thumbnail(entity, filename, size=size)
            else:
                exception = HTTPException(entity.reference, request.status_code, request.url, "thumbnail",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def delete_identifiers(self, entity: Entity, identifier_type: str = None, identifier_value: str = None):
        """
             Delete external identifiers from an entity

             Returns the entity

             :param entity: The entity to delete identifiers from
             :param identifier_type: The type of the identifier to delete.
             :param identifier_value: The value of the identifier to delete.
          """

        if (self.major_version < 7) and (self.minor_version < 1):
            raise RuntimeError("delete_identifiers API call is not available when connected to a v6.0 System")

        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/identifiers',
            headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            identifier_list = entity_response.findall(f'.//{{{self.xip_ns}}}Identifier')
            for identifier_element in identifier_list:
                _ref = _type = _value = _aipid = None
                for identifier in identifier_element:
                    if identifier.tag.endswith("Entity"):
                        _ref = identifier.text
                    if identifier.tag.endswith("Type") and identifier_type is not None:
                        _type = identifier.text
                    if identifier.tag.endswith("Value") and identifier_value is not None:
                        _value = identifier.text
                    if identifier.tag.endswith("ApiId"):
                        _aipid = identifier.text
                if _ref == entity.reference and _type == identifier_type and _value == identifier_value:
                    del_req = self.session.delete(
                        f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/identifiers/{_aipid}',
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
            logger.error(request)
            raise RuntimeError(request.status_code, "delete_identifier failed")


    def identifiers_for_entity(self, entity: Entity) -> set[Tuple]:
        """
             Get all external identifiers on an entity

             Returns the set of external identifiers on the entity

             :param entity: The Entity (Asset or Folder)
             :type  entity: Entity
          """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/identifiers',
            headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            identifier_list = entity_response.findall(f'.//{{{self.xip_ns}}}Identifier')
            result = set()
            for identifier in identifier_list:
                identifier_value = identifier_type = ""
                for child in identifier:
                    if child.tag.endswith("Type"):
                        identifier_type = child.text
                    if child.tag.endswith("Value"):
                        identifier_value = child.text
                result.add(tuple((identifier_type, identifier_value)))
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.identifiers_for_entity(entity)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "identifiers_for_entity",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception



    def identifier(self, identifier_type: str, identifier_value: str) -> set[Entity]:
        """
             Get all entities which have the external identifier

             Returns the set of entities which have the external identifier

             :param identifier_type: The identifier type
             :param identifier_value: The identifier value
          """
        headers = {HEADER_TOKEN: self.token}
        payload = {'type': identifier_type, 'value': identifier_value}
        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/entities/by-identifier', params=payload,
                                   headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            entity_list = entity_response.findall(f'.//{{{self.entity_ns}}}Entity')
            result = set()
            for entity in entity_list:
                if entity.attrib['type'] == EntityType.FOLDER.value:
                    folder = Folder(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(folder)
                elif entity.attrib['type'] == EntityType.ASSET.value:
                    asset = Asset(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(asset)
                elif entity.attrib['type'] == EntityType.CONTENT_OBJECT.value:
                    co = ContentObject(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                    result.add(co)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.identifier(identifier_type, identifier_value)
        else:
            exception = HTTPException(payload, request.status_code, request.url, "identifier",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def add_identifier(self, entity: Entity, identifier_type: str, identifier_value: str):
        """
             Add a new identifier to an entity

             Returns the internal identifier DB key

            :param entity: The Entity
            :param identifier_type: The identifier type
            :param identifier_value: The identifier value
          """

        if self.major_version < 7 and self.minor_version < 1:
            raise RuntimeError("add_identifier API call is not available when connected to a v6.0 System")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        xml_object = xml.etree.ElementTree.Element('Identifier', {"xmlns": self.xip_ns})
        xml.etree.ElementTree.SubElement(xml_object, "Type").text = identifier_type
        xml.etree.ElementTree.SubElement(xml_object, "Value").text = identifier_value
        xml.etree.ElementTree.SubElement(xml_object, "Entity").text = entity.reference
        end_point = f"/{entity.path}/{entity.reference}/identifiers"
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        logger.debug(xml_request)
        request = self.session.post(f'{self.protocol}://{self.server}/api/entity{end_point}', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.ok:
            xml_string = str(request.content.decode("utf-8"))
            identifier_response = xml.etree.ElementTree.fromstring(xml_string)
            aip_id = identifier_response.find(f'.//{{{self.xip_ns}}}ApiId')
            if hasattr(aip_id, 'text'):
                return aip_id.text
            else:
                return None
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_identifier(entity, identifier_type, identifier_value)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "add_identifier",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def update_identifiers(self, entity: Entity, identifier_type: str = None, identifier_value: str = None):
        """
             Update external identifiers based on Entity and Type

             Returns the internal identifier DB Key

             :param entity: The entity to delete identifiers from
             :param identifier_type: The type of the identifier to delete.
             :param identifier_value: The value of the identifier to delete.
          """

        if (self.major_version < 7) and (self.minor_version < 1):
            raise RuntimeError("update_identifiers API call is not available when connected to a v6.0 System")

        headers = {HEADER_TOKEN: self.token}
        response = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/identifiers',
            headers=headers)

        if response.status_code == requests.codes.ok:
            xml_response = str(response.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            identifier_list = entity_response.findall(f'.//{{{self.xip_ns}}}Identifier')
            for identifier_element in identifier_list:
                _ref = _type = _value = _aipid = None
                for identifier in identifier_element:
                    if identifier.tag.endswith("Entity"):
                        _ref = identifier.text
                    if identifier.tag.endswith("Type") and identifier_type is not None:
                        _type = identifier.text
                    if identifier.tag.endswith("Value") and identifier_value is not None:
                        _value = identifier.text
                    if identifier.tag.endswith("ApiId"):
                        _aipid = identifier.text
                if _ref == entity.reference and _type == identifier_type:

                    headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

                    xml_object = xml.etree.ElementTree.Element('Identifier', {"xmlns": self.xip_ns})
                    xml.etree.ElementTree.SubElement(xml_object, "Type").text = identifier_type
                    xml.etree.ElementTree.SubElement(xml_object, "Value").text = identifier_value
                    xml.etree.ElementTree.SubElement(xml_object, "Entity").text = entity.reference
                    xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')

                    put_response = self.session.put(
                        f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/identifiers/{_aipid}',
                        headers=headers, data=xml_request)
                    if put_response.status_code == requests.codes.ok:
                        xml_string = str(put_response.content.decode("utf-8"))
                        identifier_response = xml.etree.ElementTree.fromstring(xml_string)
                        aip_id = identifier_response.find(f'.//{{{self.xip_ns}}}ApiId')
                        if hasattr(aip_id, 'text'):
                            return aip_id.text
                        else:
                            return None
                    if put_response.status_code == requests.codes.unauthorized:
                        self.token = self.__token__()
                        return self.update_identifiers(entity, identifier_type, identifier_value)
                    if put_response.status_code == requests.codes.no_content:
                        pass
                    else:
                        return None
            return entity
        elif response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.update_identifiers(entity, identifier_type, identifier_value)
        else:
            logger.error(response)
            raise RuntimeError(response.status_code, "update_identifiers failed")

    def delete_relationships(self, entity: Entity, relationship_type: str = None):
        """
        Delete a relationship between two entities by its internal id

        This function only deletes the relationship FROM the specified entity to another entity
        It does not delete relationships TO this entity

        If relationship_type is not specified all relationships FROM this entity are deleted.

        :param entity:
        :type  entity: Entity

        :param relationship_type: The relationship type to delete
        :type  relationship_type: str
        """

        if (self.major_version < 7) and (self.minor_version < 4) and (self.patch_version < 1):
            raise RuntimeError("add_relation API call is only available with a Preservica v6.3.1 system or higher")

        for relationship in self.relationships(entity=entity):
            if relationship.direction == RelationshipDirection.FROM:
                assert relationship.this_ref == entity.reference
                if relationship_type is None:
                    self.__delete_relationship(relationship)
                if relationship_type == relationship.relationship_type:
                    self.__delete_relationship(relationship)

    def __delete_relationship(self, relationship: Relationship):
        """
            Delete a relationship between two entities by its internal id

            :param relationship:
            :return:
        """
        headers = {HEADER_TOKEN: self.token}
        entity = self.entity(relationship.entity_type, relationship.this_ref)
        end_point = f"{entity.path}/{entity.reference}/links/{relationship.api_id}"
        request = self.session.delete(f'{self.protocol}://{self.server}/api/entity/{end_point}', headers=headers)
        if request.status_code == requests.codes.no_content:
            print(relationship)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.__delete_relationship(relationship)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "delete_relationships",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def relationships(self, entity: Entity, page_size: int = 25) -> Generator[Relationship, None, None]:
        """
            List the relationship links between entities


            :param page_size: The number of items returned in a single server call
            :type: page_size: int

            :param entity: The Source Entity
            :type: entity: Entity

            :return: Generator
            :rtype:  Relationship
        """

        paged_set = self.__relationships__(entity, maximum=page_size, next_page=None)
        for e in paged_set.results:
            yield e
        while paged_set.has_more:
            paged_set = self.__relationships__(entity, maximum=page_size, next_page=paged_set.next_page)
            for e in paged_set.results:
                yield e

    def __relationships__(self, entity: Entity, maximum: int = 50, next_page: str = None) -> PagedSet:
        """
            List the relationship links between entities

            :param next_page: URL to next page of results
            :type: next_page: str

            :param maximum: The number of items returned in a single server call
            :type: maximum: int

            :param entity: The Source Entity
            :type: from_entity: Entity

            :return: relationship links
            :rtype:  list
        """

        headers = {HEADER_TOKEN: self.token}
        end_point = f"{entity.path}/{entity.reference}/links"

        if next_page is None:
            params = {'start': '0', 'max': str(maximum)}
            request = self.session.get(f'{self.protocol}://{self.server}/api/entity/{end_point}', headers=headers,
                                       params=params)
        else:
            request = self.session.get(next_page, headers=headers)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            links = entity_response.findall(f'.//{{{self.entity_ns}}}Link')
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Paging/{{{self.entity_ns}}}Next')
            total_hits = entity_response.find(f'.//{{{self.entity_ns}}}Paging/{{{self.entity_ns}}}TotalResults')
            results = []
            for link in links:
                link_type = link.attrib['linkType']
                link_direction = link.attrib['linkDirection']
                title = link.attrib['title']
                other_ref = link.attrib['ref']
                this_ref = entity.reference
                entity_type = link.attrib['type']
                api_id = link.attrib['apiId']
                results.append(Relationship(api_id, link_type, RelationshipDirection(link_direction), other_ref, title,
                                            EntityType(entity_type), this_ref, api_id))
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text

            return PagedSet(results, has_more, int(total_hits.text), url)
        elif request.status_code == requests.codes.unauthorized:
            self.__relationships__(entity=entity, maximum=maximum, next_page=next_page)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "relationships",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def add_relation(self, from_entity: Entity, relationship_type: str, to_entity: Entity):
        """
            Add a new relationship link between two Assets or Folders

            :param from_entity: The Source Entity
            :type from_entity: Entity

            :param to_entity: The Target Entity
            :type to_entity: Entity

            :param  relationship_type: The Relationship type
            :type relationship_type: str

            :return: relationship_type
            :rtype:  str
        """

        if (self.major_version < 7) and (self.minor_version < 4) and (self.patch_version < 1):
            raise RuntimeError("add_relation API call is only available with a Preservica v6.3.1 system or higher")

        assert from_entity.entity_type is not EntityType.CONTENT_OBJECT
        assert to_entity.entity_type is not EntityType.CONTENT_OBJECT

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        xml_object = xml.etree.ElementTree.Element('Link ', {"xmlns": self.xip_ns})
        xml.etree.ElementTree.SubElement(xml_object, "Type").text = relationship_type
        xml.etree.ElementTree.SubElement(xml_object, "FromEntity").text = from_entity.reference
        xml.etree.ElementTree.SubElement(xml_object, "ToEntity").text = to_entity.reference

        end_point = f"/{from_entity.path}/{from_entity.reference}/links"
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        logger.debug(xml_request)
        request = self.session.post(f'{self.protocol}://{self.server}/api/entity{end_point}', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.ok:
            xml_string = str(request.content.decode("utf-8"))
            logger.debug(xml_string)
            link_response = xml.etree.ElementTree.fromstring(xml_string)
            relation = link_response.find(f'.//{{{self.xip_ns}}}Link')
            relation_type = relation.find(f'.//{{{self.xip_ns}}}Type')
            return relation_type.text
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_relation(from_entity, relationship_type, to_entity)
        else:
            exception = HTTPException(from_entity.reference, request.status_code, request.url, "add_relation",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

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
                request = self.session.delete(url, headers=headers)
                if request.status_code == requests.codes.no_content:
                    pass
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.delete_metadata(entity, schema)
                else:
                    exception = HTTPException(entity.reference, request.status_code, request.url, "delete_metadata",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception

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

        if schema not in entity.metadata.values():
            raise RuntimeError("Only existing schema's can be updated.")

        for url in entity.metadata:
            if schema == entity.metadata[url]:
                mref = url[url.rfind(f"{entity.reference}/metadata/") + len(f"{entity.reference}/metadata/"):]
                xml_object = xml.etree.ElementTree.Element('xip:MetadataContainer',
                                                           {"schemaUri": schema, "xmlns:xip": self.xip_ns})
                xml.etree.ElementTree.SubElement(xml_object, "xip:Ref").text = mref
                xml.etree.ElementTree.SubElement(xml_object, "xip:Entity").text = entity.reference
                content = xml.etree.ElementTree.SubElement(xml_object, "xip:Content")
                if isinstance(data, str):
                    ob = xml.etree.ElementTree.fromstring(data)
                    content.append(ob)
                elif hasattr(data, "read"):
                    tree = xml.etree.ElementTree.parse(data)
                    content.append(tree.getroot())
                else:
                    raise RuntimeError("Unknown data type")
                xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
                logger.debug(xml_request)
                request = self.session.put(url, data=xml_request, headers=headers)
                if request.status_code == requests.codes.ok:
                    pass
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.update_metadata(entity, schema, data)
                else:
                    exception = HTTPException(entity.reference, request.status_code, request.url, "update_metadata",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception
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

        xml_object = xml.etree.ElementTree.Element('xip:MetadataContainer', {"schemaUri": schema,
                                                                             "xmlns:xip": self.xip_ns})
        xml.etree.ElementTree.SubElement(xml_object, "xip:Entity").text = entity.reference
        content = xml.etree.ElementTree.SubElement(xml_object, "xip:Content")
        if isinstance(data, str):
            ob = xml.etree.ElementTree.fromstring(data)
            content.append(ob)
        elif hasattr(data, "read"):
            tree = xml.etree.ElementTree.parse(data)
            content.append(tree.getroot())
        else:
            raise RuntimeError("Unknown data type")
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        end_point = f"/{entity.path}/{entity.reference}/metadata"
        logger.debug(xml_request)
        request = self.session.post(f'{self.protocol}://{self.server}/api/entity{end_point}', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.ok:
            return self.entity(entity_type=entity.entity_type, reference=entity.reference)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_metadata(entity, schema, data)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "add_metadata",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def save(self, entity: Entity) -> Entity:
        """
        Save the title and description of an entity

        Returns The updated Entity

        :param entity: The Entity to update
        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        xml_object = xml.etree.ElementTree.Element(entity.tag, {"xmlns": self.xip_ns})
        xml.etree.ElementTree.SubElement(xml_object, "Ref").text = entity.reference
        xml.etree.ElementTree.SubElement(xml_object, "Title").text = entity.title
        xml.etree.ElementTree.SubElement(xml_object, "Description").text = entity.description
        xml.etree.ElementTree.SubElement(xml_object, "SecurityTag").text = entity.security_tag

        if entity.custom_type is not None:
            xml.etree.ElementTree.SubElement(xml_object, "CustomType").text = entity.custom_type

        if entity.parent is not None:
            xml.etree.ElementTree.SubElement(xml_object, "Parent").text = entity.parent

        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        logger.debug(xml_request)
        request = self.session.put(f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}',
                                   data=xml_request, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            response = self.entity_from_string(xml_response)
            if isinstance(entity, Asset):
                asset = Asset(response['reference'], response['title'], response['description'],
                              response['security_tag'],
                              response['parent'], response['metadata'])
                if 'CustomType' in response:
                    asset.custom_type = response['CustomType']
                return asset
            elif isinstance(entity, Folder):
                folder = Folder(response['reference'], response['title'], response['description'],
                                response['security_tag'],
                                response['parent'], response['metadata'])
                if 'CustomType' in response:
                    folder.custom_type = response['CustomType']
                return folder
            elif isinstance(entity, ContentObject):
                content_object = ContentObject(response['reference'], response['title'],
                                               response['description'],
                                               response['security_tag'],
                                               response['parent'], response['metadata'])
                if 'CustomType' in response:
                    content_object.custom_type = response['CustomType']
                return content_object
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.save(entity)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "save",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def move_async(self, entity: Entity, dest_folder: Folder) -> str:
        """
        Move an Entity (Asset or Folder) to a new Folder
        If dest_folder is None then the entity must be a Folder and will be moved to the root of the repository


        Returns a process ID asynchronous (without blocking)

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
        request = self.session.put(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/parent-ref',
            data=data, headers=headers)
        if request.status_code == requests.codes.accepted:
            return request.content.decode()
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.move_async(entity, dest_folder)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "move_async",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def get_async_progress(self, pid: str) -> str:
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'text/plain'}
        request = self.session.get(f"{self.protocol}://{self.server}/api/entity/progress/{pid}", headers=headers)
        if request.status_code == requests.codes.ok:
            entity_response = xml.etree.ElementTree.fromstring(request.content.decode("utf-8"))
            status = entity_response.find(".//{http://status.preservica.com}Status")
            if hasattr(status, 'text'):
                return status.text
            else:
                return "UNKNOWN"
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.get_async_progress(pid)
        else:
            exception = HTTPException(pid, request.status_code, request.url, "get_async_progress",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def move_sync(self, entity: Entity, dest_folder: Folder) -> Entity:
        """
        Move an Entity (Asset or Folder) to a new Folder
        If dest_folder is None then the entity must be a Folder and will be moved to the root of the repository

        Returns The updated Entity.
        Blocks until the move is complete.

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
        request = self.session.put(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/parent-ref',
            data=data, headers=headers)
        if request.status_code == requests.codes.accepted:
            sleep_sec = 1
            while True:
                status = self.get_async_progress(request.content.decode("utf-8"))
                if status != "ACTIVE":
                    return self.entity(entity.entity_type, entity.reference)
                else:
                    sleep(sleep_sec)
                    sleep_sec = sleep_sec + 1

        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.move_sync(entity, dest_folder)
        else:
            exception = HTTPException(entity, request.status_code, request.url, "move_sync",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def move(self, entity: Entity, dest_folder: Folder) -> Entity:
        """
        Move an Entity (Asset or Folder) to a new Folder
        If dest_folder is None then the entity must be a Folder and will be moved to the root of the repository

        Returns The updated Entity

        :param entity:      The Entity to update
        :param dest_folder: The Folder which will become the new parent of this entity
        """
        return self.move_sync(entity, dest_folder)

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

        structural_object = xml.etree.ElementTree.Element('StructuralObject', {"xmlns": self.xip_ns})
        xml.etree.ElementTree.SubElement(structural_object, "Ref").text = str(uuid.uuid4())
        xml.etree.ElementTree.SubElement(structural_object, "Title").text = title
        xml.etree.ElementTree.SubElement(structural_object, "Description").text = description
        xml.etree.ElementTree.SubElement(structural_object, "SecurityTag").text = security_tag
        if parent is not None:
            xml.etree.ElementTree.SubElement(structural_object, "Parent").text = parent

        xml_request = xml.etree.ElementTree.tostring(structural_object, encoding='utf-8')
        logger.debug(xml_request)
        request = self.session.post(f'{self.protocol}://{self.server}/api/entity/structural-objects', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity = self.entity_from_string(xml_response)
            return Folder(entity['reference'], entity['title'], entity['description'],
                          entity['security_tag'],
                          entity['parent'],
                          entity['metadata'])
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.create_folder(title, description, security_tag, parent=parent)
        else:
            exception = HTTPException(title, request.status_code, request.url, "create_folder",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def all_metadata(self, entity: Entity) -> Tuple:
        """
        Retrieve all metadata fragments on an entity

        Returns XML documents in a tuple

        :param entity:       The entity with the metadata
        """

        for uri, schema in entity.metadata.items():
            yield tuple((str(schema), self.metadata(uri)))

    def metadata_for_entity(self, entity: Entity, schema: str) -> Union[str, None]:
        """
        Retrieve the first metadata fragment on an entity with a matching schema URI

        Returns XML document as a string

        :param entity:       The entity with the metadata
        :param schema:       The schema URI
        """

        # if the entity is a lightweight enum version request the full object
        if entity.metadata is None:
            entity = self.entity(entity.entity_type, entity.reference)

        for uri, schema_name in entity.metadata.items():
            if schema == schema_name:
                return self.metadata(uri)
        return

    def metadata_tag_for_entity(self, entity: Entity, schema: str, tag: str, isXpath: bool = False) -> str:
        """
        Retrieve the first value of the tag from a metadata template given by schema

        Returns XML document as a string

        :param isXpath:      True if the tag name is a fully qualified xpath expression
        :param entity:       The entity with the metadata
        :param schema:       The schema URI
        :param tag:          The tag name
        """

        xml_doc = self.metadata_for_entity(entity, schema)
        if xml_doc:
            xml_object = xml.etree.ElementTree.fromstring(xml_doc)
            if isXpath is False:
                return xml_object.find(f'.//{{*}}{tag}').text
            else:
                return xml_object.find(tag).text

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
        request = self.session.put(f'{self.protocol}://{self.server}/api/entity{end_point}?includeDescendants=false',
                                   data=new_tag, headers=headers)
        if request.status_code == requests.codes.accepted:
            sleep_sec = 1
            while True:
                status = self.get_async_progress(request.content.decode("utf-8"))
                if status != "ACTIVE":
                    return self.entity(entity.entity_type, entity.reference)
                else:
                    sleep(sleep_sec)
                    sleep_sec = sleep_sec + 1
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.security_tag_sync(entity, new_tag)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "security_tag_sync",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def security_tag_async(self, entity: Entity, new_tag: str):
        """
          Change the security tag for a folder or asset

          Returns a process ID asynchronous (without blocking)

          :param entity:       The entity to change
          :param new_tag:      The new security tag
          """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'text/plain'}
        end_point = f"/{entity.path}/{entity.reference}/security-descriptor"
        request = self.session.put(f'{self.protocol}://{self.server}/api/entity{end_point}?includeDescendants=false',
                                   data=new_tag, headers=headers)
        if request.status_code == requests.codes.accepted:
            return request.content.decode("utf-8")
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.security_tag_async(entity, new_tag)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url, "security_tag_async",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def metadata(self, uri: str) -> str:
        """
        Retrieve the metadata fragment which is referenced by the URI

        Returns XML document as a string

        :param uri:          The endpoint of the metadata fragment
        """
        request = self.session.get(uri, headers={HEADER_TOKEN: self.token})
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            content = entity_response.find(f'.//{{{self.xip_ns}}}Content')
            return xml.etree.ElementTree.tostring(content[0], encoding='utf-8', method='xml').decode('utf-8')
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.metadata(uri)
        else:
            exception = HTTPException(uri, request.status_code, request.url, "metadata",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

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

    def add_physical_asset(self, title: str, description: str, parent: Folder, security_tag: str = "open") -> Asset:
        """
        Create a new asset which represents a physical object

        Returns Asset

        :param title:           The title of the new Asset
        :param description:     The description of the new Asset
        :param parent:          The parent folder
        :param security_tag:    The security setting
        """

        if (self.major_version < 7) and (self.minor_version < 4):
            raise RuntimeError(
                "add_physical_asset API call is only available with a Preservica v6.4.0 system or higher")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        xip_object = xml.etree.ElementTree.Element('XIP ', {"xmlns": self.xip_ns})
        io_object = xml.etree.ElementTree.SubElement(xip_object, "InformationObject")
        xml.etree.ElementTree.SubElement(io_object, "Title").text = str(title)
        xml.etree.ElementTree.SubElement(io_object, "Description").text = str(description)
        xml.etree.ElementTree.SubElement(io_object, "SecurityTag").text = str(security_tag)
        xml.etree.ElementTree.SubElement(io_object, "Parent").text = parent.reference
        rep_object = xml.etree.ElementTree.SubElement(xip_object, "Representation")
        xml.etree.ElementTree.SubElement(rep_object, "Type").text = "Physical"

        xml_request = xml.etree.ElementTree.tostring(xip_object, encoding='utf-8')

        request = self.session.post(f'{self.protocol}://{self.server}/api/entity/{IO_PATH}', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.ok:
            xml_string = str(request.content.decode("utf-8"))
            entity = self.entity_from_string(xml_string)
            return Asset(entity['reference'], entity['title'], entity['description'],
                         entity['security_tag'], entity['parent'],
                         entity['metadata'])
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_physical_asset(title, description, parent, security_tag)
        else:
            exception = HTTPException(title, request.status_code, request.url, "add_physical_asset",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def asset(self, reference: str) -> Asset:
        """
         Retrieve an Asset by its reference

         Returns Asset

         :param reference:            The unique identifier of the entity
         """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/{IO_PATH}/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity = self.entity_from_string(xml_response)
            asset = Asset(entity['reference'], entity['title'], entity['description'],
                          entity['security_tag'], entity['parent'],
                          entity['metadata'])
            if 'CustomType' in entity:
                asset.custom_type = entity['CustomType']
            return asset
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.asset(reference)
        elif request.status_code == requests.codes.not_found:
            exception = ReferenceNotFoundException(reference, request.status_code, request.url, "asset")
            logger.error(exception)
            raise exception
        else:
            exception = HTTPException(reference, request.status_code, request.url, "asset",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def folder(self, reference: str) -> Folder:
        """
         Retrieve a Folder by its reference

         Returns Folder

         :param reference:            The unique identifier of the entity
         """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/{SO_PATH}/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity = self.entity_from_string(xml_response)
            folder = Folder(entity['reference'], entity['title'], entity['description'],
                            entity['security_tag'], entity['parent'],
                            entity['metadata'])
            if 'CustomType' in entity:
                folder.custom_type = entity['CustomType']
            return folder
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.folder(reference)
        elif request.status_code == requests.codes.not_found:
            exception = ReferenceNotFoundException(reference, request.status_code, request.url, "folder")
            logger.error(exception)
            raise exception
        else:
            exception = HTTPException(reference, request.status_code, request.url, "folder",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def content_object(self, reference: str) -> ContentObject:
        """
         Retrieve an ContentObject by its reference

         Returns ContentObject

         :param reference:            The unique identifier of the entity
         """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/{CO_PATH}/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity = self.entity_from_string(xml_response)
            content_object = ContentObject(entity['reference'], entity['title'], entity['description'],
                                           entity['security_tag'], entity['parent'],
                                           entity['metadata'])
            if 'CustomType' in entity:
                content_object.custom_type = entity['CustomType']
            return content_object
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.content_object(reference)
        elif request.status_code == requests.codes.not_found:
            exception = ReferenceNotFoundException(reference, request.status_code, request.url, "content_object")
            logger.error(exception)
            raise exception
        else:
            exception = HTTPException(reference, request.status_code, request.url, "content_object",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def content_objects(self, representation: Representation) -> list[ContentObject]:
        """
         Retrieve a list of content objects within a representation

         :param representation:

         :returns list[ContentObject]

         """
        headers = {HEADER_TOKEN: self.token}
        if not isinstance(representation, Representation):
            logger.warning("representation is not of type Representation")
            return []
        request = self.session.get(f'{representation.url}', headers=headers)
        if request.status_code == requests.codes.ok:
            results = []
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            content_objects = entity_response.findall(f'.//{{{self.xip_ns}}}Representation/'
                                                      f'{{{self.xip_ns}}}ContentObjects/{{{self.xip_ns}}}ContentObject')
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
            exception = HTTPException(representation.name, request.status_code, request.url, "content_objects",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def generation(self, url: str) -> Generation:
        """
         Retrieve a list of generation objects

         :param url:
         :returns Generation
         """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(url, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            ge = entity_response.find(f'.//{{{self.xip_ns}}}Generation')
            format_group = entity_response.find(f'.//{{{self.xip_ns}}}FormatGroup')
            effective_date = entity_response.find(f'.//{{{self.xip_ns}}}EffectiveDate')

            formats = entity_response.findall(f'.//{{{self.xip_ns}}}Formats/{{{self.xip_ns}}}Format')
            formats_list = []
            for tech_format in formats:
                format_dict = {'Valid': tech_format.attrib['valid']}
                puid = tech_format.find(f'.//{{{self.xip_ns}}}PUID')
                format_dict['PUID'] = puid.text if hasattr(puid, 'text') else None
                priority = tech_format.find(f'.//{{{self.xip_ns}}}Priority')
                format_dict['Priority'] = priority.text if hasattr(priority, 'text') else None
                method = tech_format.find(f'.//{{{self.xip_ns}}}IdentificationMethod')
                format_dict['IdentificationMethod'] = method.text if hasattr(method, 'text') else None
                name = tech_format.find(f'.//{{{self.xip_ns}}}FormatName')
                format_dict['FormatName'] = name.text if hasattr(name, 'text') else None
                version = tech_format.find(f'.//{{{self.xip_ns}}}FormatVersion')
                format_dict['FormatVersion'] = version.text if hasattr(version, 'text') else None
                formats_list.append(format_dict)

            index = int(url.rsplit("/", 1)[-1])

            properties = entity_response.findall(f'.//{{{self.xip_ns}}}Properties/{{{self.xip_ns}}}Property')
            property_set = []
            for tech_props in properties:
                tech_props_dict = {}
                puid = tech_props.find(f'.//{{{self.xip_ns}}}PUID')
                tech_props_dict['PUID'] = puid.text if hasattr(puid, 'text') else None
                name = tech_props.find(f'.//{{{self.xip_ns}}}PropertyName')
                tech_props_dict['PropertyName'] = name.text if hasattr(name, 'text') else None
                value = tech_props.find(f'.//{{{self.xip_ns}}}Value')
                tech_props_dict['Value'] = value.text if hasattr(value, 'text') else None
                property_set.append(tech_props_dict)

            bitstreams = entity_response.findall(f'./{{{self.entity_ns}}}Bitstreams/{{{self.entity_ns}}}Bitstream')
            bitstream_list = []
            for bit in bitstreams:
                bitstream_list.append(self.bitstream(bit.text))
            generation = Generation(strtobool(ge.attrib['original']), strtobool(ge.attrib['active']),
                                    format_group.text if hasattr(format_group, 'text') else None,
                                    effective_date.text if hasattr(effective_date, 'text') else None,
                                    bitstream_list)
            generation.formats = formats_list
            generation.properties = property_set
            generation.gen_index = index
            return generation
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.generation(url)
        else:
            exception = HTTPException(url, request.status_code, request.url, "generation",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def _integrity_checks(self, bitstream: Bitstream, maximum: int = 10, next_page: str = None):
        headers = {HEADER_TOKEN: self.token}
        if next_page is None:
            url = re.sub('content$', f'integrity-check-history', bitstream.content_url)
            params = {'start': '0', 'max': str(maximum)}
            request = self.session.get(url, headers=headers, params=params)
        else:
            request = self.session.get(next_page, headers=headers)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            histories = entity_response.findall(f'.//{{{self.entity_ns}}}IntegrityCheckHistory')

            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Paging/{{{self.entity_ns}}}Next')
            total_hits = entity_response.find(f'.//{{{self.entity_ns}}}Paging/{{{self.entity_ns}}}TotalResults')
            results = []
            for history in histories:
                xip_type = history.find(f'./{{{self.xip_ns}}}Type')
                xip_success = history.find(f'./{{{self.xip_ns}}}Success')
                xip_date = history.find(f'./{{{self.xip_ns}}}Date')
                xip_adapter_name = history.find(f'./{{{self.xip_ns}}}AdapterName')
                xip_fixed = history.find(f'./{{{self.xip_ns}}}Fixed')
                xip_reason = history.find(f'./{{{self.xip_ns}}}Reason')

                check = IntegrityCheck(xip_type.text if hasattr(xip_type, 'text') else None,
                                       xip_success.text if hasattr(xip_success, 'text') else None,
                                       xip_date.text if hasattr(xip_date, 'text') else None,
                                       xip_adapter_name.text if hasattr(xip_adapter_name, 'text') else None,
                                       xip_fixed.text if hasattr(xip_fixed, 'text') else None,
                                       xip_reason.text if hasattr(xip_reason, 'text') else None)
                results.append(check)
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text

            return PagedSet(results, has_more, int(total_hits.text), url)

        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._integrity_checks(bitstream, maximum, next_page)
        else:
            exception = HTTPException(bitstream.filename, request.status_code, request.url, "_integrity_checks",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def integrity_checks(self, bitstream: Bitstream) -> Generator:
        """
         Return integrity checks for a bitstream

         """
        maximum = 10
        paged_set = self._integrity_checks(bitstream=bitstream, maximum=maximum, next_page=None)
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self._integrity_checks(bitstream=bitstream, maximum=maximum, next_page=paged_set.next_page)
            for entity in paged_set.results:
                yield entity

    def bitstream(self, url: str) -> Bitstream:
        """
         Retrieve a bitstream by its url

         Returns Bitstream

         :param url:
         """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(url, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            logger.debug(xml_response)
            filename = entity_response.find(f'.//{{{self.xip_ns}}}Filename')
            filesize = entity_response.find(f'.//{{{self.xip_ns}}}FileSize')
            fixity_values = entity_response.findall(f'.//{{{self.xip_ns}}}Fixity')
            content = entity_response.find(f'.//{{{self.entity_ns}}}Content')

            index = int(url.rsplit("/", 1)[-1])

            fixity = {}
            for f in fixity_values:
                fixity[f[0].text] = f[1].text
            bitstream = Bitstream(filename.text if hasattr(filename, 'text') else None,
                                  int(filesize.text) if hasattr(filesize, 'text') else None, fixity,
                                  content.text if hasattr(content, 'text') else None)

            bitstream.bs_index = index
            return bitstream
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.bitstream(url)
        else:
            exception = HTTPException(url, request.status_code, request.url, "bitstream",
                                      request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def replace_generation_sync(self, content_object: ContentObject, file_name, fixity_algorithm=None,
                                fixity_value=None) -> str:
        """
            Replace the last active generation of a content object with a new digital file.

            Starts the workflow and blocks until the workflow completes.

        """

        status = "ACTIVE"

        pid = self.replace_generation_async(content_object=content_object, file_name=file_name,
                                            fixity_algorithm=fixity_algorithm, fixity_value=fixity_value)

        while status == "ACTIVE":
            status = self.get_async_progress(pid)

        return status

    def replace_generation_async(self, content_object: ContentObject, file_name, fixity_algorithm=None,
                                 fixity_value=None) -> str:
        """
        Replace the last active generation of a content object with a new digital file.

        Starts the workflow and returns

        """
        if (self.major_version < 7) and (self.minor_version < 2) and (self.patch_version < 1):
            raise RuntimeError("replace API call is only available when connected to a v6.2.1 System")
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}

        params = {"replaceType": "previous"}

        if fixity_algorithm is None:
            generation = self.generations(content_object=content_object).pop()
            bitstream = generation.bitstreams.pop()
            for algo, value in bitstream.fixity.items():
                fixity_algorithm = algo
                if "MD5" in fixity_algorithm.upper():
                    fixity_value = FileHash(hashlib.md5)(file_name)
                if "SHA1" in fixity_algorithm.upper() or "SHA-1" in fixity_algorithm.upper():
                    fixity_value = FileHash(hashlib.sha1)(file_name)
                if "SHA256" in fixity_algorithm.upper() or "SHA-256" in fixity_algorithm.upper():
                    fixity_value = FileHash(hashlib.sha256)(file_name)
                if "SHA512" in fixity_algorithm.upper() or "SHA-512" in fixity_algorithm.upper():
                    fixity_value = FileHash(hashlib.sha512)(file_name)

        if fixity_algorithm and fixity_value:
            if "MD5" in fixity_algorithm.upper():
                headers["Fixity-MD5"] = fixity_value
            if "SHA1" in fixity_algorithm.upper() or "SHA-1" in fixity_algorithm.upper():
                headers["Fixity-SHA-1"] = fixity_value
            if "SHA256" in fixity_algorithm.upper() or "SHA-256" in fixity_algorithm.upper():
                headers["Fixity-SHA-256"] = fixity_value
            if "SHA512" in fixity_algorithm.upper() or "SHA-512" in fixity_algorithm.upper():
                headers["Fixity-SHA-512"] = fixity_value

        headers["Filename"] = os.path.basename(file_name)
        headers['Content-Length'] = str(os.path.getsize(file_name))

        with open(file_name, 'rb') as f:
            request = self.session.post(
                f'{self.protocol}://{self.server}/api/entity/{CO_PATH}/{content_object.reference}/generations',
                params=params, data=f, headers=headers)

        if request.status_code == requests.codes.ok:
            return str(request.content.decode('utf-8'))
        elif request.status_code == requests.codes.unauthorized:
            return self.replace_generation_async(content_object=content_object, file_name=file_name,
                                                 fixity_algorithm=fixity_algorithm, fixity_value=fixity_value)
        else:
            exception = HTTPException(content_object.reference, request.status_code, request.url,
                                      "replace_generation_async", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def generations(self, content_object: ContentObject) -> list[Generation]:
        """
        Retrieve list of generations on a content object

        Returns list

        :param content_object:
        """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{CO_PATH}/{content_object.reference}/generations',
            headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            generations = entity_response.findall(f'.//{{{self.entity_ns}}}Generation')
            result = []
            for g in generations:
                if hasattr(g, 'text'):
                    generation = self.generation(g.text)
                    generation.asset = content_object.asset
                    generation.content_object = content_object
                    generation.representation_type = content_object.representation_type
                    result.append(generation)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.generations(content_object)
        else:
            exception = HTTPException(content_object.reference, request.status_code, request.url,
                                      "generations", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def bitstreams_for_asset(self, asset: Union[Asset, Entity]) -> Iterable[Bitstream]:
        """

        Return all the bitstreams within an asset.
        This includes all the representations and content objects


        :param asset:               The asset
        :return:
        """

        for representation in self.representations(asset):
            for content_object in self.content_objects(representation):
                for generation in self.generations(content_object):
                    if generation.active:
                        for bitstream in generation.bitstreams:
                            bitstream.representation = representation
                            bitstream.content_object = content_object
                            bitstream.generation = generation
                            yield bitstream

    def representations(self, asset: Asset) -> set[Representation]:
        """
        Retrieve set of representations on an Asset

        :param asset:   The asset
        :returns set[Representation]
        """
        headers = {HEADER_TOKEN: self.token}
        if not isinstance(asset, Asset):
            return set()
        request = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{asset.path}/{asset.reference}/representations',
            headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            representations = entity_response.findall(f'.//{{{self.entity_ns}}}Representation')
            result = set()
            for r in representations:
                representation = Representation(asset, r.get('type'), r.get("name", None), r.text)
                result.add(representation)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.representations(asset)
        else:
            exception = HTTPException(asset.reference, request.status_code, request.url,
                                      "representations", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def remove_thumbnail(self, entity: Entity):
        """
          remove a thumbnail icon to a folder or asset


          :param entity:   The Entity
          """
        if self.major_version < 7 and self.minor_version < 2:
            raise RuntimeError("Thumbnail API is only available when connected to a v6.2 System")

        if isinstance(entity, ContentObject):
            raise RuntimeError("Thumbnails cannot be added to Content Objects")

        headers = {HEADER_TOKEN: self.token}

        request = self.session.delete(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/preview',
            headers=headers)
        if request.status_code == requests.codes.no_content:
            return str(request.content.decode('utf-8'))
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.remove_thumbnail(entity)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url,
                                      "remove_thumbnail", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def add_access_representation(self, entity: Entity, access_file: str, name: str = "Access"):
        """
        Add a new representation to an existing asset.

        :param entity:          The existing asset which will receive the new representation
        :param access_file:     The new digital file
        :param name:            The name of the new access representation defaults to "Access"
        :return:
        """

        if self.major_version < 7 and self.minor_version < 12:
            raise RuntimeError("Add Representation API is only available when connected to a v6.12 System")

        if isinstance(entity, Folder) or isinstance(entity, ContentObject):
            raise RuntimeError("Add Representation cannot be added to Folders and Content Objects")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}

        filename = os.path.basename(access_file)

        params = {'type': 'Access', 'name': name, 'filename': filename}

        with open(access_file, 'rb') as fd:
            request = self.session.post(
                f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/representations',
                data=fd, headers=headers, params=params)
            if request.status_code == requests.codes.accepted:
                return str(request.content.decode('utf-8'))
            elif request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.add_access_representation(entity, access_file, name)
            else:
                exception = HTTPException(entity.reference, request.status_code, request.url,
                                          "add_access_representation", request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def add_thumbnail(self, entity: Entity, image_file: str):
        """
         add a thumbnail icon to a folder or asset


         :param entity:       The Entity
         :param image_file:   Path to image file
         """
        if self.major_version < 7 and self.minor_version < 2:
            raise RuntimeError("Thumbnail API is only available when connected to a v6.2 System")

        if isinstance(entity, ContentObject):
            raise RuntimeError("Thumbnails cannot be added to Content Objects")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/octet-stream'}

        with open(image_file, 'rb') as fd:
            request = self.session.put(
                f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/preview',
                data=fd, headers=headers)

        if request.status_code == requests.codes.no_content:
            return str(request.content.decode('utf-8'))
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_thumbnail(entity, image_file)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url,
                                      "add_thumbnail", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def _event_actions(self, entity: Entity, maximum: int):
        """
         event actions performed against this entity
        """
        if self.major_version < 7 and self.minor_version < 1:
            logger.error("Entity events is only available when connected to a v6.1 System")
            raise RuntimeError("Entity events is only available when connected to a v6.1 System")

        headers = {HEADER_TOKEN: self.token}
        params = {'start': str(0), 'max': str(maximum)}

        request = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/event-actions',
            params=params, headers=headers)

        if request.status_code == requests.codes.ok:
            pass
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._event_actions(entity, maximum=maximum)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url,
                                      "_event_actions", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def all_descendants(self, folder: Union[Folder, Entity] = None) -> Generator[Entity, None, None]:
        """
         Retrieve list of entities below a folder in the repository

         Returns list

         :param folder: The folder to find children of
         """
        for entity in self.descendants(folder=folder):
            yield entity
            if entity.entity_type == EntityType.FOLDER:
                yield from self.all_descendants(folder=entity)

    def descendants(self, folder: Union[str, Folder] = None) -> Generator[Entity, None, None]:
        maximum = 100
        paged_set = self.children(folder, maximum=maximum, next_page=None)
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self.children(folder, maximum=maximum, next_page=paged_set.next_page)
            for entity in paged_set.results:
                yield entity

    def children(self, folder: Union[str, Folder] = None, maximum: int = 100, next_page: str = None) -> PagedSet:
        headers = {HEADER_TOKEN: self.token}
        data = {'start': str(0), 'max': str(maximum)}

        if isinstance(folder, Folder):
            folder_reference = folder.reference
        else:
            folder_reference = folder
        if next_page is None:
            if folder_reference is None:
                request = self.session.get(f'{self.protocol}://{self.server}/api/entity/root/children', params=data,
                                           headers=headers)
            else:
                if hasattr(folder, "reference"):
                    folder_reference = folder.reference
                request = self.session.get(
                    f'{self.protocol}://{self.server}/api/entity/structural-objects/{folder_reference}/children',
                    params=data, headers=headers)
        else:
            request = self.session.get(next_page, headers=headers)
        logger.debug(request.url)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            children = entity_response.findall(f'.//{{{self.entity_ns}}}Child')
            result = set()
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Next')
            total_hits = entity_response.find(f'.//{{{self.entity_ns}}}TotalResults')
            for child in children:
                if child.attrib['type'] == EntityType.FOLDER.value:
                    folder = Folder(child.attrib['ref'], child.attrib['title'], None, None, folder_reference, None)
                    result.add(folder)
                else:
                    asset = Asset(child.attrib['ref'], child.attrib['title'], None, None, folder_reference, None)
                    result.add(asset)
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result, has_more, int(total_hits.text), url)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.children(folder_reference, maximum=maximum, next_page=next_page)
        else:
            exception = HTTPException(folder.reference, request.status_code, request.url,
                                      "children", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def all_ingest_events(self, previous_days: int = 1) -> Generator:
        self.token = self.__token__()
        previous = datetime.utcnow() - timedelta(days=previous_days)
        from_date = previous.replace(tzinfo=timezone.utc).isoformat()
        to_date = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        paged_set = self._all_events_page(maximum=25, next_page=None, type="Ingest", from_date=from_date,
                                          to_date=to_date)
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self._all_events_page(maximum=25, next_page=paged_set.next_page, type="Ingest",
                                              from_date=from_date, to_date=to_date)
            for entity in paged_set.results:
                yield entity

    def all_events(self) -> Generator:
        self.token = self.__token__()
        paged_set = self._all_events_page()
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self._all_events_page(next_page=paged_set.next_page)
            for entity in paged_set.results:
                yield entity

    def _entity_from_event_page(self, event_id: str, maximum: int = 25, next_page: str = None):
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        if next_page is None:
            url = f'{self.protocol}://{self.server}/api/entity/events/{event_id}/event-actions'
            response = requests.get(url, params={'start': 0, 'max': maximum}, headers=headers)
        else:
            response = requests.get(next_page, headers=headers)
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._entity_from_event_page(event_id, maximum, next_page)
        if response.status_code == 200:
            xml_response = str(response.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            actions = entity_response.findall(f'.//{{{self.xip_ns}}}EventAction')
            result_list = []
            for action in actions:
                entity_ref = action.findall(f'.//{{{self.xip_ns}}}Entity')
                for refs in entity_ref:
                    result_list.append(refs.text)
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Next')
            total_hits = entity_response.find(f'.//{{{self.entity_ns}}}TotalResults')
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result_list, has_more, int(total_hits.text), url)

    def entity_from_event(self, event_id: str) -> Generator:
        self.token = self.__token__()
        paged_set = self._entity_from_event_page(event_id, 25, None)
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self._entity_from_event_page(event_id, 25, next_page=paged_set.next_page)
            for entity in paged_set.results:
                yield entity

    def _all_events_page(self, maximum: int = 25, next_page: str = None, **kwargs) -> PagedSet:
        """
          event actions performed against this repository
         """
        headers = {HEADER_TOKEN: self.token}

        params = {'start': str(0), 'max': str(maximum)}
        if "type" in kwargs:
            params["types"] = kwargs.get("type")
        if "from_date" in kwargs:
            params["from"] = kwargs.get("from_date")
        if "to_date" in kwargs:
            params["to"] = kwargs.get("to_date")

        if next_page is None:
            request = self.session.get(f'{self.protocol}://{self.server}/api/entity/events', params=params,
                                       headers=headers)
        else:
            request = self.session.get(next_page, headers=headers)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            events = entity_response.findall(f'.//{{{self.xip_ns}}}Event')
            result_list = []
            for event in events:
                result = {'eventType': event.attrib['type']}
                date_node = event.find(f'.//{{{self.xip_ns}}}Date')
                result['Date'] = date_node.text if hasattr(date_node, 'text') else None
                user_node = event.find(f'.//{{{self.xip_ns}}}User')
                result['User'] = user_node.text if hasattr(user_node, 'text') else None
                ref_node = event.find(f'.//{{{self.xip_ns}}}Ref')
                result['Ref'] = ref_node.text if hasattr(ref_node, 'text') else None

                workflow_name = event.find(f'.//{{{self.xip_ns}}}WorkflowName')
                if workflow_name is not None:
                    result['WorkflowName'] = workflow_name.text

                workflow_instance_id = event.find(f'.//{{{self.xip_ns}}}WorkflowInstanceId')
                if workflow_instance_id is not None:
                    result['WorkflowInstanceId'] = workflow_instance_id.text

                serialised_command = event.find(f'.//{{{self.xip_ns}}}SerialisedCommand')
                if serialised_command is not None:
                    result['SerialisedCommand'] = serialised_command.text

                result_list.append(result)
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Next')
            total_hits = entity_response.find(f'.//{{{self.entity_ns}}}TotalResults')
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result_list, has_more, int(total_hits.text), url)

        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._all_events_page(maximum, next_page, **kwargs)
        else:
            exception = HTTPException("", request.status_code, request.url,
                                      "_all_events_page", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def _entity_events_page(self, entity: Entity, maximum: int = 25, next_page: str = None) -> PagedSet:
        """
         event actions performed against this entity
        """
        if self.major_version < 7 and self.minor_version < 1:
            logger.error("Entity events is only available when connected to a v6.1 System")
            raise RuntimeError("Entity events is only available when connected to a v6.1 System")

        headers = {HEADER_TOKEN: self.token}
        params = {'start': str(0), 'max': str(maximum)}
        if next_page is None:
            request = self.session.get(
                f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/event-actions',
                params=params, headers=headers)
        else:
            request = self.session.get(next_page, headers=headers)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            event_actions = entity_response.findall(f'.//{{{self.xip_ns}}}EventAction')
            result_list = []
            for event_action in event_actions:
                result = {'commandType': ''}
                if 'commandType' in event_action.attrib:
                    result['commandType'] = event_action.attrib['commandType']

                event = event_action.find(f'.//{{{self.xip_ns}}}Event')
                if 'type' in event_action.attrib:
                    result['eventType'] = event.attrib['type']

                date_node = event.find(f'.//{{{self.xip_ns}}}Date')
                if date_node is not None:
                    result['Date'] = date_node.text

                user_node = event.find(f'.//{{{self.xip_ns}}}User')
                if user_node is not None:
                    result['User'] = user_node.text

                ref_node = event.find(f'.//{{{self.xip_ns}}}Ref')
                if ref_node is not None:
                    result['Ref'] = ref_node.text

                workflow_name = event.find(f'.//{{{self.xip_ns}}}WorkflowName')
                if workflow_name is not None:
                    result['WorkflowName'] = workflow_name.text

                workflow_instance_id = event.find(f'.//{{{self.xip_ns}}}WorkflowInstanceId')
                if workflow_instance_id is not None:
                    result['WorkflowInstanceId'] = workflow_instance_id.text

                serialised_command = event_action.find(f'.//{{{self.xip_ns}}}SerialisedCommand')
                if serialised_command is not None:
                    result['SerialisedCommand'] = serialised_command.text

                result_list.append(result)
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Next')
            total_hits = entity_response.find(f'.//{{{self.entity_ns}}}TotalResults')
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result_list, has_more, int(total_hits.text), url)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._entity_events_page(entity)
        else:
            exception = HTTPException(entity.reference, request.status_code, request.url,
                                      "_all_events_page", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def entity_events(self, entity: Entity) -> Generator:
        self.token = self.__token__()
        paged_set = self._entity_events_page(entity)
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self._entity_events_page(entity, next_page=paged_set.next_page)
            for entity in paged_set.results:
                yield entity

    def updated_entities(self, previous_days: int = 1) -> Generator:
        self.token = self.__token__()
        maximum = 25
        paged_set = self._updated_entities_page(previous_days=previous_days, maximum=maximum, next_page=None)
        for entity in paged_set.results:
            yield entity
        while paged_set.has_more:
            paged_set = self._updated_entities_page(previous_days=previous_days, maximum=maximum,
                                                    next_page=paged_set.next_page)
            for entity in paged_set.results:
                yield entity

    def _updated_entities_page(self, previous_days: int = 1, maximum: int = 50, next_page: str = None) -> PagedSet:
        headers = {HEADER_TOKEN: self.token}
        x = datetime.utcnow() - timedelta(days=previous_days)
        today = x.replace(tzinfo=timezone.utc).isoformat()
        if next_page is None:
            params = {'date': today, 'start': '0', 'max': str(maximum)}
            request = self.session.get(f'{self.protocol}://{self.server}/api/entity/entities/updated-since',
                                       headers=headers, params=params)
        else:
            request = self.session.get(next_page, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            entities = entity_response.findall(f'.//{{{self.entity_ns}}}Entity')
            result = []
            for entity in entities:
                if 'type' in entity.attrib:
                    if entity.attrib['type'] == EntityType.FOLDER.value:
                        folder = Folder(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                        result.append(folder)
                    elif entity.attrib['type'] == EntityType.ASSET.value:
                        asset = Asset(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                        result.append(asset)
                    elif entity.attrib['type'] == EntityType.CONTENT_OBJECT.value:
                        co = ContentObject(entity.attrib['ref'], entity.attrib['title'], None, None, None, None)
                        result.append(co)
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Next')
            total_hits = entity_response.find(f'.//{{{self.entity_ns}}}TotalResults')
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result, has_more, int(total_hits.text), url)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._updated_entities_page(previous_days=previous_days, maximum=maximum,
                                               next_page=next_page)
        else:
            exception = HTTPException(previous_days, request.status_code, request.url,
                                      "_updated_entities_page", request.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def delete_asset(self, asset: Asset, operator_comment: str, supervisor_comment: str):
        """
        Delete an asset from the repository

        :param asset:               The Asset
        :param operator_comment:    The operator comment on the deletion
        :param supervisor_comment:  The supervisor comment on the deletion
        """
        if isinstance(asset, Asset):
            return self._delete_entity(asset, operator_comment, supervisor_comment)
        else:
            raise RuntimeError("delete_asset only deletes assets")

    def delete_folder(self, folder: Folder, operator_comment: str, supervisor_comment: str):
        """
         Delete an asset from the repository


         :param folder:             The Folder
         :param operator_comment:   The operator comment on the deletion
         :param supervisor_comment:  The supervisor comment on the deletion
         """
        if isinstance(folder, Folder):
            return self._delete_entity(folder, operator_comment, supervisor_comment)
        else:
            raise RuntimeError("delete_folder only deletes folders")

    def _delete_entity(self, entity: Entity, operator_comment: str, supervisor_comment: str):
        """
        Delete an asset from the repository


        :param entity:            The entity
        :param operator_comment: The comment on the deletion
        """

        # check manager password is available:
        config = configparser.ConfigParser()
        config.read('credentials.properties', encoding='utf-8')
        try:
            manager_username = config['credentials']['manager.username']
            manager_password = config['credentials']['manager.password']
            self.manager_token(manager_username, manager_password)
        except KeyError:
            raise RuntimeError("No manager password set in credentials.properties")

        self.token = self.__token__()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        xml_object = xml.etree.ElementTree.Element('DeletionAction',
                                                   {"xmlns:xip": self.xip_ns, "xmlns": self.entity_ns})
        submission_el = xml.etree.ElementTree.SubElement(xml_object, "Submission")
        comment_el = xml.etree.ElementTree.SubElement(submission_el, "Comment")
        comment_el.text = operator_comment
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        logger.debug(xml_request)
        request = self.session.delete(f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}',
                                      data=xml_request, headers=headers)
        logger.debug(request.content.decode("utf-8"))
        if request.status_code == requests.codes.accepted:
            progress = request.content.decode("utf-8")
            req = self.session.get(f"{self.protocol}://{self.server}/api/entity/progress/{progress}", headers=headers)
            while True:
                if req.status_code == requests.codes.ok:
                    entity_response = xml.etree.ElementTree.fromstring(req.content.decode("utf-8"))
                    status = entity_response.find(".//{http://status.preservica.com}Status")
                    if hasattr(status, 'text'):
                        if status.text == "COMPLETED":
                            return entity.reference
                        if status.text == "PENDING":
                            headers = {HEADER_TOKEN: self.manager_token(manager_username, manager_password),
                                       'Content-Type': 'application/xml;charset=UTF-8'}
                            xml_object = xml.etree.ElementTree.Element('DeletionAction ', {"xmlns:xip": self.xip_ns,
                                                                                           "xmlns": self.entity_ns})
                            approval_el = xml.etree.ElementTree.SubElement(xml_object, "Approval")
                            xml.etree.ElementTree.SubElement(approval_el, "Approved").text = "true"
                            xml.etree.ElementTree.SubElement(approval_el, "Comment").text = supervisor_comment
                            xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
                            logger.debug(xml_request)
                            approve = self.session.put(
                                f"{self.protocol}://{self.server}/api/entity/actions/deletions/{progress}",
                                data=xml_request, headers=headers)
                            if approve.status_code == requests.codes.accepted:
                                return entity.reference
                            else:
                                logger.error(approve.content.decode('utf-8'))
                                raise RuntimeError(approve.status_code, "delete_asset failed during approval")
                        sleep(2.0)
                req = self.session.get(f"{self.protocol}://{self.server}/api/entity/progress/{progress}",
                                       headers=headers)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._delete_entity(entity, operator_comment, supervisor_comment)
        if request.status_code == requests.codes.unprocessable:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "no active workflow context for full deletion exists in the system")
        if request.status_code == requests.codes.forbidden:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "User doesn't have deletion rights on the "
                                                    "entity or the required operator role to evaluate a deletion")

        exception = HTTPException(entity.reference, request.status_code, request.url,
                                  "_delete_entity", request.content.decode('utf-8'))
        logger.error(exception)
        raise exception
