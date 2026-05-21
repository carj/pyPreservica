import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def setup():
    pass


def tear_down():
    pass


@pytest.fixture
def setup_data(request):
    print(f"\nRunning test: {request.node.name}")

    setup()

    yield

    tear_down()


def test_delete_folder(setup_data):
    client = EntityAPI()
    folder = client.folder(FOLDER_ID)
    assert folder
    new_folder = client.create_folder(title="title", description="description", security_tag="open",
                                      parent=folder.reference)
    assert folder.reference == new_folder.parent
    ref = client.delete_folder(new_folder, "operator", "supervisor")
    assert ref == new_folder.reference
