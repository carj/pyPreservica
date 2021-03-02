import pytest
import xmlschema
from pyPreservica import *


def test_can_create_xml_docs_from_csv():
    csv_file = "./test_data/metadata.csv"
    xsd_file = cvs_to_xsd(csv_file, xml_namespace="https://metadata.com", root_element="oai_dc")

    for xml_file in cvs_to_xml(csv_file, xml_namespace="https://metadata.com", root_element="oai_dc",
                               file_name_column="Identifier"):
        print(xmlschema.validate(xml_file, xsd_file))

    cmis_schema = "./test_data/CmisMetadata.xsd"
    cmis_file = cvs_to_cmis_xslt(csv_file, xml_namespace="https://metadata.com", root_element="oai_dc")

    search_schema = "./test_data/custom-indexer.xsd"
    search_file = csv_to_search_xml(csv_file, xml_namespace="https://metadata.com", root_element="oai_dc")

    xmlschema.validate(search_file, search_schema)
