import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_add_rescan_sync():
    client = EntityAPI()

    content_object = client.content_object(CO_ID)

    file = "./test_data/LC-USZ62-20901.tiff"

    status = client.replace_generation_sync(content_object, file)

    assert status == "COMPLETED"


def test_add_rescan_async():
    client = EntityAPI()

    content_object = client.content_object(CO_ID)

    file = "./test_data/LC-USZ62-20901.tiff"

    fh = FileHash(hashlib.md5)
    hash_val = fh(file)

    pid = client.replace_generation_async(content_object, file)

    status = "ACTIVE"

    while status == "ACTIVE":
        status = client.get_async_progress(pid)

    assert status == "COMPLETED"
