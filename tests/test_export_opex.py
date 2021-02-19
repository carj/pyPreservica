import pytest
from pyPreservica import *


def test_export_file_wait():
    client = EntityAPI()
    asset = client.asset("c365634e-9fcc-4ea1-b47f-077f55df9d64")
    zip_file = client.export_opex_sync(asset)
    assert os.path.exists(zip_file)
    assert 1066650 < os.stat(zip_file).st_size < 1066670
    os.remove(zip_file)


def test_export_file_no_wait():
    client = EntityAPI()
    asset = client.asset("c365634e-9fcc-4ea1-b47f-077f55df9d64")
    pid = client.export_opex_async(asset)
    status = "ACTIVE"

    while status == "ACTIVE":
        status = client.get_async_progress(pid)

    assert status == "COMPLETED"

    zip_file = client.download_opex(pid)
    assert os.path.exists(zip_file)
    assert 1066650 < os.stat(zip_file).st_size < 1066670
    os.remove(zip_file)

