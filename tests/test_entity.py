import pytest
from pyPreservica import *


def test_get_folder():
    client = EntityAPI()
    folder = client.folder("874779c9-7fa2-450f-b351-e4606368fb67")
    assert folder is not None
    assert folder.title == "folder_title"
    assert folder.description == "folder_description"
    assert folder.entity_type is EntityType.FOLDER
    assert folder.parent == "ae78a872-50a3-4c5e-b03f-c58c4a0f3e3d"
    assert folder.security_tag == "open"
    assert folder.reference == "874779c9-7fa2-450f-b351-e4606368fb67"


def test_get_asset():
    client = EntityAPI()
    asset = client.asset("34a2e8b1-8200-4736-b5e6-965bf7fa4a1f")
    assert asset is not None
    assert asset.title == "First Flight"
    assert asset.description is None
    assert asset.entity_type is EntityType.ASSET
    assert asset.parent == "de70d2f5-85fa-4b45-9c3b-580e10dba17d"
    assert asset.security_tag == "open"
    assert asset.reference == "34a2e8b1-8200-4736-b5e6-965bf7fa4a1f"


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
    entity = client.entity(EntityType.FOLDER, "874779c9-7fa2-450f-b351-e4606368fb67")
    assert entity is not None
    assert entity.title == "folder_title"
    assert entity.description == "folder_description"
    assert entity.entity_type is EntityType.FOLDER
    assert entity.parent == "ae78a872-50a3-4c5e-b03f-c58c4a0f3e3d"
    assert entity.security_tag == "open"
    assert entity.reference == "874779c9-7fa2-450f-b351-e4606368fb67"


def test_get_asset_as_entity():
    client = EntityAPI()
    asset = client.entity(EntityType.ASSET, "34a2e8b1-8200-4736-b5e6-965bf7fa4a1f")
    assert asset is not None
    assert asset.title == "First Flight"
    assert asset.description is None
    assert asset.entity_type is EntityType.ASSET
    assert asset.parent == "de70d2f5-85fa-4b45-9c3b-580e10dba17d"
    assert asset.security_tag == "open"
    assert asset.reference == "34a2e8b1-8200-4736-b5e6-965bf7fa4a1f"


def test_get_folder_metadata():
    client = EntityAPI()
    entity = client.entity(EntityType.FOLDER, "874779c9-7fa2-450f-b351-e4606368fb67")
    xml_string = client.metadata_for_entity(entity, "http://www.openarchives.org/OAI/2.0/oai_dc/")
    assert xml_string is not None


def test_get_folder_by_identifier():
    client = EntityAPI()
    list_of_objects = client.identifier("Ref", "874779c9-7fa2-450f-b351-e4606368fb67")
    assert len(list_of_objects) == 1
    entity = list_of_objects.pop()
    assert entity.title == "folder_title"
    assert entity.entity_type is EntityType.FOLDER
    assert entity.reference == "874779c9-7fa2-450f-b351-e4606368fb67"


def test_save_folder_name():
    client = EntityAPI()
    folder = client.folder("874779c9-7fa2-450f-b351-e4606368fb67")
    assert folder is not None
    assert folder.title == "folder_title"
    folder.title = "new title"
    f = client.save(folder)
    assert f.title == "new title"
    folder = client.folder("874779c9-7fa2-450f-b351-e4606368fb67")
    assert folder.title == "new title"
    folder.title = "folder_title"
    client.save(folder)


def test_save_folder_description():
    client = EntityAPI()
    folder = client.folder("874779c9-7fa2-450f-b351-e4606368fb67")
    assert folder is not None
    assert folder.description == "folder_description"
    folder.description = "new description"
    f = client.save(folder)
    assert f.description == "new description"
    folder = client.folder("874779c9-7fa2-450f-b351-e4606368fb67")
    assert folder.description == "new description"
    folder.description = "folder_description"
    client.save(folder)


def test_save_asset_name():
    client = EntityAPI()
    asset = client.asset("34a2e8b1-8200-4736-b5e6-965bf7fa4a1f")
    assert asset is not None
    assert asset.title == "First Flight"
    asset.title = "First Flight Image"
    a = client.save(asset)
    assert a.title == "First Flight Image"
    asset = client.asset("34a2e8b1-8200-4736-b5e6-965bf7fa4a1f")
    assert asset.title == "First Flight Image"
    asset.title = "First Flight"
    client.save(asset)


def test_save_asset_description():
    client = EntityAPI()
    asset = client.asset("34a2e8b1-8200-4736-b5e6-965bf7fa4a1f")
    assert asset is not None
    assert asset.description is None
    asset.description = "First Flight Description"
    a = client.save(asset)
    assert a.description == "First Flight Description"
    asset = client.asset("34a2e8b1-8200-4736-b5e6-965bf7fa4a1f")
    assert asset.description == "First Flight Description"
    asset.description = None
    asset = client.save(asset)
    assert asset.description is None
