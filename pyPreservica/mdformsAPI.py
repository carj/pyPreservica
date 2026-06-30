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
        """
        Initialise a GroupField with its identifier, display name, and optional constraints.

        :param field_id: Unique identifier for the field within its group.
        :type field_id: str
        :param name: Human-readable display name for the field.
        :type name: str
        :param field_type: Data type of the field (STRING, LONG_STRING, DATE, or NUMBER).
        :type field_type: GroupFieldType
        :param maxLength: Maximum character length for the field value; -1 means unlimited.
        :type maxLength: int
        :param default: Default value to pre-populate the field with.
        :type default: str
        :param visible: Whether the field is visible in the metadata form UI.
        :type visible: bool
        :param editable: Whether the field value can be edited by users.
        :type editable: bool
        :param minOccurs: Minimum number of times the field must appear (0 = optional).
        :type minOccurs: int
        :param maxOccurs: Maximum number of times the field may appear (1 = single value).
        :type maxOccurs: int
        :param indexed: Whether the field value is indexed for search.
        :type indexed: bool
        :param values: Optional list of allowed values forming a controlled vocabulary.
        :type values: list or None
        """
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
        """
        Return a human-readable string representation of this GroupField.

        :returns: Multi-line string showing the field ID, name, type, visibility, and editability.
        :rtype: str
        """
        return (f"Field ID: {self.field_id}\n" + f"Field Name: {self.name}\n" + f"Field Type: {self.field_type}\n" +
                f"Field Visible: {self.visible}\n" + f"Field Editable: {self.editable}\n")


class Group:
    group_id: str
    name: str
    description: str
    schemaUri: str
    fields: List[GroupField]

    def __init__(self, name: str, description: str):
        """
        Initialise a Group with a name and description, with an empty field list.

        :param name: Human-readable name for the metadata group.
        :type name: str
        :param description: Descriptive text explaining the purpose of the group.
        :type description: str
        """
        self.name = name
        self.description = description
        self.fields = []

    def __str__(self):
        """
        Return a human-readable string representation of this Group.

        :returns: Multi-line string showing the group ID, name, description, and schema URI.
        :rtype: str
        """
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
                    if gf.values is None:
                        gf.values = []
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
                 protocol: str = "https", request_hook: Callable = None, credentials_path: str = 'credentials.properties'):
        """
        Initialise the MetadataGroupsAPI client and register common XML namespaces.

        Credentials may be supplied as arguments or loaded automatically from environment
        variables (``PRESERVICA_USERNAME``, ``PRESERVICA_PASSWORD``, ``PRESERVICA_TENANT``,
        ``PRESERVICA_SERVER``) or from a ``credentials.properties`` file.

        :param username: Preservica account username (email address).
        :type username: str or None
        :param password: Preservica account password.
        :type password: str or None
        :param tenant: Preservica tenancy name.
        :type tenant: str or None
        :param server: Preservica server hostname (e.g. ``demo.preservica.com``).
        :type server: str or None
        :param use_shared_secret: Use a shared-secret token rather than username/password.
        :type use_shared_secret: bool
        :param two_fa_secret_key: TOTP secret key for two-factor authentication.
        :type two_fa_secret_key: str or None
        :param protocol: HTTP protocol to use, either ``"https"`` (default) or ``"http"``.
        :type protocol: str
        :param request_hook: Optional callable invoked as a requests event hook before each request.
        :type request_hook: Callable or None
        :param credentials_path: Path to a ``credentials.properties`` file used when explicit
            credentials are not provided.
        :type credentials_path: str
        """
        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook, credentials_path)

        xml.etree.ElementTree.register_namespace("oai_dc", "http://www.openarchives.org/OAI/2.0/oai_dc/")
        xml.etree.ElementTree.register_namespace("ead", "urn:isbn:1-931666-22-9")

    def download_template(self, form_name: str):
        """
        Download a CSV template for the named metadata form to allow bulk data input.

        The template is written to a file named ``<form_name>.csv`` in the current working
        directory.  The method searches all forms in the tenancy for one whose title matches
        ``form_name``; if no match is found ``None`` is returned without raising an exception.

        :param form_name: The title of the metadata form for which to download a template.
        :type form_name: str
        :returns: The path to the downloaded CSV file, or ``None`` if no matching form was found.
        :rtype: str or None
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """
        headers = {HEADER_TOKEN: self.token}
        url = f'{self.protocol}://{self.server}/api/metadata/csv-templates/download'

        for form in self.forms():
            if form['title'] == form_name:
                form_id: str = form['id']
                params = {'ids': form_id}
                with self.session.get(url, headers=headers, params=params) as response:
                    if response.status_code == requests.codes.ok:
                        with open(f"{form_name}.csv", mode="wt", encoding="utf-8") as fd:
                            fd.write(response.content.decode("utf-8"))
                            fd.flush()
                            return f"{form_name}.csv"
                    else:
                        exception = HTTPException(None, response.status_code, response.url, "download_template",
                                                  response.content.decode('utf-8'))
                        logger.error(exception)
                        raise exception
        return None

    def delete_group_namespace(self, schema: str):
        """
        Delete a Metadata Group identified by its schema URI.

        Iterates over all groups in the tenancy and deletes the first one whose
        ``schemaUri`` matches the supplied ``schema`` string.  If no group matches,
        the method returns without raising an exception.

        :param schema: The XML namespace / schema URI that uniquely identifies the group.
        :type schema: str
        :returns: None
        :rtype: None
        :raises HTTPException: If the underlying delete API call returns an unexpected HTTP error.
        """
        for group in self.groups():
            if group.schemaUri == schema:
                self.delete_group(group.group_id)

    def delete_group(self, group_id: str):
        """
        Delete a Metadata Group by its unique ID.

        :param group_id: The unique identifier of the group to delete.
        :type group_id: str
        :returns: None
        :rtype: None
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{group_id}'
        with self.session.delete(url, headers=headers) as request:
            if request.status_code == requests.codes.no_content:
                return None
            else:
                exception = HTTPException(None, request.status_code, request.url, "delete_group",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def add_fields(self, group_id: str, new_fields: List[GroupField]) -> dict:
        """
        Append new metadata fields to an existing metadata group.

        The new fields are appended after any fields already present in the group.

        :param group_id: The unique identifier of the group to update.
        :type group_id: str
        :param new_fields: The list of new fields to append to the group.
        :type new_fields: List[GroupField]
        :returns: The updated metadata group as a JSON dictionary.
        :rtype: dict
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """

        this_group: Group = self.group(group_id)

        for field in new_fields:
            this_group.fields.append(field)

        doc = _json_from_object_(this_group)

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{group_id}'
        with self.session.put(url, headers=headers, json=doc) as request:
            if request.status_code == requests.codes.created:
                return json.loads(str(request.content.decode('utf-8')))
            else:
                exception = HTTPException(None, request.status_code, request.url, "add_fields",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def add_group(self, group_name: str, group_description: str, fields: List[GroupField]) -> dict:
        """
        Create a new metadata group with the supplied name, description, and fields.

        :param group_name: The name of the new group.
        :type group_name: str
        :param group_description: A human-readable description of the new group.
        :type group_description: str
        :param fields: The list of ``GroupField`` objects that define the group's schema.
        :type fields: List[GroupField]
        :returns: The newly created metadata group as a JSON dictionary.
        :rtype: dict
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """

        group: Group = Group(group_name, group_description)
        group.fields = fields

        json_document: dict = _json_from_object_(group)
        json_response: dict = self.add_group_json(json_document)
        return json_response

    def update_form(self, form_id: str, json_form: Union[dict, str]):
        """
        Update an existing metadata form using a JSON dictionary or JSON string.

        :param form_id: The unique identifier of the form to update.
        :type form_id: str
        :param json_form: The updated form definition as a JSON-serialisable dict or a
            JSON-encoded string.
        :type json_form: dict or str
        :returns: The updated form as a JSON dictionary.
        :rtype: dict
        :raises RuntimeError: If ``json_form`` is neither a ``dict`` nor a ``str``.
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/forms/{form_id}'

        if isinstance(json_form, dict):
            with self.session.put(url, headers=headers, json=json_form) as request:
                if request.status_code == requests.codes.ok:
                    return json.loads(str(request.content.decode('utf-8')))
                else:
                    exception = HTTPException(None, request.status_code, request.url, "add_form_json",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception

        elif isinstance(json_form, str):
            with self.session.put(url, headers=headers, data=json_form) as request:
                if request.status_code == requests.codes.ok:
                    return json.loads(str(request.content.decode('utf-8')))
                else:
                    exception = HTTPException(None, request.status_code, request.url, "add_form_json",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception
        else:
            raise RuntimeError("Argument must be a JSON dictionary or a JSON str")

    def add_form(self, json_form: Union[dict, str]):
        """
        Create a new metadata form using a JSON dictionary or JSON-encoded string.

        :param json_form: The form definition as a JSON-serialisable dict or a JSON-encoded
            string.
        :type json_form: dict or str
        :returns: The newly created form as a JSON dictionary.
        :rtype: dict
        :raises RuntimeError: If ``json_form`` is neither a ``dict`` nor a ``str``.
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/forms/'

        if isinstance(json_form, dict):
            with self.session.post(url, headers=headers, json=json_form) as request:
                if request.status_code == requests.codes.created:
                    return json.loads(str(request.content.decode('utf-8')))
                else:
                    exception = HTTPException(None, request.status_code, request.url, "add_form_json",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception

        elif isinstance(json_form, str):
            with self.session.post(url, headers=headers, data=json_form) as request:
                if request.status_code == requests.codes.created:
                    return json.loads(str(request.content.decode('utf-8')))
                else:
                    exception = HTTPException(None, request.status_code, request.url, "add_form_json",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception
        else:
            raise RuntimeError("Argument must be a JSON dictionary or a JSON str")


    # def set_default_form(self, form_id: str):
    #     """
    #     Set the default form
    #
    #     """
    #
    #     headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
    #     url = f'{self.protocol}://{self.server}/api/metadata/forms/{form_id}/default'
    #
    #     payload: dict = {"default": True, "useAsDefault": True}
    #
    #     with self.session.get(url, headers=headers, json=json.dumps(payload)) as request:
    #         if request.status_code == requests.codes.ok:
    #             return json.loads(str(request.content.decode('utf-8')))
    #         else:
    #             exception = HTTPException(None, request.status_code, request.url, "set_default_form",
    #                                       request.content.decode('utf-8'))
    #             logger.error(exception)
    #             raise exception




    def add_group_json(self, json_object: Union[dict, str]) -> dict:
        """
        Create a new metadata group using a JSON dictionary or JSON-encoded string.

        :param json_object: The group definition as a JSON-serialisable dict or a JSON-encoded
            string.
        :type json_object: dict or str
        :returns: The newly created metadata group as a JSON dictionary.
        :rtype: dict
        :raises RuntimeError: If ``json_object`` is neither a ``dict`` nor a ``str``.
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/'

        if isinstance(json_object, dict):
            with self.session.post(url, headers=headers, json=json_object) as request:
                if request.status_code == requests.codes.created:
                    return json.loads(str(request.content.decode('utf-8')))
                else:
                    exception = HTTPException(None, request.status_code, request.url, "add_group_json",
                                              request.content.decode('utf-8'))
                    logger.error(exception)
                    raise exception

        elif isinstance(json_object, str):
            with self.session.post(url, headers=headers, data=json_object) as request:
                if request.status_code == requests.codes.created:
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
        Return a metadata group as a raw JSON dictionary.

        :param group_id: The unique identifier of the group to retrieve.
        :type group_id: str
        :returns: The metadata group as a JSON dictionary.
        :rtype: dict
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{group_id}'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.ok:
                return json.loads(str(request.content.decode('utf-8')))
            else:
                exception = HTTPException(None, request.status_code, request.url, "group_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def group(self, group_id: str) -> Group:
        """
        Return a metadata group as a ``Group`` object by its unique ID.

        :param group_id: The unique identifier of the group to retrieve.
        :type group_id: str
        :returns: The metadata group as a ``Group`` object with all fields populated.
        :rtype: Group
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """

        return _object_from_json_(self.group_json(group_id))

    def groups_json(self) -> List[dict]:
        """
        Return all metadata groups in the tenancy as a list of raw JSON dictionaries.

        :returns: A list where each element is a JSON dictionary representing one metadata group.
        :rtype: List[dict]
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.ok:
                return json.loads(str(request.content.decode('utf-8')))['groups']
            else:
                exception = HTTPException(None, request.status_code, request.url, "groups_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def forms(self, schema_uri: Union[str, None] = None) -> dict:
        """
        Return all metadata forms in the tenancy as a list of JSON dictionaries.

        An optional ``schema_uri`` filter limits results to forms associated with a
        specific XML namespace URI.

        :param schema_uri: If provided, only forms whose schema URI matches this value are
            returned.  When ``None`` (the default) all forms are returned.
        :type schema_uri: str or None
        :returns: A list where each element is a JSON dictionary representing one metadata form.
        :rtype: list[dict]
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/forms'
        params = {}
        if schema_uri is not None:
            params = {'schemaUri': schema_uri}
        with self.session.get(url, headers=headers, params=params) as request:
            if request.status_code == requests.codes.ok:
                return json.loads(str(request.content.decode('utf-8')))['metadataForms']
            else:
                exception = HTTPException(None, request.status_code, request.url, "forms_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception


    def delete_form(self, form_id: str):
        """
        Delete a metadata form by its unique ID.

        :param form_id: The unique identifier of the form to delete.
        :type form_id: str
        :returns: None
        :rtype: None
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/forms/{form_id}'
        with self.session.delete(url, headers=headers) as request:
            if request.status_code == requests.codes.no_content:
                return None
            else:
                exception = HTTPException(None, request.status_code, request.url, "delete_form",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception



    def form(self, form_id: str) -> dict:
        """
        Return a metadata form as a JSON dictionary by its unique ID.

        :param form_id: The unique identifier of the form to retrieve.
        :type form_id: str
        :returns: The metadata form as a JSON dictionary.
        :rtype: dict
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/forms/{form_id}'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.ok:
                return json.loads(str(request.content.decode('utf-8')))
            else:
                exception = HTTPException(None, request.status_code, request.url, "form_json",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception



    def groups(self) -> Generator[Group, None, None]:
        """
        Yield all metadata groups in the tenancy as ``Group`` objects.

        :returns: A generator that yields one ``Group`` object per metadata group in the tenancy.
        :rtype: Generator[Group, None, None]
        :raises HTTPException: If the Preservica API returns an unexpected HTTP error status.
        """

        for group in self.groups_json():
            yield _object_from_json_(group)
