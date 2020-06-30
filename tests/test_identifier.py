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



