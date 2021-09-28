import shutil
import xmlschema
import pytest
import zipfile
import xml.etree.ElementTree
from pyPreservica import *

client = EntityAPI()
FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
file = "./test_data/LC-USZ62-20901.tiff"
NS = "http://preservica.com/XIP/v6.0"

XML_DOCUMENT = "<person:Person  xmlns:person='https://www.person.com/person'>" \
               "<person:Name>Name</person:Name>" \
               "<person:Phone>01234 100 100</person:Phone>" \
               "<person:Email>test@test.com</person:Email>" \
               "<person:Address>Abingdon, UK</person:Address>" \
               "</person:Person>"


def test_create_simple_package_no_parent():
    with pytest.raises(RuntimeError):
        package = simple_asset_package(preservation_file=file)


def test_create_simple_package_with_parent():
    folder = client.folder(FOLDER_ID)
    package = simple_asset_package(preservation_file=file, parent_folder=folder)
    io_ref = os.path.basename(package).replace(".zip", "")
    with zipfile.ZipFile(package, "r") as zip_ref:
        zip_ref.extractall("./test_data/")
    folder = f"./test_data/{io_ref}"
    assert os.path.exists(folder)
    metadata = f"{folder}/metadata.xml"
    assert os.path.exists(metadata)
    xml_document = xml.etree.ElementTree.parse(metadata)
    ref = xml_document.find(f'.//{{{NS}}}InformationObject/{{{NS}}}Ref')
    assert ref.text == io_ref
    xmlschema.validate(metadata, './test_data/XIP-V6.0.xsd')
    shutil.rmtree(folder)


class FixityCallBackTuple:
    def __call__(self, filename, full_path):
        sha1 = FileHash(hashlib.sha1)
        return tuple(("SHA1", sha1(full_path)))


class FixityCallBack:
    def __call__(self, filename, full_path):
        sha1 = FileHash(hashlib.sha1)
        return "SHA1", sha1(full_path)


class TwoFixityCallBack:
    def __call__(self, filename, full_path):
        sha1 = FileHash(hashlib.sha1)
        md5 = FileHash(hashlib.md5)
        return {"MD5": md5(full_path), "SHA1": sha1(full_path)}


def test_create_simple_package_with_fixity_tuple():
    folder = client.folder(FOLDER_ID)
    package = simple_asset_package(preservation_file=file, parent_folder=folder,
                                   Preservation_files_fixity_callback=FixityCallBackTuple())
    io_ref = os.path.basename(package).replace(".zip", "")
    with zipfile.ZipFile(package, "r") as zip_ref:
        zip_ref.extractall("./test_data/")
    folder = f"./test_data/{io_ref}"
    assert os.path.exists(folder)
    metadata = f"{folder}/metadata.xml"
    assert os.path.exists(metadata)
    xml_document = xml.etree.ElementTree.parse(metadata)
    ref = xml_document.find(f'.//{{{NS}}}InformationObject/{{{NS}}}Ref')
    assert ref.text == io_ref
    xmlschema.validate(metadata, './test_data/XIP-V6.0.xsd')
    shutil.rmtree(folder)


def test_create_simple_package_with_fixity():
    folder = client.folder(FOLDER_ID)
    package = simple_asset_package(preservation_file=file, parent_folder=folder,
                                   Preservation_files_fixity_callback=FixityCallBack())
    io_ref = os.path.basename(package).replace(".zip", "")
    with zipfile.ZipFile(package, "r") as zip_ref:
        zip_ref.extractall("./test_data/")
    folder = f"./test_data/{io_ref}"
    assert os.path.exists(folder)
    metadata = f"{folder}/metadata.xml"
    assert os.path.exists(metadata)
    xml_document = xml.etree.ElementTree.parse(metadata)
    ref = xml_document.find(f'.//{{{NS}}}InformationObject/{{{NS}}}Ref')
    assert ref.text == io_ref
    xmlschema.validate(metadata, './test_data/XIP-V6.0.xsd')
    shutil.rmtree(folder)


def test_create_simple_package_with_fixities():
    folder = client.folder(FOLDER_ID)
    package = simple_asset_package(preservation_file=file, parent_folder=folder,
                                   Preservation_files_fixity_callback=TwoFixityCallBack())
    io_ref = os.path.basename(package).replace(".zip", "")
    with zipfile.ZipFile(package, "r") as zip_ref:
        zip_ref.extractall("./test_data/")
    folder = f"./test_data/{io_ref}"
    assert os.path.exists(folder)
    metadata = f"{folder}/metadata.xml"
    assert os.path.exists(metadata)
    xml_document = xml.etree.ElementTree.parse(metadata)
    ref = xml_document.find(f'.//{{{NS}}}InformationObject/{{{NS}}}Ref')
    assert ref.text == io_ref
    xmlschema.validate(metadata, './test_data/XIP-V6.0.xsd')
    shutil.rmtree(folder)


def test_create_complex_package_with_parent():
    folder = client.folder(FOLDER_ID)
    preservation_files_list = [file, file]
    package = complex_asset_package(preservation_files_list=preservation_files_list, parent_folder=folder)
    io_ref = os.path.basename(package).replace(".zip", "")
    with zipfile.ZipFile(package, "r") as zip_ref:
        zip_ref.extractall("./test_data/")
    folder = f"./test_data/{io_ref}"
    assert os.path.exists(folder)
    metadata = f"{folder}/metadata.xml"
    assert os.path.exists(metadata)
    xml_document = xml.etree.ElementTree.parse(metadata)
    ref = xml_document.find(f'.//{{{NS}}}InformationObject/{{{NS}}}Ref')
    assert ref.text == io_ref
    xmlschema.validate(metadata, './test_data/XIP-V6.0.xsd')
    shutil.rmtree(folder)


def test_create_complex_package_with_metadata():
    folder = client.folder(FOLDER_ID)
    preservation_files_list = [file, file]
    metadata = {"https://www.person.com/person": XML_DOCUMENT}
    package = complex_asset_package(preservation_files_list=preservation_files_list, parent_folder=folder,
                                    Asset_Metadata=metadata)
    io_ref = os.path.basename(package).replace(".zip", "")
    with zipfile.ZipFile(package, "r") as zip_ref:
        zip_ref.extractall("./test_data/")
    folder = f"./test_data/{io_ref}"
    assert os.path.exists(folder)
    metadata = f"{folder}/metadata.xml"
    assert os.path.exists(metadata)
    xml_document = xml.etree.ElementTree.parse(metadata)
    ref = xml_document.find(f'.//{{{NS}}}InformationObject/{{{NS}}}Ref')
    assert ref.text == io_ref
    xmlschema.validate(metadata, './test_data/XIP-V6.0.xsd')
    shutil.rmtree(folder)
