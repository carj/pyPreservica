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
    """
    Utility class for reading and extracting content from Preservica OPEX export packages.

    An OPEX export is a ZIP file containing one or more ``.pax.zip`` archives (one per asset)
    and paired ``.pax.zip.opex`` sidecar XML files that carry the asset metadata. This class
    provides methods to iterate over those assets and extract their XIP metadata records and
    binary bitstream content.
    """

    class OPEXMetadata(object):
        """
        Container for the metadata associated with a single asset within an OPEX export.

        Instances are normally created by :meth:`OpexAPI.properties` and have their
        :attr:`pax_file` attribute set to the path of the corresponding ``.pax.zip`` entry
        within the outer OPEX ZIP file.
        """

        def __init__(self, source: str, title: str, description: str, SecurityDescriptor: str):
            """
            Initialise an OPEXMetadata instance.

            :param source: The Preservica source identifier (reference UUID) of the asset.
            :type source: str
            :param title: The descriptive title of the asset, or ``None`` if not set.
            :type title: str
            :param description: A longer free-text description of the asset, or ``None`` if not set.
            :type description: str
            :param SecurityDescriptor: The security tag applied to the asset (e.g. ``"open"``).
            :type SecurityDescriptor: str
            """
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
        """
        Initialise the OpexAPI with the path to an OPEX export ZIP file.

        :param opex_file: Absolute or relative filesystem path to the ``.opex`` ZIP archive
            produced by a Preservica export.
        :type opex_file: str
        """
        self.opex = opex_file

    def bitstream_bytes(self, opex_metadata: OPEXMetadata, bitstream_name: dict):
        """
        Read and return the raw bytes of a specific bitstream from within a PAX archive.

        Locates the ``.pax.zip`` archive identified by ``opex_metadata.pax_file`` inside the outer
        OPEX ZIP, then opens the nested PAX ZIP and reads the file whose path is formed by joining
        all values in ``bitstream_name`` with ``/``.

        :param opex_metadata: Metadata object identifying which PAX archive to open, as returned
            by :meth:`properties`.
        :type opex_metadata: OPEXMetadata
        :param bitstream_name: An ordered dict whose values are joined with ``/`` to form the
            path of the target file inside the PAX archive (e.g.
            ``{"Representation": "...", "Content Object": "...", "Generation": "...", "Bitstream": "..."}``)
            as yielded by :meth:`bitstream`.
        :type bitstream_name: dict
        :returns: The raw binary content of the requested bitstream, or ``None`` if the PAX archive
            is not found within the OPEX file.
        :rtype: bytes or None
        """
        with ZipFile(self.opex) as zip_opex_file:
            for o in zip_opex_file.namelist():
                if o == opex_metadata.pax_file:
                    with zip_opex_file.open(opex_metadata.pax_file) as zip_pax_file:
                        with ZipFile(zip_pax_file) as pax_file:
                            name = "/".join(bitstream_name.values())
                            with pax_file.open(name, mode="r") as myfile:
                                return myfile.read()

    def xip_metadata(self, opex_metadata: OPEXMetadata):
        """
        Return the name of the XIP metadata file within the PAX archive (unused — shadowed below).

        .. deprecated::
            This definition is immediately overridden by the second :meth:`xip_metadata` definition
            below. It is retained here for reference only and is never called at runtime.

        :param opex_metadata: Metadata object identifying which PAX archive to inspect, as returned
            by :meth:`properties`.
        :type opex_metadata: OPEXMetadata
        :returns: The archive-relative path of the first ``.xip`` file found, or ``None``.
        :rtype: str or None
        """
        with ZipFile(self.opex) as zip_opex_file:
            for o in zip_opex_file.namelist():
                if o == opex_metadata.pax_file:
                    with zip_opex_file.open(opex_metadata.pax_file) as zip_pax_file:
                        with ZipFile(zip_pax_file) as pax_file:
                            for name in pax_file.namelist():
                                if name.endswith(".xip") is True:
                                    return name

    def xip_metadata(self, opex_metadata: OPEXMetadata):
        """
        Read and return the raw bytes of the XIP metadata file from within a PAX archive.

        Opens the ``.pax.zip`` archive identified by ``opex_metadata.pax_file`` inside the outer
        OPEX ZIP, locates the first entry whose name ends with ``.xip`` (excluding directory
        entries), and returns its binary content.

        :param opex_metadata: Metadata object identifying which PAX archive to inspect, as returned
            by :meth:`properties`.
        :type opex_metadata: OPEXMetadata
        :returns: The raw binary content of the XIP metadata file, or ``None`` if the PAX archive
            or XIP entry is not found.
        :rtype: bytes or None
        """
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
        """
        Yield the path components of every bitstream stored within a PAX archive.

        Opens the ``.pax.zip`` archive identified by ``opex_metadata.pax_file`` inside the outer
        OPEX ZIP and iterates over all non-directory, non-XIP entries. Each entry's four-part path
        (``Representation/ContentObject/Generation/Bitstream``) is split and yielded as a dict.
        The returned dict can be passed directly to :meth:`bitstream_bytes` to retrieve the file
        content.

        :param opex_metadata: Metadata object identifying which PAX archive to inspect, as returned
            by :meth:`properties`.
        :type opex_metadata: OPEXMetadata
        :returns: A generator that yields one dict per bitstream with the keys ``"Representation"``,
            ``"Content Object"``, ``"Generation"``, and ``"Bitstream"``.
        :rtype: Generator[dict, None, None]
        """
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
        """
        Yield an :class:`OPEXMetadata` instance for every asset in the OPEX export.

        Iterates over all entries in the outer OPEX ZIP whose names end with
        ``.pax.zip.opex``, parses each sidecar XML file to extract the asset's source
        identifier, title, description, and security tag, and yields a populated
        :class:`OPEXMetadata` object with its :attr:`~OPEXMetadata.pax_file` attribute set
        to the path of the corresponding ``.pax.zip`` archive within the same ZIP.

        The yielded objects can be passed to :meth:`bitstream`, :meth:`bitstream_bytes`, and
        :meth:`xip_metadata` to access the asset's content.

        :returns: A generator that yields one :class:`OPEXMetadata` per asset found in the
            OPEX export file.
        :rtype: Generator[OPEXMetadata, None, None]
        """
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
