import pytest
from pyPreservica import *


def test_add_identifier_folder():
    client = EntityAPI()
    folder = client.folder("874779c9-7fa2-450f-b351-e4606368fb67")
    client.add_identifier(folder, "ISBN", "1234567890")
    entity_set = client.identifier("ISBN", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == folder.reference


def test_add_identifier_asset():
    client = EntityAPI()
    asset = client.asset("4006c85a-0e1d-4ec5-ab99-5025c3f22f0b")
    client.add_identifier(asset, "ARK", "1234567890")
    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == asset.reference


def test_get_identifier_folder():
    client = EntityAPI()
    folder = client.folder("874779c9-7fa2-450f-b351-e4606368fb67")
    identifiers = client.identifiers_for_entity(folder)
    assert len(identifiers) == 3
    test_pass = False
    for identifier in identifiers:
        if "ISBN" in identifier:
            test_pass = True
            assert identifier[1] == "1234567890"
    assert test_pass


def test_get_identifier_asset():
    client = EntityAPI()
    asset = client.asset("4006c85a-0e1d-4ec5-ab99-5025c3f22f0b")
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
    folder = client.folder("874779c9-7fa2-450f-b351-e4606368fb67")
    entity_set = client.identifier("ISBN", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == folder.reference
    client.delete_identifiers(folder, "ISBN", "1234567890")
    entity_set = client.identifier("ISBN", "1234567890")
    assert len(entity_set) == 0


def test_delete_identifier_asset():
    client = EntityAPI()
    asset = client.asset("4006c85a-0e1d-4ec5-ab99-5025c3f22f0b")
    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 1
    entity = entity_set.pop()
    assert entity.reference == asset.reference
    client.delete_identifiers(asset, "ARK", "1234567890")
    entity_set = client.identifier("ARK", "1234567890")
    assert len(entity_set) == 0
