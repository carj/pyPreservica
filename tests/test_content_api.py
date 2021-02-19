import pytest

from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_get_asset_details():
    client = ContentAPI()
    json_dict = client.object_details(EntityType.ASSET, ASSET_ID)
    assert json_dict is not None
    assert json_dict['id'] == 'sdb:IO|683f9db7-ff81-4859-9c03-f68cfa5d9c3d'
    assert json_dict['name'] == 'LC-USZ62-20901'


def test_download_asset():
    client = ContentAPI()
    filename = client.download(ASSET_ID, "filename.img")
    assert os.path.exists(filename)
    os.remove(filename)


def test_download_folder():
    client = ContentAPI()
    with pytest.raises(RuntimeError):
        filename = client.download(FOLDER_ID, "filename.img")


def test_get_thumbnail_small():
    client = ContentAPI()
    small = client.thumbnail("IO", ASSET_ID, "filename.img", Thumbnail.SMALL)
    assert os.path.exists(small)
    os.remove(small)


def test_get_thumbnail_med():
    client = ContentAPI()
    med = client.thumbnail("IO", ASSET_ID, "filename.img", Thumbnail.MEDIUM)
    assert os.path.exists(med)
    os.remove(med)


def test_get_thumbnail_large():
    client = ContentAPI()
    large = client.thumbnail("IO", ASSET_ID, "filename.img", Thumbnail.LARGE)
    assert os.path.exists(large)
    os.remove(large)


def test_get_indexed_fields():
    client = ContentAPI()
    fields = client.indexed_fields()
    assert fields is not None
    assert 'xip.title' in fields
    assert 'xip.description' in fields


def test_simple_search_list():
    client = ContentAPI()
    results = list(client.simple_search_list(query="pyPreservica"))
    assert len(results) == 1
    assert results.pop()['xip.reference'] == '9fd239eb-19a3-4a46-9495-40fd9a5d8f93'



