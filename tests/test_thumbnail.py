import pytest

from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_add_thumbnail_to_asset():
    client = EntityAPI()
    asset = client.asset(ASSET_ID)

    file = "./test_data/267_Python_logo-512.png"

    client.add_thumbnail(asset, file)

    client.remove_thumbnail(asset)


def test_add_thumbnail_to_folder():
    client = EntityAPI()

    folder = client.folder(FOLDER_ID)

    file = "./test_data/267_Python_logo-512.png"

    client.add_thumbnail(folder, file)

    client.remove_thumbnail(folder)


def test_add_thumbnail_to_content_object():
    client = EntityAPI()

    content_object = client.content_object(CO_ID)

    file = "./test_data/LC-USZ62-20901.tiff"

    with pytest.raises(RuntimeError):
        client.add_thumbnail(content_object, file)
