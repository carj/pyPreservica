import csv
import os
import tempfile
from time import sleep

import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"
MOVE_ASSET_ID = "05e2750d-bd68-41a0-af25-31cb3498cc2d"
DEST_FOLDER_ID = "9fd239eb-19a3-4a46-9495-40fd9a5d8f93"
TEST_SCHEMA = "http://www.example.com/test-schema"


# --- has_thumbnail ---

def test_has_thumbnail_asset():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    result = client.has_thumbnail(asset)
    assert isinstance(result, bool)
    assert result is True


def test_has_thumbnail_folder():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    result = client.has_thumbnail(folder)
    assert isinstance(result, bool)
    assert result is True


# --- bitstream_chunks ---

def test_bitstream_chunks():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    representation = list(client.representations(asset))[0]
    content_object = client.content_objects(representation)[0]
    generation = client.generations(content_object)[0]
    bitstream = generation.bitstreams[0]
    chunks = list(client.bitstream_chunks(bitstream))
    assert len(chunks) > 0
    assert sum(len(c) for c in chunks) == bitstream.length


def test_bitstream_chunks_invalid_argument():
    client = EntityAPI()
    with pytest.raises(RuntimeError):
        list(client.bitstream_chunks("not_a_bitstream"))


# --- security_tag_async ---

def test_security_tag_async():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    assert asset.security_tag == "open"
    pid = client.security_tag_async(asset, "closed")
    assert pid is not None and len(pid) > 0
    result = client.get_progress(pid)
    while result != AsyncProgress.COMPLETED:
        sleep(0.5)
        result = client.get_progress(pid)
    asset = client.asset(ASSET_ID)
    assert asset.security_tag == "closed"

    client.security_tag_sync(asset, "open")
    asset = client.asset(ASSET_ID)
    assert asset.security_tag == "open"


# --- get_progress ---

def test_get_progress():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    pid = client.security_tag_async(asset, "closed")
    progress = client.get_progress(pid)
    while progress != AsyncProgress.COMPLETED:
        sleep(0.5)
        progress = client.get_progress(pid)
    assert isinstance(progress, AsyncProgress)
    client.security_tag_sync(asset, "open")


# --- move_async / move_sync ---

def _wait_for_pid(client, pid, timeout=30):
    elapsed = 0
    while elapsed < timeout:
        status = client.get_async_progress(pid)
        if status != "ACTIVE":
            return status
        sleep(1)
        elapsed += 1
    return "TIMEOUT"


def test_move_async():
    client = EntityAPI()
    asset = client.asset(MOVE_ASSET_ID)
    assert asset.parent == FOLDER_ID

    dest_folder = client.folder(DEST_FOLDER_ID)
    pid = client.move_async(asset, dest_folder)
    assert pid is not None and len(pid) > 0

    _wait_for_pid(client, pid.strip())
    client.move_sync(asset, client.folder(FOLDER_ID))
    assert client.asset(MOVE_ASSET_ID).parent == FOLDER_ID


def test_move_sync():
    client = EntityAPI()
    asset = client.asset(MOVE_ASSET_ID)
    assert asset.parent == FOLDER_ID

    dest_folder = client.folder(DEST_FOLDER_ID)
    moved = client.move_sync(asset, dest_folder)
    assert moved.parent == DEST_FOLDER_ID

    client.move_sync(asset, client.folder(FOLDER_ID))
    assert client.asset(MOVE_ASSET_ID).parent == FOLDER_ID


def test_move_async_asset_to_root_raises():
    client = EntityAPI()
    asset = client.asset(MOVE_ASSET_ID)
    with pytest.raises(RuntimeError):
        client.move_async(asset, None)


# --- metadata / add_metadata_as_fragment ---

def test_add_metadata_as_fragment():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    fragment = '<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Test Fragment</dc:title>'
    updated = client.add_metadata_as_fragment(asset, "http://purl.org/dc/elements/1.1/", fragment)
    assert updated is not None
    assert "http://purl.org/dc/elements/1.1/" in updated.metadata.values()
    client.delete_metadata(updated, "http://purl.org/dc/elements/1.1/")


def test_metadata():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    fragment = '<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Metadata URI Test</dc:title>'
    updated = client.add_metadata_as_fragment(asset, "http://purl.org/dc/elements/1.1/", fragment)
    uri = next(url for url, schema in updated.metadata.items() if schema == "http://purl.org/dc/elements/1.1/")
    xml_doc = client.metadata(uri)
    assert xml_doc is not None
    assert "Metadata URI Test" in xml_doc
    client.delete_metadata(updated, "http://purl.org/dc/elements/1.1/")


# --- xml_asset ---

def test_xml_asset():
    client = EntityAPI()
    xml_str = client.xml_asset(ASSET_ID)
    assert xml_str is not None
    assert ASSET_ID in xml_str


def test_xml_asset_not_found():
    client = EntityAPI()
    with pytest.raises(ReferenceNotFoundException):
        client.xml_asset("invalid-reference")


# --- generation ---

def test_generation():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)
    representation = list(client.representations(asset))[0]
    content_object = client.content_objects(representation)[0]
    gen_url = (
        f"{client.protocol}://{client.server}/api/entity/content-objects"
        f"/{content_object.reference}/generations/1"
    )
    gen = client.generation(gen_url, content_object.reference)
    assert gen is not None
    assert isinstance(gen.original, bool)
    assert isinstance(gen.active, bool)
    assert len(gen.bitstreams) > 0


# --- add_physical_asset ---

def test_add_physical_asset():
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    asset = client.add_physical_asset(
        title="Test Physical Asset",
        description="Test Description",
        parent=folder,
        security_tag="open",
    )
    assert asset is not None
    assert asset.title == "Test Physical Asset"
    assert asset.description == "Test Description"
    assert asset.parent == folder.reference
    try:
        client.delete_asset(asset, "test cleanup", "test cleanup")
    except RuntimeError:
        pass


# --- updated_entities ---

def test_updated_entities():
    client = EntityAPI()
    entities = list(client.updated_entities(previous_days=7))
    assert isinstance(entities, list)


# --- all_ingest_events ---

def test_all_ingest_events():
    client = EntityAPI()
    events = list(client.all_ingest_events(previous_days=30))
    assert isinstance(events, list)
    for event in events:
        assert 'eventType' in event


# --- entity_from_event ---

def test_entity_from_event():
    client = EntityAPI()
    ingest_events = list(client.all_ingest_events(previous_days=30))
    if not ingest_events:
        pytest.skip("No ingest events found in the last 30 days")
    event_ref = ingest_events[0].get('Ref')
    if event_ref is None:
        pytest.skip("Event has no Ref field")
    actions = list(client.entity_from_event(event_ref))
    assert isinstance(actions, list)

