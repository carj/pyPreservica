from pyPreservica import *
import xml.etree.ElementTree


def test_get_xsd_documents():
    client = AdminAPI()
    xsd_documents = client.xml_schemas()
    assert type(xsd_documents) is list
    assert len(xsd_documents) > 10
    for xsd in xsd_documents:
        assert type(xsd) is dict
        assert "Name" in xsd
        assert "SchemaUri" in xsd
        assert "ApiId" in xsd


def test_get_xsd_document_by_uri():
    client = AdminAPI()
    xsd_document = client.xml_schema("http://purl.org/dc/elements/1.1/")
    xml.etree.ElementTree.fromstring(xsd_document)


def test_add_xsd_document():
    client = AdminAPI()
    client.delete_xml_schema("http://www.loc.gov/standards/alto/ns-v4#")

    xsd = requests.get("https://www.loc.gov/standards/alto/v4/alto-4-2.xsd").content.decode("utf-8")
    client.add_xml_schema(name="alto-4-2.xsd", description="alto", originalName="alto-4-2", xml_data=xsd)
    ns = "http://www.loc.gov/standards/alto/ns-v4#"
    xsd_document = client.xml_schema(ns)
    assert len(xsd_document) == len(xsd)

    client.delete_xml_schema("http://www.loc.gov/standards/alto/ns-v4#")


def test_get_xml_documents():
    client = AdminAPI()
    xml_documents = client.xml_documents()
    assert type(xml_documents) is list
    assert len(xml_documents) > 10
    for x in xml_documents:
        assert type(x) is dict
        assert "Name" in x
        assert "SchemaUri" in x
        assert "ApiId" in x


def test_get_xml_document_by_uri():
    client = AdminAPI()
    xsd_document = client.xml_document("http://www.openarchives.org/OAI/2.0/oai_dc/")
    xml.etree.ElementTree.fromstring(xsd_document)


def test_add_xml_document():
    client = AdminAPI()
    client.delete_xml_document("http://www.crossref.org/schema/5.4.0")
    xml_doc = requests.get(
        "https://gitlab.com/crossref/schema/-/raw/master/best-practice-examples/book5.3.0.xml").content.decode("utf-8")
    client.add_xml_document("book5.4.0", xml_doc)
    xml_document = client.xml_document("http://www.crossref.org/schema/5.4.0")
    assert len(xml_document) == len(xml_doc)
    client.delete_xml_document("http://www.crossref.org/schema/5.4.0")

    with open("test_data/mods.xml", mode="rb") as fd:
        client.add_xml_document("mods31", xml_doc)

    xml_document = client.xml_document("http://www.loc.gov/mods/v31")
    client.delete_xml_document("http://www.loc.gov/mods/v31")


def test_get_xml_transforms():
    client = AdminAPI()
    xml_transforms = client.xml_transforms()
    assert type(xml_transforms) is list
    assert len(xml_transforms) > 10
    for x in xml_transforms:
        assert type(x) is dict
        assert "Name" in x
        assert "FromSchemaUri" in x
        assert "ToSchemaUri" in x
        assert "ApiId" in x


def test_get_xml_transform_by_uri():
    client = AdminAPI()
    xsd_document = client.xml_transform("http://www.loc.gov/mods/v3", "http://www.tessella.com/sdb/cmis/metadata")
    xml.etree.ElementTree.fromstring(xsd_document)


def test_add_xml_transforms():
    client = AdminAPI()

    unog_transform = client.xml_transform("https://archive.unog.ch", "http://www.tessella.com/sdb/cmis/metadata")
    xml.etree.ElementTree.fromstring(unog_transform)

    client.delete_xml_transform("https://archive.unog.ch", "http://www.tessella.com/sdb/cmis/metadata")

    client.add_xml_transform("UNOG CMIS", "https://archive.unog.ch", "http://www.tessella.com/sdb/cmis/metadata",
                             "transform", "UNOG-CMIS.xml", unog_transform)
