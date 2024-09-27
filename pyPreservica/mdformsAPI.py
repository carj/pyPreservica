"""
pyPreservica MDFormsAPI module definition

A client library for the Preservica Repository web services Metadata API
https://demo.preservica.com/api/metadata/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
import json
import xml.etree.ElementTree
from typing import Callable, List

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
    fields: List[GroupField] = []

    def __str__(self):
        return (f"Group ID: {self.group_id}\n" + f"Group Name: {self.name}\n" +
                f"Group Description: {self.description}\n" + f"Group Schema URI: {self.schemaUri}")


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

         :return: None
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

    def add_group(self, group_name: str, group_description: str, fields: List[GroupField]):
        """
          Create a new Metadata Group GroupFields

          :param group_name: The name of the new Group
          :type group_name: str

          :param group_description: The description of the new Group
          :type group_description: str

          :param fields: The list of fields
          :type fields: List[GroupField]

          :return:  JSON document
          :rtype: str

          """

        fields_str_list = []
        for field in fields:

            values = ""
            if (field.values is not None) and (len(field.values) > 0):
                values = f"""\n"values" : [ {",".join('"' + item + '"' for item in field.values)} ],
                """

            fields_str = f"""{{
            "id" : "{field.field_id}",
            "name": "{field.name}",
            "type": "{field.field_type.value}",
            "minOccurs": "{field.minOccurs}",
            "maxOccurs": "{field.maxOccurs}",
            "visible": "{field.visible}", {values}
            "editable": "{field.editable}",
            "defaultValue": "{field.default}",
            "indexed": "{field.indexed}"
            }}"""
            
            fields_str_list.append(fields_str)

        json_doc = f"""{{
          "name" : "{group_name}",
          "description" : "{group_description}",
          "fields" : [ {",".join(fields_str_list)}  ]
        }}"""

        print(json_doc)

        json_response = self.add_group_json(json_doc)
        group_id = json_response['id']
        return self.group(group_id)

    def add_group_json(self, json_document: str) -> str:
        """
         Create a new Metadata Group using a JSON document

         :param json_document: JSON document
         :type json_document: str

         :return:  JSON document
         :rtype: str

         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/'
        with self.session.post(url, headers=headers, data=json_document) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.add_group_json(json_document)
            elif request.status_code == requests.codes.created:
                return json.loads(str(request.content.decode('utf-8')))
            else:
                exception = HTTPException(None, request.status_code, request.url, "add_group_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def group_json(self, group_id: str) -> str:
        """
         Return a Group as a JSON document

         :param group_id: The Group id
         :type group_id: str

         :return:  JSON document
         :rtype: str

         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{group_id}'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.group_json(group_id)
            elif request.status_code == requests.codes.ok:
                return str(request.content.decode('utf-8'))
            else:
                exception = HTTPException(None, request.status_code, request.url, "group_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def group(self, group_id: str) -> Group:
        """
         Return a Group object by its id

         :param group_id: The Group id
         :type group_id: str

         :return: The Group
         :rtype: Group

         """
        json_group = json.loads(self.group_json(group_id))
        group: Group = Group()
        group.group_id = json_group['id']
        group.name = json_group['name']
        group.description = json_group['description']
        group.schemaUri = json_group['schemaUri']

        for f in json_group['fields']:
            gf: GroupField = GroupField(f['id'], f['name'])
            if 'type' in f:
                gf.field_type = f['type']
            if 'visible' in f:
                gf.visible = f['visible']
            if 'editable' in f:
                gf.editable = f['editable']
            if 'indexed' in f:
                gf.indexed = f['indexed']
            if 'maxOccurs' in f:
                gf.maxOccurs = f['maxOccurs']
            if 'minOccurs' in f:
                gf.minOccurs = f['minOccurs']
            if 'values' in f:
                gf.values = f['values']
            group.fields.append(gf)
        return group

    def groups_json(self) -> str:
        """
        Return all the groups in the tenancy as a single json document

        :return: JSON document
        :rtype: str

        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.groups_json()
            elif request.status_code == requests.codes.ok:
                return str(request.content.decode('utf-8'))
            else:
                exception = HTTPException(None, request.status_code, request.url, "groups_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def groups(self) -> List[Group]:
        """
        Return all the groups in the tenancy

        :return: list of Groups
        :rtype: List[Group]

        """
        groups = json.loads(self.groups_json())['groups']
        return_groups = []
        for g in groups:
            group: Group = Group()
            group.group_id = g['id']
            group.name = g['name']
            group.description = g['description']
            group.schemaUri = g['schemaUri']
            return_groups.append(group)
        return return_groups
