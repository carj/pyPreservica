import pytest
from pyPreservica import *

CO_ID = "08838224-3fcb-4bac-994d-ad74effaee58"


def test_add_rescan_sync():
    client = EntityAPI()

    content_object = client.content_object("08838224-3fcb-4bac-994d-ad74effaee58")

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
