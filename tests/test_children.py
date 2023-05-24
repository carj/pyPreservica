import xml

import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_get_root_folders():
    client = EntityAPI()
    paged_set = client.children(None)
    assert paged_set.total > 0
    objs = set()
    for f in paged_set.results:
        assert f.entity_type == EntityType.FOLDER
        assert f.parent is None
        objs.add(f)
    assert len(objs) == paged_set.total


def test_get_root_folders_descendants():
    client = EntityAPI()
    for f in client.descendants(None):
        assert f.entity_type == EntityType.FOLDER
        assert f.parent is None


def test_get_root_folder1():
    client = EntityAPI()
    paged_set = client.children()
    assert paged_set.total > 0
    objs = set()
    for f in paged_set.results:
        assert f.entity_type == EntityType.FOLDER
        assert f.parent is None
        objs.add(f)
    assert len(objs) == paged_set.total


def test_get_root_folders_paged():
    client = EntityAPI()
    objs = set()
    url = None
    while True:
        paged_set = client.children(None, maximum=3, next_page=url)
        assert paged_set.total > 0
        for f in paged_set.results:
            assert f.entity_type == EntityType.FOLDER
            assert f.parent is None
            objs.add(f)
        url = paged_set.next_page
        if url is None:
            break
    assert len(objs) == paged_set.total


def test_get_children_of_folder():
    client = EntityAPI()
    paged_set = client.children(FOLDER_ID)
    assert paged_set.total == 171
    for f in paged_set.results:
        assert f.entity_type == EntityType.ASSET
        assert f.parent == FOLDER_ID


def test_get_children_of_folder_descendants():
    client = EntityAPI()
    objs = set()
    for f in client.descendants(FOLDER_ID):
        assert f.entity_type == EntityType.ASSET
        assert f.parent == FOLDER_ID
        objs.add(f)
    assert len(objs) == 171
