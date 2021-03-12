import csv
import json
import shutil
import tempfile
import uuid
import xml
from time import sleep

import boto3
from datetime import datetime
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError

from pyPreservica.common import *

logger = logging.getLogger(__name__)

GB = 1024 ** 3
transfer_config = TransferConfig(multipart_threshold=int((1 * GB) / 8))


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = xml.etree.ElementTree.tostring(elem, 'utf-8')
    re_parsed = minidom.parseString(rough_string)
    return re_parsed.toprettyxml(indent="  ")


def __create_io__(file_name=None, parent_folder=None, **kwargs):
    xip = Element('XIP')
    xip.set('xmlns', 'http://preservica.com/XIP/v6.0')
    io = SubElement(xip, 'InformationObject')
    ref = SubElement(io, 'Ref')

    if 'IO_Identifier_callback' in kwargs:
        ident_callback = kwargs.get('IO_Identifier_callback')
        ref.text = ident_callback()
    else:
        ref.text = str(uuid.uuid4())

    title = SubElement(io, 'Title')
    title.text = kwargs.get('Title', file_name)
    description = SubElement(io, 'Description')
    description.text = kwargs.get('Description', file_name)
    security = SubElement(io, 'SecurityTag')
    security.text = kwargs.get('SecurityTag', "open")
    custom_type = SubElement(io, 'CustomType')
    custom_type.text = kwargs.get('CustomType', "")
    parent = SubElement(io, 'Parent')

    if hasattr(parent_folder, "reference"):
        parent.text = parent_folder.reference
    elif isinstance(parent_folder, str):
        parent.text = parent_folder

    return xip, ref.text


def __make_representation__(xip, rep_name, rep_type, io_ref):
    representation = SubElement(xip, 'Representation')
    io_link = SubElement(representation, 'InformationObject')
    io_link.text = io_ref
    access_name = SubElement(representation, 'Name')
    access_name.text = rep_name
    access_type = SubElement(representation, 'Type')
    access_type.text = rep_type
    content_objects = SubElement(representation, 'ContentObjects')
    content_object = SubElement(content_objects, 'ContentObject')
    content_object_ref = str(uuid.uuid4())
    content_object.text = content_object_ref
    return content_object_ref


def __make_content_objects__(xip, content_title, co_ref, io_ref, tag, content_description, content_type):
    content_object = SubElement(xip, 'ContentObject')
    ref_element = SubElement(content_object, "Ref")
    ref_element.text = co_ref
    title = SubElement(content_object, "Title")
    title.text = content_title
    description = SubElement(content_object, "Description")
    description.text = content_description
    security_tag = SubElement(content_object, "SecurityTag")
    security_tag.text = tag
    custom_type = SubElement(content_object, "CustomType")
    custom_type.text = content_type
    parent = SubElement(content_object, "Parent")
    parent.text = io_ref


def __make_generation__(xip, filename, co_ref, generation_label):
    generation = SubElement(xip, 'Generation', {"original": "true", "active": "true"})
    content_object = SubElement(generation, "ContentObject")
    content_object.text = co_ref
    label = SubElement(generation, "Label")
    if generation_label:
        label.text = generation_label
    else:
        label.text = os.path.splitext(filename)[0]
    effective_date = SubElement(generation, "EffectiveDate")
    effective_date.text = datetime.now().isoformat()
    bitstreams = SubElement(generation, "Bitstreams")
    bitstream = SubElement(bitstreams, "Bitstream")
    bitstream.text = filename
    SubElement(generation, "Formats")
    SubElement(generation, "Properties")


def __make_bitstream__(xip, file_name, full_path, callback):
    bitstream = SubElement(xip, 'Bitstream')
    filename_element = SubElement(bitstream, "Filename")
    filename_element.text = file_name
    filesize = SubElement(bitstream, "FileSize")
    file_stats = os.stat(full_path)
    filesize.text = str(file_stats.st_size)
    physical_location = SubElement(bitstream, "PhysicalLocation")
    fixities = SubElement(bitstream, "Fixities")
    fixity = SubElement(fixities, "Fixity")
    fixity_algorithm_ref = SubElement(fixity, "FixityAlgorithmRef")
    fixity_value = SubElement(fixity, "FixityValue")
    fixity = callback(file_name, full_path)
    fixity_algorithm_ref.text = fixity[0]
    fixity_value.text = fixity[1]


def __make_representation_multiple_co__(xip, rep_name, rep_type, rep_files, io_ref):
    representation = SubElement(xip, 'Representation')
    io_link = SubElement(representation, 'InformationObject')
    io_link.text = io_ref
    access_name = SubElement(representation, 'Name')
    access_name.text = rep_name
    access_type = SubElement(representation, 'Type')
    access_type.text = rep_type
    content_objects = SubElement(representation, 'ContentObjects')
    refs_dict = {}
    for f in rep_files:
        content_object = SubElement(content_objects, 'ContentObject')
        content_object_ref = str(uuid.uuid4())
        content_object.text = content_object_ref
        refs_dict[content_object_ref] = f
    return refs_dict


def cvs_to_cmis_xslt(csv_file, xml_namespace, root_element, title="Metadata Title", export_folder=None,
                     additional_namespaces=None):
    """
            Create a custom CMIS transform to display metadata within UA.

    """
    headers = set()
    with open(csv_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for header in row:
                xml_tag = header.strip()
                xml_tag = xml_tag.replace(" ", "")
                xml_tag = xml_tag.replace("-", "")
                headers.add(xml_tag)
            break

    namespaces = {"version": "2.0",
                  "xmlns:xsl": "http://www.w3.org/1999/XSL/Transform",
                  "xmlns:fn": "http://www.w3.org/2005/xpath-functions",
                  "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
                  "xmlns:csv": xml_namespace,
                  "xmlns": "http://www.tessella.com/sdb/cmis/metadata",
                  "exclude-result-prefixes": "csv"}

    if additional_namespaces is not None:
        for prefix, uri in additional_namespaces.items():
            namespaces["xmlns:" + prefix] = uri

    xml_stylesheet = xml.etree.ElementTree.Element("xsl:stylesheet", namespaces)

    xml.etree.ElementTree.SubElement(xml_stylesheet, "xsl:output", {"method": "xml", "indent": "yes"})

    xml_template = xml.etree.ElementTree.SubElement(xml_stylesheet, "xsl:template", {"match": "csv:" + root_element})

    xml_group = xml.etree.ElementTree.SubElement(xml_template, "group")

    xml_title = xml.etree.ElementTree.SubElement(xml_group, "title")
    xml_title.text = title

    xml_templates = xml.etree.ElementTree.SubElement(xml_group, "xsl:apply-templates")

    elements = ""

    for header in headers:
        if ":" in header:
            elements = elements + "|" + header
        else:
            elements = elements + "|csv:" + header

    elements = elements[1:]

    xml_matches = xml.etree.ElementTree.SubElement(xml_stylesheet, "xsl:template", {"match": elements})

    xml_item = xml.etree.ElementTree.SubElement(xml_matches, "item")
    xml_name = xml.etree.ElementTree.SubElement(xml_item, "name")
    xml_name_value = xml.etree.ElementTree.SubElement(xml_name, "xsl:value-of", {
        "select": "fn:replace(translate(local-name(), '_', ' '), '([a-z])([A-Z])', '$1 $2')"})

    xml_value = xml.etree.ElementTree.SubElement(xml_item, "value")
    xml_value_value = xml.etree.ElementTree.SubElement(xml_value, "xsl:value-of", {"select": "."})

    xml_type = xml.etree.ElementTree.SubElement(xml_item, "type")
    xml_type_value = xml.etree.ElementTree.SubElement(xml_type, "xsl:value-of", {
        "select": "fn:replace(translate(local-name(), '_', ' '), '([a-z])([A-Z])', '$1 $2')"})

    xml_request = xml.etree.ElementTree.tostring(xml_stylesheet, encoding='utf-8', xml_declaration=True)
    cmis_xslt = root_element + "-cmis.xslt"
    if export_folder is not None:
        cmis_xslt = os.path.join(export_folder, cmis_xslt)
    file = open(cmis_xslt, "wt", encoding="utf-8")
    file.write(xml_request.decode("utf-8"))
    file.close()
    return cmis_xslt


def cvs_to_xsd(csv_file, xml_namespace, root_element, export_folder=None, additional_namespaces=None):
    """
        Create a XSD definition based on the csv file

    """
    headers = set()
    with open(csv_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for header in row:
                xml_tag = header.strip()
                xml_tag = xml_tag.replace(" ", "")
                xml_tag = xml_tag.replace("-", "")
                headers.add(xml_tag)
            break

    namespaces = {"xmlns:xs": "http://www.w3.org/2001/XMLSchema",
                  "attributeFormDefault": "unqualified",
                  "elementFormDefault": "qualified",
                  "targetNamespace": xml_namespace}

    if additional_namespaces is not None:
        for prefix, uri in additional_namespaces.items():
            namespaces["xmlns:" + prefix.trim()] = uri.trim()

    xml_schema = xml.etree.ElementTree.Element("xs:schema", namespaces)

    if additional_namespaces is not None:
        for prefix, namespace in additional_namespaces.items():
            xml_import = xml.etree.ElementTree.SubElement(xml_schema, "xs:import", {"namespace": namespace})

    xml_element = xml.etree.ElementTree.SubElement(xml_schema, "xs:element", {"name": root_element})

    xml_complex_type = xml.etree.ElementTree.SubElement(xml_element, "xs:complexType")
    xml_sequence = xml.etree.ElementTree.SubElement(xml_complex_type, "xs:sequence")
    for header in headers:
        if ":" in header:
            prefix, sep, tag = header.partition(":")
            try:
                namespace = additional_namespaces[prefix]
                xml.etree.ElementTree.SubElement(xml_sequence, "xs:element",
                                                 {"ref": header, "xmlns:" + prefix: namespace})
            except KeyError:
                xml.etree.ElementTree.SubElement(xml_sequence, "xs:element", {"type": "xs:string", "name": header})
        else:
            xml.etree.ElementTree.SubElement(xml_sequence, "xs:element", {"type": "xs:string", "name": header})

    xml_request = xml.etree.ElementTree.tostring(xml_schema, encoding='utf-8', xml_declaration=True)

    xsd_file = root_element + ".xsd"
    if export_folder is not None:
        xsd_file = os.path.join(export_folder, xsd_file)
    file = open(xsd_file, "wt", encoding="utf-8")
    file.write(xml_request.decode("utf-8"))
    file.close()
    return xsd_file


def csv_to_search_xml(csv_file, xml_namespace, root_element, title="Metadata Title", export_folder=None,
                      additional_namespaces=None):
    """
        Create a custom Preservica search index based on the columns in a csv file

    """
    headers = set()
    with open(csv_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for header in row:
                xml_tag = header.strip()
                xml_tag = xml_tag.replace(" ", "")
                xml_tag = xml_tag.replace("-", "")
                headers.add(xml_tag)
            break

    xml_index = xml.etree.ElementTree.Element("index", {"xmlns": "http://www.preservica.com/customindex/v1"})

    short_name = "csv"

    xml_schemaName = xml.etree.ElementTree.SubElement(xml_index, "schemaName")
    xml_schemaName.text = title
    xml_schemaUri = xml.etree.ElementTree.SubElement(xml_index, "schemaUri")
    xml_schemaUri.text = xml_namespace
    xml_shortName = xml.etree.ElementTree.SubElement(xml_index, "shortName")
    xml_shortName.text = short_name

    for header in headers:
        if ":" in header:
            xpath_expression = f"//{short_name}:{root_element}/{header}"
        else:
            xpath_expression = f"//{short_name}:{root_element}/{short_name}:{header}"

        attr = {"indexName": header, "displayName": header,
                "xpath": xpath_expression,
                "indexType": "STRING_DEFAULT"}
        xml_term = xml.etree.ElementTree.SubElement(xml_index, "term", attr)

    if additional_namespaces is not None:
        for prefix, uri in additional_namespaces.items():
            xml.etree.ElementTree.SubElement(xml_index, "namespaceMapping", {"key": prefix, "value": uri})

    xml_request = xml.etree.ElementTree.tostring(xml_index, encoding='utf-8', xml_declaration=True)
    search_xml = root_element + "-index.xml"
    if export_folder is not None:
        search_xml = os.path.join(export_folder, search_xml)
    file = open(search_xml, "wt", encoding="utf-8")
    file.write(xml_request.decode("utf-8"))
    file.close()
    return search_xml


def cvs_to_xml(csv_file, xml_namespace, root_element, file_name_column="filename", export_folder=None,
               additional_namespaces=None):
    """
    Export the rows of a CSV file as XML metadata documents which can be added to Preservica assets

    """
    headers = list()
    link_column_id = 0
    with open(csv_file, encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            col_id = 0
            for header in row:
                col_id += 1
                if header == file_name_column:
                    link_column_id = col_id
                xml_tag = header.strip()
                xml_tag = xml_tag.replace(" ", "")
                xml_tag = xml_tag.replace("-", "")
                headers.append(xml_tag)
            break
        if link_column_id > 0:
            namespaces = {"xmlns": xml_namespace}
            if additional_namespaces is not None:
                for prefix, uri in additional_namespaces.items():
                    namespaces["xmlns:" + prefix] = uri
            for row in reader:
                col_id = 0
                xml_object = xml.etree.ElementTree.Element(root_element, namespaces)
                for value, header in zip(row, headers):
                    col_id += 1
                    xml.etree.ElementTree.SubElement(xml_object, header).text = value
                    if col_id == link_column_id:
                        file_name = value
                xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8', xml_declaration=True)
                name = file_name + ".xml"
                name = sanitize(name)
                if export_folder is not None:
                    name = os.path.join(export_folder, name)
                file = open(name, "wt", encoding="utf-8")
                file.write(xml_request.decode("utf-8"))
                file.close()
                yield name


def complex_asset_package(preservation_files_list=None, access_files_list=None, export_folder=None,
                          parent_folder=None, **kwargs):
    """
        optional kwargs map
        'Title'                                 Asset Title
        'Description'                           Asset Description
        'SecurityTag'                           Asset Security Tag
        'CustomType'                            Asset Type
        'Preservation_Content_Title'            Content Object Title of the Preservation Object
        'Preservation_Content_Description'      Content Object Description of the Preservation Object
        'Access_Content_Title'                  Content Object Title of the Access Object
        'Access_Content_Description'            Content Object Description of the Access Object
        'Preservation_Generation_Label'         Generation Label for the Preservation Object
        'Access_Generation_Label'               Generation Label for the Access Object
        'Asset_Metadata'                        Map of metadata schema/documents to add to asset
        'Identifiers'                           Map of asset identifiers
        'Preservation_files_fixity_callback'    Callback to allow external generated fixity values
        'Access_files_fixity_callback'          Callback to allow external generated fixity values
        'IO_Identifier_callback'                Callback to allow external generated Asset identifier
    """
    # some basic validation
    if export_folder is None:
        export_folder = tempfile.gettempdir()
    if not os.path.isdir(export_folder):
        logger.error("Export Folder Does Not Exist")
        raise RuntimeError(export_folder, "Export Folder Does Not Exist")
    if parent_folder is None:
        logger.error("You must specify a parent folder for the package asset")
        raise RuntimeError("You must specify a parent folder for the package asset")

    io_ref = None
    xip = None
    default_asset_title = None
    preservation_refs_dict = dict()
    access_refs_dict = dict()

    security_tag = kwargs.get('SecurityTag', "open")
    content_type = kwargs.get('CustomType', "")

    has_preservation_files = bool((preservation_files_list is not None) and (len(preservation_files_list) > 0))
    has_access_files = bool((access_files_list is not None) and (len(access_files_list) > 0))

    if has_preservation_files:
        if default_asset_title is None:
            default_asset_title = os.path.splitext(os.path.basename(preservation_files_list[0]))[0]

        # create the asset
        xip, io_ref = __create_io__(file_name=default_asset_title, parent_folder=parent_folder, **kwargs)

    if has_access_files:
        if default_asset_title is None:
            default_asset_title = os.path.splitext(os.path.basename(access_files_list[0]))[0]

        if io_ref is None:
            xip, io_ref = __create_io__(file_name=default_asset_title, parent_folder=parent_folder, **kwargs)

    if has_preservation_files:
        # add the content objects
        preservation_refs_dict = __make_representation_multiple_co__(xip, "Preservation", "Preservation",
                                                                     preservation_files_list, io_ref)

    if has_access_files:
        # add the content objects
        access_refs_dict = __make_representation_multiple_co__(xip, "Access", "Access", access_files_list, io_ref)

    if has_preservation_files:

        for content_ref, filename in preservation_refs_dict.items():
            default_content_objects_title = os.path.splitext(os.path.basename(filename))[0]
            preservation_content_title = kwargs.get('Preservation_Content_Title', default_content_objects_title)
            preservation_content_description = kwargs.get('Preservation_Content_Description',
                                                          default_content_objects_title)

            if isinstance(preservation_content_title, dict):
                preservation_content_title = preservation_content_title[filename]

            if isinstance(preservation_content_description, dict):
                preservation_content_description = preservation_content_description[filename]

            __make_content_objects__(xip, preservation_content_title, content_ref, io_ref, security_tag,
                                     preservation_content_description, content_type)

    if has_access_files:

        for content_ref, filename in access_refs_dict.items():
            default_content_objects_title = os.path.splitext(os.path.basename(filename))[0]

            access_content_title = kwargs.get('Access_Content_Title', default_content_objects_title)
            access_content_description = kwargs.get('Access_Content_Description', default_content_objects_title)

            if isinstance(access_content_title, dict):
                access_content_title = access_content_title[filename]

            if isinstance(access_content_description, dict):
                access_content_title = access_content_title[filename]

            __make_content_objects__(xip, access_content_title, content_ref, io_ref, security_tag,
                                     access_content_description, content_type)

    if has_preservation_files:

        preservation_generation_label = kwargs.get('Preservation_Generation_Label', "")

        for content_ref, filename in preservation_refs_dict.items():
            preservation_file_name = os.path.basename(filename)
            __make_generation__(xip, preservation_file_name, content_ref, preservation_generation_label)

    if has_access_files:

        access_generation_label = kwargs.get('Access_Generation_Label', "")

        for content_ref, filename in access_refs_dict.items():
            access_file_name = os.path.basename(filename)
            __make_generation__(xip, access_file_name, content_ref, access_generation_label)

    if has_preservation_files:

        if 'Preservation_files_fixity_callback' in kwargs:
            callback = kwargs.get('Preservation_files_fixity_callback')
        else:
            callback = Sha1FixityCallBack()

        for content_ref, filename in preservation_refs_dict.items():
            preservation_file_name = os.path.basename(filename)
            __make_bitstream__(xip, preservation_file_name, filename, callback)

    if has_access_files:

        if 'Access_files_fixity_callback' in kwargs:
            callback = kwargs.get('Access_files_fixity_callback')
        else:
            callback = Sha1FixityCallBack()

        for content_ref, filename in access_refs_dict.items():
            access_file_name = os.path.basename(filename)
            __make_bitstream__(xip, access_file_name, filename, callback)

    if 'Identifiers' in kwargs:
        identifier_map = kwargs.get('Identifiers')
        for identifier_key, identifier_value in identifier_map.items():
            if identifier_key:
                if identifier_value:
                    identifier = SubElement(xip, 'Identifier')
                    id_type = SubElement(identifier, "Type")
                    id_type.text = identifier_key
                    id_value = SubElement(identifier, "Value")
                    id_value.text = identifier_value
                    id_io = SubElement(identifier, "Entity")
                    id_io.text = io_ref

    if 'Asset_Metadata' in kwargs:
        metadata_map = kwargs.get('Asset_Metadata')
        for metadata_ns, metadata_path in metadata_map.items():
            if metadata_ns:
                if metadata_path:
                    if os.path.exists(metadata_path) and os.path.isfile(metadata_path):
                        descriptive_metadata = xml.etree.ElementTree.parse(source=metadata_path)
                        metadata = SubElement(xip, 'Metadata', {'schemaUri': metadata_ns})
                        metadata_ref = SubElement(metadata, 'Ref')
                        metadata_ref.text = str(uuid.uuid4())
                        entity = SubElement(metadata, 'Entity')
                        entity.text = io_ref
                        content = SubElement(metadata, 'Content')
                        content.append(descriptive_metadata.getroot())

    if xip is not None:
        export_folder = export_folder
        top_level_folder = os.path.join(export_folder, io_ref)
        os.mkdir(top_level_folder)
        inner_folder = os.path.join(top_level_folder, io_ref)
        os.mkdir(inner_folder)
        os.mkdir(os.path.join(inner_folder, "content"))
        metadata_path = os.path.join(inner_folder, "metadata.xml")
        metadata = open(metadata_path, "wt", encoding='utf-8')
        metadata.write(prettify(xip))
        metadata.close()
        for content_ref, filename in preservation_refs_dict.items():
            src_file = filename
            dst_file = os.path.join(os.path.join(inner_folder, "content"), os.path.basename(filename))
            shutil.copyfile(src_file, dst_file)
        for content_ref, filename in access_refs_dict.items():
            src_file = filename
            dst_file = os.path.join(os.path.join(inner_folder, "content"), os.path.basename(filename))
            shutil.copyfile(src_file, dst_file)
        shutil.make_archive(top_level_folder, 'zip', top_level_folder)
        shutil.rmtree(top_level_folder)
        return top_level_folder + ".zip"


def simple_asset_package(preservation_file=None, access_file=None, export_folder=None, parent_folder=None, **kwargs):
    """
        optional kwargs map
        'Title'                             Asset Title
        'Description'                       Asset Description
        'SecurityTag'                       Asset Security Tag
        'CustomType'                        Asset Type
        'Preservation_Content_Title'        Content Object Title of the Preservation Object
        'Preservation_Content_Description'  Content Object Description of the Preservation Object
        'Access_Content_Title'              Content Object Title of the Access Object
        'Access_Content_Description'        Content Object Description of the Access Object
        'Preservation_Generation_Label'     Generation Label for the Preservation Object
        'Access_Generation_Label'           Generation Label for the Access Object
        'Asset_Metadata'                    Map of metadata schema/documents to add to asset
        'Identifiers'                       Map of asset identifiers
        'Preservation_files_fixity_callback'    Callback to allow external generated fixity values
        'Access_files_fixity_callback'    Callback to allow external generated fixity values
    """

    # some basic validation
    if export_folder is None:
        export_folder = tempfile.gettempdir()
    if not os.path.isdir(export_folder):
        logger.error("Export Folder Does Not Exist")
        raise RuntimeError(export_folder, "Export Folder Does Not Exist")
    if parent_folder is None:
        logger.error("You must specify a parent folder for the package asset")
        raise RuntimeError("You must specify a parent folder for the package asset")

    preservation_file_list = list()
    access_file_list = list()

    if preservation_file is not None:
        preservation_file_list.append(preservation_file)

    if access_file is not None:
        access_file_list.append(access_file)

    return complex_asset_package(preservation_files_list=preservation_file_list, access_files_list=access_file_list,
                                 export_folder=export_folder, parent_folder=parent_folder, **kwargs)


class UploadAPI(AuthenticatedAPI):

    def ingest_twitter_feed(self, twitter_user=None, num_tweets: int = 25, twitter_consumer_key=None,
                            twitter_secret_key=None, folder=None, callback=None, **kwargs):

        def get_image(m, has_video_element):
            media_url_https_ = m["media_url_https"]
            if media_url_https_:
                req = requests.get(media_url_https_)
                if req.status_code == requests.codes.ok:
                    if has_video_element:
                        image_name_ = f"{{{media_id_str}}}_[{twitter_user}]_thumb.jpg"
                    else:
                        image_name_ = f"{{{media_id_str}}}_[{twitter_user}].jpg"
                    image_name_document_ = open(image_name_, "wb")
                    image_name_document_.write(req.content)
                    image_name_document_.close()
                    return image_name_

        def get_video(m):
            video_info_ = m["video_info"]
            variants_ = video_info_["variants"]
            for v_ in variants_:
                video_url_ = v_["url"]
                req = requests.get(video_url_)
                if req.status_code == requests.codes.ok:
                    video_name_ = f"{{{media_id_str}}}_[{twitter_user}].mp4"
                    video_name_document_ = open(video_name_, "wb")
                    video_name_document_.write(req.content)
                    video_name_document_.close()
                    return video_name_, True

        entity_client = pyPreservica.EntityAPI(username=self.username, password=self.password, server=self.server,
                                               tenant=self.tenant)
        if hasattr(folder, "reference"):
            folder = entity_client.folder(folder.reference)
        else:
            folder = entity_client.folder(folder)
        try:
            import tweepy
            from tweepy import TweepError
        except ImportError:
            logger.error("Package tweepy is required for twitter harvesting. pip install --upgrade tweepy")
            raise RuntimeError("Package tweepy is required for twitter harvesting. pip install --upgrade tweepy")
        config = configparser.ConfigParser()
        config.read('credentials.properties')
        if twitter_consumer_key is None:
            twitter_consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
            if twitter_consumer_key is None:
                try:
                    twitter_consumer_key = config['credentials']['TWITTER_CONSUMER_KEY']
                except KeyError:
                    logger.error("No valid TWITTER_CONSUMER_KEY found in method arguments, "
                                 "environment variables or credentials.properties file")
                    raise RuntimeError("No valid TWITTER_CONSUMER_KEY found in method arguments, "
                                       "environment variables or credentials.properties file")
        if twitter_secret_key is None:
            twitter_secret_key = os.environ.get('TWITTER_SECRET_KEY')
            if twitter_secret_key is None:
                try:
                    twitter_secret_key = config['credentials']['TWITTER_SECRET_KEY']
                except KeyError:
                    logger.error("No valid TWITTER_SECRET_KEY found in method arguments, "
                                 "environment variables or credentials.properties file")
                    raise RuntimeError("No valid TWITTER_SECRET_KEY found in method arguments, "
                                       "environment variables or credentials.properties file")

        api = None
        try:
            auth = tweepy.AppAuthHandler(twitter_consumer_key, twitter_secret_key)
            api = tweepy.API(auth, wait_on_rate_limit=True)
        except TweepError:
            logger.error("No valid Twitter API keys. Could not authenticate")
            raise RuntimeError("No valid Twitter API keys. Could not authenticate")
        if api is not None:
            logger.debug(api)
            for tweet in tweepy.Cursor(api.user_timeline, id=twitter_user).items(int(num_tweets)):
                created_at = tweet.created_at
                id_str = tweet.id_str
                author = tweet.author.name
                tweet_entities = tweet.entities
                hashtags = dict()
                if 'hashtags' in tweet_entities:
                    hashtags = tweet.entities['hashtags']
                entities = entity_client.identifier("tweet_id", id_str.strip())
                if len(entities) > 0:
                    logger.warning("Tweet already exists, skipping....")
                    continue
                logger.info(f"Processing tweet {id_str} ...")
                tid = tweet.id
                content_objects = list()
                full_tweet = api.get_status(tid, tweet_mode="extended", include_entities=True)
                text = tweet.text
                full_text = full_tweet.full_text
                file_name = f"{{{id_str}}}_[{twitter_user}].json"
                json_doc = json.dumps(full_tweet._json)
                json_file = open(file_name, "wt", encoding="UTF-8")
                json_file.write(json_doc)
                json_file.close()
                content_objects.append(file_name)
                if hasattr(full_tweet, "extended_entities"):
                    extended_entities = full_tweet.extended_entities
                    if "media" in extended_entities:
                        media = extended_entities["media"]
                        for med in media:
                            media_id_str = med["id_str"]
                            has_video = False
                            if "video_info" in med:
                                co, has_video = get_video(med)
                                content_objects.append(co)
                                continue
                            if "media_url_https" in med:
                                co = get_image(med, has_video)
                                content_objects.append(co)
                identifiers = dict()
                asset_metadata = dict()
                identifiers["tweet_id"] = id_str

                user = full_tweet._json['user']

                if full_tweet._json.get('retweeted_status'):
                    retweeted_status = full_tweet._json['retweeted_status']
                    if retweeted_status.get("extended_entities"):
                        extended_entities = retweeted_status["extended_entities"]
                        if "media" in extended_entities:
                            media = extended_entities["media"]
                            for med in media:
                                media_id_str = med["id_str"]
                                has_video = False
                                if "video_info" in med:
                                    co, has_video = get_video(med)
                                    content_objects.append(co)
                                    continue
                                if "media_url_https" in med:
                                    co = get_image(med, has_video)
                                    content_objects.append(co)

                xml_object = xml.etree.ElementTree.Element('tweet', {"xmlns": "http://www.preservica.com/tweets/v1"})
                xml.etree.ElementTree.SubElement(xml_object, "id").text = id_str
                xml.etree.ElementTree.SubElement(xml_object, "full_text").text = full_text
                xml.etree.ElementTree.SubElement(xml_object, "created_at").text = str(created_at)
                xml.etree.ElementTree.SubElement(xml_object, "screen_name_sender").text = user.get('screen_name')
                for h in hashtags:
                    xml.etree.ElementTree.SubElement(xml_object, "hashtag").text = str(h['text'])

                xml.etree.ElementTree.SubElement(xml_object, "name").text = author
                xml.etree.ElementTree.SubElement(xml_object, "retweet").text = str(full_tweet._json['retweet_count'])
                xml.etree.ElementTree.SubElement(xml_object, "likes").text = str(full_tweet._json['favorite_count'])

                xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')

                metadata_document = open("metadata.xml", "wt", encoding="utf-8")
                metadata_document.write(xml_request.decode("utf-8"))
                metadata_document.close()

                asset_metadata["http://www.preservica.com/tweets/v1"] = "metadata.xml"

                security_tag = kwargs.get("SecurityTag", "open")
                asset_title = kwargs.get("Title", text)
                asset_description = kwargs.get("Description", full_text)

                p = complex_asset_package(preservation_files_list=content_objects, parent_folder=folder,
                                          Title=asset_title, Description=asset_description, CustomType="Tweet",
                                          Identifiers=identifiers, Asset_Metadata=asset_metadata,
                                          SecurityTag=security_tag)
                self.upload_zip_package(p, folder=folder, callback=callback)
                for ob in content_objects:
                    os.remove(ob)
                os.remove("metadata.xml")
                sleep(2)

    def ingest_web_video(self, url=None, parent_folder=None, **kwargs):
        try:
            import youtube_dl
        except ImportError:
            logger.error("Package youtube_dl is required for this method. pip install --upgrade youtube-dl")
            raise RuntimeError("Package youtube_dl is required for this method. pip install --upgrade youtube-dl")

        ydl_opts = {}

        def my_hook(d):
            if d['status'] == 'finished':
                logger.info('Download Complete. Uploading to Preservica ...')

        ydl_opts = {
            'outtmpl': '%(id)s.mp4',
            'progress_hooks': [my_hook],
        }

        if True:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = ['en']

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=True)

            vid_id = meta.get('id')

            if 'Title' in kwargs:
                title = kwargs.get("Title")
            else:
                title = meta.get('title')

            if 'Description' in kwargs:
                description = kwargs.get("Description")
            else:
                description = meta.get('description')

            if 'SecurityTag' in kwargs:
                security_tag = kwargs.get("SecurityTag")
            else:
                security_tag = "open"

            if 'Identifiers' in kwargs:
                identifier_map = kwargs.get('Identifiers')
                identifier_map["Video-ID"] = vid_id
            else:
                identifier_map = {"Video-ID": vid_id}

            if 'Asset_Metadata' in kwargs:
                descriptive_metadata = kwargs.get('Asset_Metadata')
            else:
                descriptive_metadata = {}

            if 'callback' in kwargs:
                callback = kwargs.get("callback")
            else:
                callback = None

            upload_date = meta.get('upload_date')
            duration = meta.get('duration')

            package = simple_asset_package(preservation_file=f"{vid_id}.mp4", parent_folder=parent_folder, Title=title,
                                           Description=description, Identifiers=identifier_map,
                                           Asset_Metadata=descriptive_metadata,
                                           Preservation_Content_Title=title, SecurityTag=security_tag)

            #self.upload_zip_package(path_to_zip_package=package, folder=parent_folder, callback=callback)

    def upload_zip_package(self, path_to_zip_package, folder=None, callback=None, delete_after_upload=False):
        bucket = f'{self.tenant.lower()}.package.upload'
        endpoint = f'https://{self.server}/api/s3/buckets'
        self.token = self.__token__()
        s3_client = boto3.client('s3', endpoint_url=endpoint, aws_access_key_id=self.token,
                                 aws_secret_access_key="NOT_USED",
                                 config=Config(s3={'addressing_style': 'path'}))

        metadata = dict()
        if folder is not None:
            if hasattr(folder, "reference"):
                metadata = {'Metadata': {'structuralobjectreference': folder.reference}}
            elif isinstance(folder, str):
                metadata = {'Metadata': {'structuralobjectreference': folder}}

        if os.path.exists(path_to_zip_package) and os.path.isfile(path_to_zip_package):
            try:
                key_id = str(uuid.uuid4()) + ".zip"
                s3_client.upload_file(path_to_zip_package, bucket, key_id, ExtraArgs=metadata,
                                      Callback=callback, Config=transfer_config)
                if delete_after_upload:
                    os.remove(path_to_zip_package)
            except ClientError as e:
                raise e

    def upload_zip_package_progress_token(self, path_to_zip_package, folder=None, delete_after_upload=False):
        bucket = f'{self.tenant.lower()}.package.upload'
        endpoint = f'https://{self.server}/api/s3/buckets'
        self.token = self.__token__()
        s3_client = boto3.client('s3', endpoint_url=endpoint, aws_access_key_id=self.token,
                                 aws_secret_access_key="NOT_USED",
                                 config=Config(s3={'addressing_style': 'path'}))

        metadata = dict()
        if folder is not None:
            if hasattr(folder, "reference"):
                metadata = {'structuralobjectreference': folder.reference}
            elif isinstance(folder, str):
                metadata = {'structuralobjectreference': folder}

        if os.path.exists(path_to_zip_package) and os.path.isfile(path_to_zip_package):
            try:
                key_id = str(uuid.uuid4()) + ".zip"
                with open(path_to_zip_package, 'rb') as fd:
                    response = s3_client.put_object(Body=fd, Bucket=bucket, Key=key_id, Metadata=metadata)

                if delete_after_upload:
                    os.remove(path_to_zip_package)
                return response['ResponseMetadata']['HTTPHeaders']['preservica-progress-token']
            except ClientError as e:
                raise e
