from pathlib import Path

import pytest
from pyPreservica import *

ASSET_ID = "b14848b5-4c4d-4d8a-b394-3b764069ee93"


def test_get_representations():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    assert asset is not None
    representations = client.representations(asset)
    assert len(representations) == 2
    preservation_representations = list(filter(lambda x: x.rep_type == "Preservation", representations))
    assert len(preservation_representations) == 1
    representation = preservation_representations.pop()
    assert representation.asset.title == asset.title
    assert representation.rep_type == "Preservation"
    assert representation.name == "Preservation-1"


def test_get_generations():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    assert asset is not None
    representations = client.representations(asset)
    assert len(representations) == 2
    preservation_representations = list(filter(lambda x: x.rep_type == "Preservation", representations))
    assert len(preservation_representations) == 1
    representation = preservation_representations.pop()
    assert representation.asset.title == asset.title
    assert representation.rep_type == "Preservation"
    assert representation.name == "Preservation-1"
    content_objects = client.content_objects(representation)
    assert len(content_objects) == 1
    content_object = content_objects[0]
    assert content_object.asset == asset
    generations = client.generations(content_object)
    assert len(generations) == 1
    generation = generations[0]
    assert generation.active is True
    assert generation.original is True
    assert generation.format_group == "tiff"
    access_representations = list(filter(lambda x: x.rep_type == "Access", representations))
    assert len(access_representations) == 1
    representation = access_representations.pop()
    assert representation.asset.title == asset.title
    assert representation.rep_type == "Access"
    assert representation.name == "Access Copy"
    content_objects = client.content_objects(representation)
    assert len(content_objects) == 1
    content_object = content_objects[0]
    assert content_object.asset == asset
    generations = client.generations(content_object)
    assert len(generations) == 1
    generation = generations[0]
    assert generation.active is True
    assert generation.original is False
    assert generation.format_group == "jpeg"




def test_get_bitstream_content():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    preservation_representations = list(filter(lambda x: x.rep_type == "Preservation", client.representations(asset)))
    preservation_content_objects = client.content_objects(preservation_representations.pop())
    generation = client.generations(preservation_content_objects[0])[0]
    assert generation.format_group == "tiff"
    assert len(generation.bitstreams) == 1
    bitstream = generation.bitstreams[0]
    assert bitstream.filename == "LC-USZ62-51820.tiff"
    assert bitstream.length == 1942466
    client.bitstream_content(bitstream, bitstream.filename)
    assert os.path.isfile(bitstream.filename) is True
    assert Path(bitstream.filename).stat().st_size == 1942466
    os.remove(bitstream.filename)
