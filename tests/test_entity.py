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


def test_get_folder_raises_error1():
    client = EntityAPI()
    with pytest.raises(RuntimeError):
        folder = client.folder("bla")


def test_get_folder_raises_error2():
    client = EntityAPI()
    with pytest.raises(RuntimeError):
        folder = client.folder(None)


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


