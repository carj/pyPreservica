import os
import uuid
import xml
import xml.etree.ElementTree
from xml.etree import ElementTree

import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID =  "0f2997f7-728c-4e55-9f92-381ed1260d70"

XML_DOCUMENT = """
               <person:Person  xmlns:person="https://www.person.com/person">
                   <person:Name>Name</person:Name>
                   <person:Phone>01234 100 100</person:Phone>
                   <person:Email>test@test.com</person:Email>
                   <person:Address>Abingdon, UK</person:Address>
               </person:Person>
"""

XML_DOCUMENT_NO_PREFIX = """
               <Person xmlns="https://www.person.com/person">
                   <Name>Name</Name>
                   <Phone>01234 100 100</Phone>
                   <Email>test@test.com</Email>
                   <Address>Abingdon, UK</Address>
               </Person>
"""


def test_get_folder_metadata():
    client = EntityAPI()
    entity = client.entity(EntityType.FOLDER, FOLDER_ID)
    xml_string = client.metadata_for_entity(entity, "http://purl.org/dc/elements/1.1/")
    assert xml_string is not None
    document = xml.etree.ElementTree.fromstring(xml_string)
    identifier = document.find(".//{http://purl.org/dc/elements/1.1/}identifier")
    assert identifier.text == "LC-USZ62-43601"


def test_update_folder_metadata():
    client = EntityAPI()
    entity = client.entity(EntityType.FOLDER, FOLDER_ID)
    xml_string = client.metadata_for_entity(entity, "http://purl.org/dc/elements/1.1/")
    assert xml_string is not None
    document = xml.etree.ElementTree.fromstring(xml_string)
    identifier = document.find(".//{http://purl.org/dc/elements/1.1/}identifier")
    assert identifier.text == "LC-USZ62-43601"
    description = document.find(".//{http://purl.org/dc/elements/1.1/}description")
    assert description.text == "a"
    description.text = "description"
    xml_string = ElementTree.tostring(document, encoding='utf-8').decode("utf-8")
    folder = client.update_metadata(entity, "http://purl.org/dc/elements/1.1/", xml_string)
    document = xml.etree.ElementTree.fromstring(client.metadata_for_entity(folder, "http://purl.org/dc/elements/1.1/"))
    description = document.find(".//{http://purl.org/dc/elements/1.1/}description")
    assert description.text == "description"
    description.text = "a"
    xml_string = ElementTree.tostring(document, encoding='utf-8').decode("utf-8")
    folder = client.update_metadata(entity, "http://purl.org/dc/elements/1.1/", xml_string)


def test_add_folder_metadata_no_prefix():
    client = EntityAPI()
    entity = client.entity(EntityType.FOLDER, FOLDER_ID)
    folder = client.add_metadata(entity, "https://www.person.com/person", XML_DOCUMENT_NO_PREFIX)

def test_add_folder_metadata_with_ns():
    client = EntityAPI()
    entity = client.entity(EntityType.FOLDER, FOLDER_ID)
    folder = client.add_metadata(entity, "https://www.person.com/person", XML_DOCUMENT)

def test_add_asset_metadata_no_prefix():
    client = EntityAPI()
    entity = client.entity(EntityType.ASSET, ASSET_ID)
    folder = client.add_metadata(entity, "https://www.person.com/person", XML_DOCUMENT_NO_PREFIX)

def test_add_asset_metadata_with_ns():
    client = EntityAPI()
    entity = client.entity(EntityType.ASSET, ASSET_ID)
    folder = client.add_metadata(entity, "https://www.person.com/person", XML_DOCUMENT)



def test_add_folder_metadata_string():
    client = EntityAPI()
    entity = client.entity(EntityType.FOLDER, FOLDER_ID)
    assert len(entity.metadata) == 3
    folder = client.add_metadata(entity, "https://www.person.com/person", XML_DOCUMENT)
    assert len(folder.metadata) == 4
    xml_string = client.metadata_for_entity(folder, "https://www.person.com/person")
    document = xml.etree.ElementTree.fromstring(xml_string)
    name = document.find(".//{https://www.person.com/person}Name")
    assert name.text == "Name"
    folder = client.delete_metadata(folder, "https://www.person.com/person")
    assert len(folder.metadata) == 3


def test_get_asset_metadata():
    client = EntityAPI()
    entity = client.entity(EntityType.ASSET, ASSET_ID)
    xml_string = client.metadata_for_entity(entity, "http://purl.org/dc/elements/1.1/")
    assert xml_string is not None
    document = xml.etree.ElementTree.fromstring(xml_string)
    filename = document.find(".//{http://purl.org/dc/elements/1.1/}filename")
    assert filename.text == "LC-USZ62-20901.tiff"


def test_get_all_asset_metadata():
    client = EntityAPI()
    entity = client.entity(EntityType.ASSET, ASSET_ID)
    for m in client.all_metadata(entity):
        assert m[0] is not None
        document = xml.etree.ElementTree.fromstring(m[1])
        assert document is not None


def test_get_co_metadata():
    client = EntityAPI()
    entity_object = client.entity(EntityType.CONTENT_OBJECT, CO_ID)
    entity = client.delete_metadata(entity_object, "https://www.person.com/person")
    xml_string = client.metadata_for_entity(entity, "https://www.person.com/person")
    assert xml_string is None
    co = client.add_metadata(entity, "https://www.person.com/person", XML_DOCUMENT)
    xml_string = client.metadata_for_entity(co, "https://www.person.com/person")
    document = xml.etree.ElementTree.fromstring(xml_string)
    name = document.find(".//{https://www.person.com/person}Name")
    assert name.text == "Name"
    e = client.delete_metadata(co, "https://www.person.com/person")
    xml_string = client.metadata_for_entity(e, "https://www.person.com/person")
    assert xml_string is None


def test_get_folder_metadata_file():
    client = EntityAPI()
    entity = client.entity(EntityType.FOLDER, FOLDER_ID)
    assert len(entity.metadata) == 3
    filename = str(uuid.uuid4()) + ".xml"
    fd = open(filename, "wt", encoding="utf-8")
    fd.write(XML_DOCUMENT)
    fd.flush()
    fd.close()
    with open(filename, "rt", encoding="utf-8") as file:
        folder = client.add_metadata(entity, "https://www.person.com/person", file)
    assert len(folder.metadata) == 4
    xml_string = client.metadata_for_entity(folder, "https://www.person.com/person")
    document = xml.etree.ElementTree.fromstring(xml_string)
    name = document.find(".//{https://www.person.com/person}Name")
    assert name.text == "Name"
    folder = client.delete_metadata(folder, "https://www.person.com/person")
    assert len(folder.metadata) == 3
    os.remove(filename)


def test_get_asset_metadata_file():
    client = EntityAPI()
    entity = client.entity(EntityType.ASSET, ASSET_ID)
    assert len(entity.metadata) == 2
    filename = str(uuid.uuid4()) + ".xml"
    fd = open(filename, "wt", encoding="utf-8")
    fd.write(XML_DOCUMENT)
    fd.flush()
    fd.close()
    with open(filename, "rt", encoding="utf-8") as file:
        asset = client.add_metadata(entity, "https://www.person.com/person", file)
    assert len(asset.metadata) == 3
    xml_string = client.metadata_for_entity(asset, "https://www.person.com/person")
    document = xml.etree.ElementTree.fromstring(xml_string)
    name = document.find(".//{https://www.person.com/person}Name")
    assert name.text == "Name"
    asset = client.delete_metadata(asset, "https://www.person.com/person")
    assert len(asset.metadata) == 2
    os.remove(filename)
