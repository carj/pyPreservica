import xml

import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_get_folder():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    assert folder is not None
    assert folder.title == "Amelia Earhart"
    assert folder.description == "Amelia Earhart"
    assert folder.entity_type is EntityType.FOLDER
    assert folder.parent == "9fd239eb-19a3-4a46-9495-40fd9a5d8f93"
    assert folder.security_tag == "open"
    assert folder.reference == FOLDER_ID


def test_get_asset():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    assert asset is not None
    assert asset.title == "LC-USZ62-20901"
    assert asset.description is None
    assert asset.entity_type is EntityType.ASSET
    assert asset.parent == FOLDER_ID
    assert asset.security_tag == "open"
    assert asset.reference == ASSET_ID


def test_get_co():
    client = EntityAPI()
    content_object = client.content_object(CO_ID)
    assert content_object is not None
    assert content_object.reference == CO_ID
    assert content_object.title == "LC-USZ62-20901"
    assert content_object.description == "LC-USZ62-20901"
    assert content_object.entity_type is EntityType.CONTENT_OBJECT
    assert content_object.parent == ASSET_ID


def test_get_co_raises_error1():
    client = EntityAPI()
    with pytest.raises(RuntimeError):
        folder = client.content_object("bla")


def test_get_asset_raises_error1():
    client = EntityAPI()
    with pytest.raises(RuntimeError):
        folder = client.asset("bla")


def test_get_folder_raises_error1():
    client = EntityAPI()
    with pytest.raises(RuntimeError):
        folder = client.folder("bla")


def test_get_folder_raises_error2():
    client = EntityAPI()
    with pytest.raises(RuntimeError):
        folder = client.folder(None)


def test_get_asset_raises_error2():
    client = EntityAPI()
    with pytest.raises(RuntimeError):
        folder = client.asset(None)


def test_get_folder_as_entity():
    client = EntityAPI()
    entity = client.entity(EntityType.FOLDER, FOLDER_ID)
    assert entity is not None
    assert entity.title == "Amelia Earhart"
    assert entity.description == "Amelia Earhart"
    assert entity.entity_type is EntityType.FOLDER
    assert entity.parent == "9fd239eb-19a3-4a46-9495-40fd9a5d8f93"
    assert entity.security_tag == "open"
    assert entity.reference == FOLDER_ID


def test_get_asset_as_entity():
    client = EntityAPI()
    asset = client.entity(EntityType.ASSET, ASSET_ID)
    assert asset is not None
    assert asset.title == "LC-USZ62-20901"
    assert asset.description is None
    assert asset.entity_type is EntityType.ASSET
    assert asset.parent == FOLDER_ID
    assert asset.security_tag == "open"
    assert asset.reference == ASSET_ID


def test_get_co_as_entity():
    client = EntityAPI()
    content_object = client.entity(EntityType.CONTENT_OBJECT, CO_ID)
    assert content_object is not None
    assert content_object.reference == CO_ID
    assert content_object.title == "LC-USZ62-20901"
    assert content_object.description == "LC-USZ62-20901"
    assert content_object.entity_type is EntityType.CONTENT_OBJECT
    assert content_object.parent == ASSET_ID


def test_save_folder_name():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    assert folder is not None
    assert folder.title == "Amelia Earhart"
    folder.title = "NEW TITLE"
    f = client.save(folder)
    assert f.title == "NEW TITLE"
    folder = client.folder(FOLDER_ID)
    assert folder.title == "NEW TITLE"
    folder.title = "Amelia Earhart"
    client.save(folder)


def test_save_folder_description():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    assert folder is not None
    assert folder.description == "Amelia Earhart"
    folder.description = "NEW TITLE"
    f = client.save(folder)
    assert f.description == "NEW TITLE"
    folder = client.folder(FOLDER_ID)
    assert folder.description == "NEW TITLE"
    folder.description = "Amelia Earhart"
    client.save(folder)


def test_save_asset_name():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    assert asset is not None
    assert asset.title == "LC-USZ62-20901"
    asset.title = "NEW TITLE"
    a = client.save(asset)
    assert a.title == "NEW TITLE"
    asset = client.asset(ASSET_ID)
    assert asset.title == "NEW TITLE"
    asset.title = "LC-USZ62-20901"
    client.save(asset)


def test_save_asset_description():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    assert asset is not None
    assert asset.description is None
    asset.description = "NEW TITLE"
    a = client.save(asset)
    assert a.description == "NEW TITLE"
    asset = client.asset(ASSET_ID)
    assert asset.description == "NEW TITLE"
    asset.description = None
    client.save(asset)


def test_save_co_name():
    client = EntityAPI()
    content_object = client.content_object(CO_ID)
    assert content_object is not None
    assert content_object.title == "LC-USZ62-20901"
    content_object.title = "NEW TITLE"
    a = client.save(content_object)
    assert a.title == "NEW TITLE"
    content_object = client.content_object(CO_ID)
    assert content_object.title == "NEW TITLE"
    content_object.title = "LC-USZ62-20901"
    client.save(content_object)


def test_save_co_description():
    client = EntityAPI()
    content_object = client.content_object(CO_ID)
    assert content_object is not None
    assert content_object.description == "LC-USZ62-20901"
    content_object.description = "NEW TITLE"
    a = client.save(content_object)
    assert a.description == "NEW TITLE"
    content_object = client.content_object(CO_ID)
    assert content_object.description == "NEW TITLE"
    content_object.description = "LC-USZ62-20901"
    content_object = client.save(content_object)
    assert content_object.description == "LC-USZ62-20901"


def test_move_entity_to_root():
    client = EntityAPI()
    asset = client.asset("c365634e-9fcc-4ea1-b47f-077f55df9d64")
    folder = client.folder(FOLDER_ID)
    assert asset.parent == folder.reference
    assert asset.title == "LC-USZ62-79099"

    new_folder = client.folder("9fd239eb-19a3-4a46-9495-40fd9a5d8f93")
    asset = client.move(asset, new_folder)
    assert asset.parent == new_folder.reference

    asset = client.move(asset, folder)
    assert asset.parent == folder.reference


def change_security_tag():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    assert asset.security_tag == "open"
    client.security_tag_sync(asset, "closed")

    asset = client.asset(ASSET_ID)
    assert asset.security_tag == "closed"

    client.security_tag_sync(asset, "open")
    asset = client.asset(ASSET_ID)
    assert asset.security_tag == "open"

