import pytest

from zipfile import ZipFile
from pyPreservica import *


def test_export_file_wait():
    client = EntityAPI()
    asset = client.asset("683f9db7-ff81-4859-9c03-f68cfa5d9c3d")
    zip_file = client.export_opex_sync(asset)
    assert os.path.exists(zip_file)
    assert 1066650 < os.stat(zip_file).st_size
    with ZipFile(zip_file, 'r') as zipObj:
        assert len(zipObj.namelist()) == 6
    os.remove(zip_file)


def test_export_file_no_wait():
    client = EntityAPI()
    asset = client.asset("683f9db7-ff81-4859-9c03-f68cfa5d9c3d")
    pid = client.export_opex_async(asset)
    status = "ACTIVE"

    while status == "ACTIVE":
        status = client.get_async_progress(pid)

    assert status == "COMPLETED"

    zip_file = client.download_opex(pid)
    assert os.path.exists(zip_file)
    assert 1066650 < os.stat(zip_file).st_size
    with ZipFile(zip_file, 'r') as zipObj:
        assert len(zipObj.namelist()) == 6

    os.remove(zip_file)

