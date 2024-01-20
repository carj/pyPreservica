import uuid

import pytest
from pyPreservica import *


class IORefGen:
    def __init__(self, id_val):
        self.id_val = id_val

    def __call__(self):
        return self.id_val


def test_ingest_single_file():
    client = EntityAPI()
    upload = UploadAPI()
    folder_id = "9fd239eb-19a3-4a46-9495-40fd9a5d8f93"
    folder = client.folder(folder_id)
    file = "./test_data/LC-USZ62-20901.tiff"
    gener = str(uuid.uuid4())
    package = simple_asset_package(preservation_file=file, parent_folder=folder, IO_Identifier_callback=IORefGen(gener))
    token = upload.upload_zip_package(package)

    status = "ACTIVE"
    while status == "ACTIVE":
        status = client.get_async_progress(token)

    asset = client.asset(gener)

    assert asset.title == "LC-USZ62-20901"

    client.delete_asset(asset, "operator comment", "supervisor")


def test_ingest_single_file_title():
    client = EntityAPI()
    upload = UploadAPI()
    folder_id = "9fd239eb-19a3-4a46-9495-40fd9a5d8f93"
    folder = client.folder(folder_id)
    file = "./test_data/LC-USZ62-20901.tiff"
    gener = str(uuid.uuid4())
    package = simple_asset_package(preservation_file=file, parent_folder=folder, Title="My Title", IO_Identifier_callback=IORefGen(gener),
                                   Description="My Description")
    token = upload.upload_zip_package(package)

    status = "ACTIVE"
    while status == "ACTIVE":
        status = client.get_async_progress(token)

    asset = client.asset(gener)

    assert asset.title == "My Title"
    assert asset.description == "My Description"

    client.delete_asset(asset, "operator comment", "supervisor")


def test_ingest_access_file():
    client = EntityAPI()
    upload = UploadAPI()
    folder_id = "9fd239eb-19a3-4a46-9495-40fd9a5d8f93"
    folder = client.folder(folder_id)
    file = "./test_data/LC-USZ62-20901.tiff"
    access_file = "./test_data/LC-USZ62-20901.jpg"
    gener = str(uuid.uuid4())
    package = simple_asset_package(preservation_file=file, access_file=access_file, parent_folder=folder, Title="My Title",
                                   IO_Identifier_callback=IORefGen(gener), Description="My Description")
    token = upload.upload_zip_package(package)

    status = "ACTIVE"
    while status == "ACTIVE":
        status = client.get_async_progress(token)

    asset = client.asset(gener)

    assert asset.title == "My Title"
    assert asset.description == "My Description"

    assert 2 == len(client.representations(asset))

    client.delete_asset(asset, "operator comment", "supervisor")


def test_s3_upload():
    client = EntityAPI()
    upload = UploadAPI()
    folder_id = "9fd239eb-19a3-4a46-9495-40fd9a5d8f93"
    folder = client.folder(folder_id)
    file = "./test_data/LC-USZ62-20901.tiff"
    access_file = "./test_data/LC-USZ62-20901.jpg"
    gener = str(uuid.uuid4())
    package = simple_asset_package(preservation_file=file, access_file=access_file, parent_folder=folder, Title="S3 Upload",
                                   IO_Identifier_callback=IORefGen(gener), Description="My Description")

    buckets = upload.upload_buckets()
    for bucket in buckets:
        print(bucket['containerName'])

    upload.upload_zip_package_to_S3(path_to_zip_package=package,
                                    bucket_name="com.preservica.dev.preview.sales.autoupload", folder=folder)


