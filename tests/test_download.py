import os
import uuid

import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_can_download_bistream():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    representations = client.representations(asset)
    assert len(representations) == 1
    representation = representations.pop()
    assert representation.name == "Preservation-1"
    assert representation.rep_type == "Preservation"
    content_objects = client.content_objects(representation)
    assert len(content_objects) == 1
    content_object = content_objects[0]
    assert content_object.asset.reference == ASSET_ID
    assert content_object.representation_type == representation.rep_type
    assert content_object.title == "LC-USZ62-20901"
    generations = client.generations(content_object)
    assert len(generations) == 1
    generation = generations[0]
    assert generation.content_object.asset.reference == ASSET_ID
    assert generation.format_group == "tiff"
    assert generation.active
    assert generation.original
    assert len(generation.bitstreams) == 1
    bitstream = generation.bitstreams[0]
    assert bitstream.filename == "LC-USZ62-20901.tiff"
    client.bitstream_content(bitstream, bitstream.filename)
    assert os.path.isfile(bitstream.filename)
    assert os.stat(bitstream.filename).st_size == bitstream.length
    os.remove(bitstream.filename)


def test_can_download_file():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    filename = str(uuid.uuid4())
    f = client.download(asset, filename)
    assert f == filename
    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 1790114
    os.remove(filename)


def test_can_download_file2():
    client = EntityAPI()
    asset = client.asset("799b467f-050d-415f-b8ec-7c74b343f628")
    filename = str(uuid.uuid4())
    f = client.download(asset, filename)
    assert f == filename
    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 1864130
    os.remove(filename)


def test_can_download_file3():
    client = EntityAPI()
    folder = client.folder("ebd977f6-bebd-4ecf-99be-e054989f9af4")
    filename = str(uuid.uuid4())
    with pytest.raises(HTTPException):
        f = client.download(folder, filename)


def test_can_get_small_thumbnail():
    client = EntityAPI()
    asset = client.asset("799b467f-050d-415f-b8ec-7c74b343f628")
    filename = str(uuid.uuid4()) + ".jpg"
    f = client.thumbnail(asset, filename, Thumbnail.SMALL)
    assert f == filename
    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 6426
    os.remove(filename)


def test_can_get_med_thumbnail():
    client = EntityAPI()
    asset = client.asset("799b467f-050d-415f-b8ec-7c74b343f628")
    filename = str(uuid.uuid4()) + ".jpg"
    f = client.thumbnail(asset, filename, Thumbnail.MEDIUM)
    assert f == filename
    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 27585
    os.remove(filename)


def test_can_get_large_thumbnail():
    client = EntityAPI()
    asset = client.asset("799b467f-050d-415f-b8ec-7c74b343f628")
    filename = str(uuid.uuid4()) + ".jpg"
    f = client.thumbnail(asset, filename, Thumbnail.LARGE)
    assert f == filename
    assert os.path.isfile(filename)
    assert os.stat(filename).st_size == 129192
    os.remove(filename)
