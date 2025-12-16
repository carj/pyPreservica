from os.path import isfile

import pytest

from zipfile import ZipFile
from pyPreservica import *




def setup():
    pass


def tear_down(zip_files):
    for f in zip_files:
        if os.path.exists(f):
            os.remove(f)


@pytest.fixture
def setup_data():
    print("\nSetting up resources...")
    zip_files = []
    setup()
    yield zip_files
    print(f"\nTearing down resources...")
    tear_down(zip_files)

def test_export_file_wait(setup_data):
    client = EntityAPI()
    asset = client.asset("683f9db7-ff81-4859-9c03-f68cfa5d9c3d")
    zip_file = client.export_opex_sync(asset, IncludeContent='true', IncludeMetadata='true')
    assert os.path.exists(zip_file)
    setup_data.append(zip_file)
    assert 1066650 < os.stat(zip_file).st_size
    with ZipFile(zip_file, 'r') as zipObj:
        assert len(zipObj.namelist()) == 6
    os.remove(zip_file)


def test_export_file_no_wait(setup_data):
    client = EntityAPI()
    asset = client.asset("683f9db7-ff81-4859-9c03-f68cfa5d9c3d")
    pid = client.export_opex_async(asset, IncludeContent='true', IncludeMetadata='true')
    status = "ACTIVE"

    while status == "ACTIVE":
        status = client.get_async_progress(pid)

    assert status == "COMPLETED"

    zip_file = client.download_opex(pid)
    assert os.path.exists(zip_file)
    setup_data.append(zip_file)
    assert 1066650 < os.stat(zip_file).st_size
    with ZipFile(zip_file, 'r') as zipObj:
        assert len(zipObj.namelist()) == 6

    os.remove(zip_file)

