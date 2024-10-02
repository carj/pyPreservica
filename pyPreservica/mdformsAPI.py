"""
pyPreservica MDFormsAPI module definition

A client library for the Preservica Repository web services Metadata API
https://demo.preservica.com/api/metadata/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
import xml.etree.ElementTree
from typing import Callable, List, Union, Generator

from pyPreservica.common import *


class GroupFieldType(Enum):
    STRING = "STRING"
    LONG_STRING = "LONGSTRING"
    DATE = "DATE"
    NUMBER = "NUMBER"


class GroupField:
    field_id: str
    name: str
    field_type: GroupFieldType
    maxLength: int
    default: str
    visible: bool
    editable: bool
    minOccurs: int
    maxOccurs: int
    values: List[str]
    indexed: bool

    def __init__(self, field_id: str, name: str, field_type: GroupFieldType = GroupFieldType.STRING,
                 maxLength: int = -1, default: str = "", visible: bool = True, editable: bool = True,
                 minOccurs: int = 0, maxOccurs: int = 1, indexed: bool = True, values: List = None):
        self.field_id = field_id
        self.name = name
        self.field_type = field_type
        self.maxLength = maxLength
        self.default = default
        self.visible = visible
        self.editable = editable
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs
        self.values = values
        self.indexed = indexed

    def __str__(self):
        return (f"Field ID: {self.field_id}\n" + f"Field Name: {self.name}\n" + f"Field Type: {self.field_type}\n" +
                f"Field Visible: {self.visible}\n" + f"Field Editable: {self.editable}\n")


class Group:
    group_id: str
    name: str
    description: str
    schemaUri: str
    fields: List[GroupField]

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.fields = []

    def __str__(self):
        return (f"Group ID: {self.group_id}\n" + f"Group Name: {self.name}\n" +
                f"Group Description: {self.description}\n" + f"Group Schema URI: {self.schemaUri}")


def _object_from_json_(json_doc: dict) -> Group:
    """
    Create a JSON dict object from a Group object
    """

    group: Group = Group(name=json_doc['name'], description=json_doc['description'])
    group.fields = []
    if 'id' in json_doc:
        group.group_id = json_doc['id']
    if 'schemaUri' in json_doc:
        group.schemaUri = json_doc['schemaUri']

    if 'fields' in json_doc:
        for field in json_doc['fields']:
            gf: GroupField = GroupField(field['id'], field['name'], GroupFieldType(str(field['type'])))
            if 'minOccurs' in field:
                gf.minOccurs = int(field['minOccurs'])
            if 'maxOccurs' in field:
                gf.maxOccurs = int(field['maxOccurs'])
            if 'visible' in field:
                gf.visible = bool(field['visible'])
            if 'editable' in field:
                gf.editable = bool(field['editable'])
            if 'values' in field:
                for v in field['values']:
                    gf.values.append(str(v))
            if 'defaultValue' in field:
                gf.default = str(field['defaultValue'])
            if 'indexed' in field:
                gf.indexed = bool(field['indexed'])

            group.fields.append(gf)

    return group


def _json_from_object_(group: Group) -> dict:
    """
    Create a JSON dict object from a Group object
    """

    fields = []
    for field in group.fields:
        f = {"id": field.field_id, "name": field.name, "type": str(field.field_type.value)}
        f["minOccurs"] = str(field.minOccurs)
        f["maxOccurs"] = str(field.maxOccurs)
        f["visible"] = str(field.visible)
        f["editable"] = str(field.editable)
        if (field.values is not None) and (len(field.values) > 0):
            f["values"] = [item for item in field.values]
        f["defaultValue"] = str(field.default)
        f["indexed"] = str(field.indexed)
        fields.append(f)

    json_doc = {"name": group.name, "description": group.description, "fields": fields}

    return json_doc


class MetadataGroupsAPI(AuthenticatedAPI):
    def __init__(self, username: str = None, password: str = None, tenant: str = None, server: str = None,
                 use_shared_secret: bool = False, two_fa_secret_key: str = None,
                 protocol: str = "https", request_hook: Callable = None):

        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook)

        xml.etree.ElementTree.register_namespace("oai_dc", "http://www.openarchives.org/OAI/2.0/oai_dc/")
        xml.etree.ElementTree.register_namespace("ead", "urn:isbn:1-931666-22-9")

    def delete_group_namespace(self, schema: str):
        """
         Delete a new Metadata Group using its schema URI

         :param schema: The Group namespace schema URI
         :type schema: str

         :return: None
         :rtype: None

         """
        for group in self.groups():
            if group.schemaUri == schema:
                self.delete_group(group.group_id)

    def delete_group(self, group_id: str):
        """
         Delete a new Metadata Group using its ID

         :param group_id: Group ID
         :type group_id: str

         :return:
         :rtype: None

         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{group_id}'
        with self.session.delete(url, headers=headers) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.delete_group(group_id)
            elif request.status_code == requests.codes.no_content:
                return None
            else:
                exception = HTTPException(None, request.status_code, request.url, "delete_group",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def add_fields(self, group_id: str, new_fields: List[GroupField]) -> dict:
        """
        Add new metadata fields to an existing Group

        The new fields are appended to the end of the group

        :param group_id: The group ID of the group to update
        :type group_id: str

        :param new_fields: The list of new fields to add to the group
        :type new_fields: List[GroupField]

        :return:  The updated Metadata Group as a JSON dict
        :rtype:   dict


        """

        this_group: Group = self.group(group_id)

        for field in new_fields:
            this_group.fields.append(field)

        doc = _json_from_object_(this_group)

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{group_id}'
        with self.session.put(url, headers=headers, json=doc) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.add_fields(group_id, new_fields)
            elif request.status_code == requests.codes.created:
                return json.loads(str(request.content.decode('utf-8')))
            else:
                exception = HTTPException(None, request.status_code, request.url, "add_fields",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def add_group(self, group_name: str, group_description: str, fields: List[GroupField]) -> dict:
        """
          Create a new Metadata Group GroupFields

          :param group_name: The name of the new Group
          :type group_name: str

          :param group_description: The description of the new Group
          :type group_description: str

          :param fields: The list of fields
          :type fields: List[GroupField]

          :return:  The new metadata Group as a JSON dict
          :rtype:   dict

          """

        group: Group = Group(group_name, group_description)
        group.fields = fields

        json_document: dict = _json_from_object_(group)
        json_response: dict = self.add_group_json(json_document)
        return json_response

    def add_group_json(self, json_object: Union[dict, str]) -> dict:
        """
          Create a new Metadata Group using a JSON dictionary object or document

          :param json_object: JSON dictionary or string
          :type json_object: dict

          :return:  JSON document
          :rtype: dict

          """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/'

        if isinstance(json_object, dict):
            with self.session.post(url, headers=headers, json=json_object) as request:
                if request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.add_group_json(json_object)
                elif request.status_code == requests.codes.created:
                    return json.loads(str(request.content.decode('utf-8')))
                else:
                    exception = HTTPException(None, request.status_code, request.url, "add_group_json",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception

        elif isinstance(json_object, str):
            with self.session.post(url, headers=headers, data=json_object) as request:
                if request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.add_group_json(json_object)
                elif request.status_code == requests.codes.created:
                    return json.loads(str(request.content.decode('utf-8')))
                else:
                    exception = HTTPException(None, request.status_code, request.url, "add_group_json",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception
        else:
            raise RuntimeError("Argument must be a JSON dictionary or a JSON str")

    def group_json(self, group_id: str) -> dict:
        """
         Return a Group as a JSON object

         :param group_id: The Group id
         :type group_id: str

         :return:  JSON document
         :rtype: dict

         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{group_id}'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.group_json(group_id)
            elif request.status_code == requests.codes.ok:
                return json.loads(str(request.content.decode('utf-8')))
            else:
                exception = HTTPException(None, request.status_code, request.url, "group_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def group(self, group_id: str) -> Group:
        """
         Return a Group object by its ID

         :param group_id: The Group id
         :type group_id: str

         :return:  The metadata Group Object
         :rtype: Group

         """

        return _object_from_json_(self.group_json(group_id))

    def groups_json(self) -> List[dict]:
        """
        Return all the metadata Groups in the tenancy as a list of JSON dict objects

        :return: List of JSON dictionary object
        :rtype: List[dict]

        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.groups_json()
            elif request.status_code == requests.codes.ok:
                return json.loads(str(request.content.decode('utf-8')))['groups']
            else:
                exception = HTTPException(None, request.status_code, request.url, "groups_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def groups(self) -> Generator[Group, None, None]:
        """
        Return all the metadata Groups in the tenancy as Group Objects

        :return: Generator of Group Objects
        :rtype: Group

        """

        for group in self.groups_json():
            yield _object_from_json_(group)
