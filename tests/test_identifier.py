import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_get_entity_by_identifier():
    client = EntityAPI()
    list_of_objects = client.identifier("code", "Amelia Earhart")
    assert len(list_of_objects) == 1
    entity = list_of_objects.pop()
    assert entity.title == "Amelia Earhart"
    assert entity.entity_type is EntityType.FOLDER
    assert entity.reference == FOLDER_ID


def test_add_identifier_folder():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    client.add_identifier(folder, "ISBN", "1234567890")
    entity_set = client.identifier("ISBN", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == folder.reference


def test_add_identifier_asset():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    client.add_identifier(asset, "ARK", "1234567890")
    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == asset.reference
    assert len(client.identifiers_for_entity(asset)) == 1


def test_add_identifier_content_obj():
    client = EntityAPI()
    content_object = client.content_object(CO_ID)
    client.add_identifier(content_object, "CO", "12333")
    entity_set = client.identifier("CO", "12333")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == content_object.reference
    assert len(client.identifiers_for_entity(content_object)) == 1


def test_get_identifier_folder():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    identifiers = client.identifiers_for_entity(folder)
    assert len(identifiers) == 2
    test_pass = False
    for identifier in identifiers:
        if "ISBN" in identifier:
            test_pass = True
            assert identifier[1] == "1234567890"
    assert test_pass


def test_get_identifier_asset():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    identifiers = client.identifiers_for_entity(asset)
    assert len(identifiers) == 1
    test_pass = False
    for identifier in identifiers:
        if "ARK" in identifier:
            test_pass = True
            assert identifier[1] == "1234567890"
    assert test_pass


def test_delete_identifier_folder():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    entity_set = client.identifier("ISBN", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == folder.reference
    client.delete_identifiers(folder, "ISBN", "1234567890")
    entity_set = client.identifier("ISBN", "1234567890")
    assert len(entity_set) == 0
    folder = client.folder(FOLDER_ID)
    identifiers = client.identifiers_for_entity(folder)
    assert len(identifiers) == 1


def test_delete_identifier_asset():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == asset.reference
    client.delete_identifiers(asset, "ARK", "1234567890")
    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 0


def test_delete_identifier_co():
    client = EntityAPI()
    content_object = client.content_object(CO_ID)
    entity_set = client.identifier("CO", "12333")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == content_object.reference
    client.delete_identifiers(content_object, "CO", "12333")
    entity_set = client.identifier("CO", "12333")
    assert len(entity_set) == 0


def test_add_same_id_to_asset_folder():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    folder = client.folder(FOLDER_ID)
    client.add_identifier(asset, "DOI", "123456:98776")
    asset_set = client.identifiers_for_entity(asset)
    assert len(asset_set) == 1
    client.add_identifier(folder, "DOI", "123456:98776")
    folder_set = client.identifiers_for_entity(folder)
    assert len(folder_set) == 2
    entity_set = client.identifier("DOI", "123456:98776")
    assert len(entity_set) == 2
    client.delete_identifiers(asset, "DOI", "123456:98776")
    client.delete_identifiers(folder, "DOI", "123456:98776")
    entity_set = client.identifier("DOI", "123456:98776")
    assert len(entity_set) == 0
