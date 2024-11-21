import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def delete_identifiers():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    for i in client.identifiers_for_entity(folder):
        client.delete_identifiers(folder, i[0], i[1])

    asset = client.asset(ASSET_ID)
    for i in client.identifiers_for_entity(asset):
        client.delete_identifiers(asset, i[0], i[1])

    co = client.content_object(CO_ID)
    for i in client.identifiers_for_entity(co):
        client.delete_identifiers(co, i[0], i[1])


@pytest.fixture
def setup_data():
    print("\nSetting up resources...")

    client = EntityAPI()
    folder = client.folder(FOLDER_ID)

    delete_identifiers()

    client.add_identifier(folder, "code", "Amelia Earhart")

    yield

    print("\nTearing down resources...")

    delete_identifiers()


def test_get_entity_by_identifier(setup_data):
    client = EntityAPI()
    list_of_objects = client.identifier("code", "Amelia Earhart")
    assert len(list_of_objects) == 1
    entity = list_of_objects.pop()
    assert entity.title == "Amelia Earhart"
    assert entity.entity_type is EntityType.FOLDER
    assert entity.reference == FOLDER_ID


def test_add_identifier_folder(setup_data):
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    client.add_identifier(folder, "ISBN", "1234567890")
    entity_set = client.identifier("ISBN", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == folder.reference


def test_add_identifier_asset(setup_data):
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    client.add_identifier(asset, "ARK", "1234567890")
    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == asset.reference
    assert len(client.identifiers_for_entity(asset)) == 1


def test_add_identifier_content_obj(setup_data):
    client = EntityAPI()
    content_object = client.content_object(CO_ID)
    client.add_identifier(content_object, "CO", "12333")
    entity_set = client.identifier("CO", "12333")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == content_object.reference
    assert len(client.identifiers_for_entity(content_object)) == 1


def test_get_identifier_folder(setup_data):
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)

    client.add_identifier(folder, "ISBN", "1234567890")
    client.add_identifier(folder, "ARK", "1234567890")

    identifiers = client.identifiers_for_entity(folder)
    assert len(identifiers) == 3
    test_pass = False
    for identifier in identifiers:
        if "ISBN" in identifier:
            test_pass = True
            assert identifier[1] == "1234567890"
    assert test_pass


def test_get_identifier_asset(setup_data):
    client = EntityAPI()
    asset = client.asset(ASSET_ID)

    client.add_identifier(asset, "ARK", "1234567890")

    identifiers = client.identifiers_for_entity(asset)
    assert len(identifiers) == 1
    test_pass = False
    for identifier in identifiers:
        if "ARK" in identifier:
            test_pass = True
            assert identifier[1] == "1234567890"
    assert test_pass


def test_delete_identifier_folder(setup_data):
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)

    client.add_identifier(folder, "ISBN", "1234567890")

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


def test_delete_identifier_asset(setup_data):
    client = EntityAPI()
    asset = client.asset(ASSET_ID)

    client.add_identifier(asset, "ARK", "1234567890")

    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == asset.reference
    client.delete_identifiers(asset, "ARK", "1234567890")
    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 0


def test_delete_identifier_co(setup_data):
    client = EntityAPI()
    content_object = client.content_object(CO_ID)

    client.add_identifier(content_object, "CO", "12333")

    entity_set = client.identifier("CO", "12333")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == content_object.reference
    client.delete_identifiers(content_object, "CO", "12333")
    entity_set = client.identifier("CO", "12333")
    assert len(entity_set) == 0


def test_add_same_id_to_asset_folder(setup_data):
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


def test_can_update_identifier(setup_data):
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    client.add_identifier(folder, "ISBN", "ISBN_0001")
    entity_set = client.identifier("ISBN", "ISBN_0001")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == folder.reference
    client.update_identifiers(folder, "ISBN", "ISBN_0002")
    entity_set = client.identifier("ISBN", "ISBN_0002")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == folder.reference
    client.delete_identifiers(folder, "ISBN", "ISBN_0002")
