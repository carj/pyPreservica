"""
pyPreservica OpexAPI module definition

A Utility class to work with Opex Objects

author:     James Carr
licence:    Apache License 2.0

"""
import xml.etree.ElementTree
from typing import Generator
from zipfile import ZipFile


class OpexAPI(object):
    class OPEXMetadata(object):
        def __init__(self, source: str, title: str, description: str, SecurityDescriptor: str):
            self.pax_file = None
            self.source = source
            self.title = title
            self.description = description
            self.SecurityDescriptor = SecurityDescriptor

        def __str__(self):
            return self.__repr__()

        def __repr__(self):
            return {"SourceID": self.source, "Title": self.title, "Description": self.description,
                    "SecurityDescriptor": self.SecurityDescriptor}.__str__()

    def __init__(self, opex_file: str):
        self.opex = opex_file

    def bitstream_bytes(self, opex_metadata: OPEXMetadata, bitstream_name: dict):
        with ZipFile(self.opex) as zip_opex_file:
            for o in zip_opex_file.namelist():
                if o == opex_metadata.pax_file:
                    with zip_opex_file.open(opex_metadata.pax_file) as zip_pax_file:
                        with ZipFile(zip_pax_file) as pax_file:
                            name = "/".join(bitstream_name.values())
                            with pax_file.open(name, mode="r") as myfile:
                                return myfile.read()

    def xip_metadata(self, opex_metadata: OPEXMetadata):
        with ZipFile(self.opex) as zip_opex_file:
            for o in zip_opex_file.namelist():
                if o == opex_metadata.pax_file:
                    with zip_opex_file.open(opex_metadata.pax_file) as zip_pax_file:
                        with ZipFile(zip_pax_file) as pax_file:
                            for name in pax_file.namelist():
                                if name.endswith(".xip") is True:
                                    return name

    def xip_metadata(self, opex_metadata: OPEXMetadata):
        with ZipFile(self.opex) as zip_opex_file:
            for o in zip_opex_file.namelist():
                if o == opex_metadata.pax_file:
                    with zip_opex_file.open(opex_metadata.pax_file) as zip_pax_file:
                        with ZipFile(zip_pax_file) as pax_file:
                            for name in pax_file.namelist():
                                if (name.endswith("/") is False) and (name.endswith(".xip") is True):
                                    with pax_file.open(name, mode="r") as myfile:
                                        return myfile.read()

    def bitstream(self, opex_metadata: OPEXMetadata) -> Generator:
        with ZipFile(self.opex) as zip_opex_file:
            for o in zip_opex_file.namelist():
                if o == opex_metadata.pax_file:
                    with zip_opex_file.open(opex_metadata.pax_file) as zip_pax_file:
                        with ZipFile(zip_pax_file) as pax_file:
                            for name in pax_file.namelist():
                                if (name.endswith("/") is False) and (name.endswith(".xip") is False):
                                    parts = name.split("/")
                                    assert len(parts) == 4
                                    yield {"Representation": parts[0], "Content Object": parts[1],
                                           "Generation": parts[2], "Bitstream": parts[3]}

    def properties(self) -> Generator:
        with ZipFile(self.opex) as myzip:
            for o in myzip.namelist():
                if o.endswith(".pax.zip.opex"):
                    pax_file = o.replace(".pax.zip.opex", ".pax.zip")
                    with myzip.open(o) as myfile:
                        xml_response = str(myfile.read().decode('utf-8'))
                        entity_response = xml.etree.ElementTree.fromstring(xml_response)
                        source_id = entity_response.find(f'.//{{*}}SourceID')
                        title_node = entity_response.find(f'.//{{*}}Title')
                        description_node = entity_response.find(f'.//{{*}}Description')
                        tag_node = entity_response.find(f'.//{{*}}SecurityDescriptor')

                        title = title_node.text if hasattr(title_node, 'text') else None
                        description = description_node.text if hasattr(description_node, 'text') else None
                        tag = tag_node.text if hasattr(tag_node, 'text') else None

                        opex_metadata = self.OPEXMetadata(source_id.text, title, description, tag)
                        opex_metadata.pax_file = pax_file

                        yield opex_metadata
