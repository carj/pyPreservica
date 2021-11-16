from pyPreservica import *

ASSET_ID = "b14848b5-4c4d-4d8a-b394-3b764069ee93"


def test_get_entity_events():
    i = 0
    client = EntityAPI()
    for e in client.entity_events(client.asset(ASSET_ID)):
        assert e is not None
        assert e['Date'] is not None
        assert e['User'] is not None
        i = i + 1
        if i > 100:
            return


def test_get_all_events():
    i = 0
    client = EntityAPI()
    for e in client.all_events():
        assert e is not None
        assert e['Date'] is not None
        assert e['Ref'] is not None
        i = i + 1
        if i > 100:
            return


def test_get_bitstream_checks():
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

    checks = list(client.integrity_checks(bitstream))
    assert len(checks) > 3
