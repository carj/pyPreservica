"""
pyPreservica Preservation Action Registry module definition

A client library for the Preservica PAR API
https://us.preservica.com/Registry/par/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
from typing import AnyStr

from requests.auth import HTTPBasicAuth

from pyPreservica.common import *


def __get_contents__(document) -> AnyStr:
    try:
        with open(document, "rb") as f:
            return f.read()
    except (OSError, TypeError):
        return json.dumps(json.loads(document))


class PreservationActionRegistry(AuthenticatedAPI):

    def format_family(self, guid: str) -> str:
        """
        Retrieve a single format family record by its GUID.

        :param guid: The unique identifier (GUID) of the format family to retrieve.
        :type guid: str
        :returns: The format family record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(guid, "format-families")

    def format_families(self) -> str:
        """
        Retrieve all format family records from the registry.

        :returns: A JSON-encoded string containing all format family records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("format-families")

    def add_format_family(self, document) -> str:
        """
        Create a new format family record in the registry.

        :param document: The format family definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created format family record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("format-families", document)

    def update_format_family(self, guid: str, document) -> str:
        """
        Update an existing format family record in the registry.

        :param guid: The unique identifier (GUID) of the format family to update.
        :type guid: str
        :param document: The updated format family definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated format family record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "format-families", document)

    def delete_format_family(self, guid) -> str:
        """
        Delete a format family record from the registry.

        :param guid: The unique identifier (GUID) of the format family to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "format-families")

    def preservation_action_type(self, guid: str) -> str:
        """
        Retrieve a single preservation action type record by its GUID.

        :param guid: The unique identifier (GUID) of the preservation action type to retrieve.
        :type guid: str
        :returns: The preservation action type record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(guid, "preservation-action-types")

    def preservation_action_types(self) -> str:
        """
        Retrieve all preservation action type records from the registry.

        :returns: A JSON-encoded string containing all preservation action type records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("preservation-action-types")

    def add_preservation_action_type(self, document) -> str:
        """
        Create a new preservation action type record in the registry.

        :param document: The preservation action type definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created preservation action type record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("preservation-action-types", document)

    def update_preservation_action_type(self, guid: str, document) -> str:
        """
        Update an existing preservation action type record in the registry.

        :param guid: The unique identifier (GUID) of the preservation action type to update.
        :type guid: str
        :param document: The updated preservation action type definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated preservation action type record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "preservation-action-types", document)

    def delete_preservation_action_type(self, guid) -> str:
        """
        Delete a preservation action type record from the registry.

        :param guid: The unique identifier (GUID) of the preservation action type to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "preservation-action-types")

    def property(self, guid: str) -> str:
        """
        Retrieve a single property record by its GUID.

        :param guid: The unique identifier (GUID) of the property to retrieve.
        :type guid: str
        :returns: The property record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(guid, "properties")

    def properties(self) -> str:
        """
        Retrieve all property records from the registry.

        :returns: A JSON-encoded string containing all property records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("properties")

    def add_property(self, document) -> str:
        """
        Create a new property record in the registry.

        :param document: The property definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created property record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("properties", document)

    def update_property(self, guid: str, document) -> str:
        """
        Update an existing property record in the registry.

        :param guid: The unique identifier (GUID) of the property to update.
        :type guid: str
        :param document: The updated property definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated property record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "properties", document)

    def delete_property(self, guid) -> str:
        """
        Delete a property record from the registry.

        :param guid: The unique identifier (GUID) of the property to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "properties")

    def representation_format(self, guid: str) -> str:
        """
        Retrieve a single representation format record by its GUID.

        :param guid: The unique identifier (GUID) of the representation format to retrieve.
        :type guid: str
        :returns: The representation format record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(guid, "representation-formats")

    def representation_formats(self) -> str:
        """
        Retrieve all representation format records from the registry.

        :returns: A JSON-encoded string containing all representation format records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("representation-formats")

    def add_representation_format(self, document) -> str:
        """
        Create a new representation format record in the registry.

        :param document: The representation format definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created representation format record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("representation-formats", document)

    def update_representation_format(self, guid: str, document) -> str:
        """
        Update an existing representation format record in the registry.

        :param guid: The unique identifier (GUID) of the representation format to update.
        :type guid: str
        :param document: The updated representation format definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated representation format record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "representation-formats", document)

    def delete_representation_format(self, guid) -> str:
        """
        Delete a representation format record from the registry.

        :param guid: The unique identifier (GUID) of the representation format to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "representation-formats")

    def file_format(self, puid: str) -> str:
        """
        Retrieve a single file format record by its PRONOM Unique Identifier (PUID).

        :param puid: The PRONOM Unique Identifier (PUID) of the file format to retrieve
            (e.g. ``fmt/14`` for PDF 1.0).
        :type puid: str
        :returns: The file format record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(puid, "file-formats")

    def file_formats(self) -> str:
        """
        Retrieve all file format records from the registry.

        :returns: A JSON-encoded string containing all file format records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("file-formats")

    def add_file_format(self, document) -> str:
        """
        Create a new file format record in the registry.

        :param document: The file format definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created file format record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("file-formats", document)

    def update_file_format(self, guid: str, document) -> str:
        """
        Update an existing file format record in the registry.

        :param guid: The unique identifier (GUID) of the file format to update.
        :type guid: str
        :param document: The updated file format definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated file format record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "file-formats", document)

    def delete_file_format(self, guid) -> str:
        """
        Delete a file format record from the registry.

        :param guid: The unique identifier (GUID) of the file format to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "file-formats")

    def tool(self, guid: str) -> str:
        """
        Retrieve a single tool record by its GUID.

        :param guid: The unique identifier (GUID) of the tool to retrieve.
        :type guid: str
        :returns: The tool record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(guid, "tools")

    def tools(self) -> str:
        """
        Retrieve all tool records from the registry.

        :returns: A JSON-encoded string containing all tool records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("tools")

    def add_tool(self, document) -> str:
        """
        Create a new tool record in the registry.

        :param document: The tool definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created tool record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("tools", document)

    def update_tool(self, guid: str, document) -> str:
        """
        Update an existing tool record in the registry.

        :param guid: The unique identifier (GUID) of the tool to update.
        :type guid: str
        :param document: The updated tool definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated tool record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "tools", document)

    def delete_tool(self, guid) -> str:
        """
        Delete a tool record from the registry.

        :param guid: The unique identifier (GUID) of the tool to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "tools")

    def preservation_action(self, guid: str) -> str:
        """
        Retrieve a single preservation action record by its GUID.

        :param guid: The unique identifier (GUID) of the preservation action to retrieve.
        :type guid: str
        :returns: The preservation action record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(guid, "preservation-actions")

    def preservation_actions(self) -> str:
        """
        Retrieve all preservation action records from the registry.

        :returns: A JSON-encoded string containing all preservation action records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("preservation-actions")

    def add_preservation_action(self, document) -> str:
        """
        Create a new preservation action record in the registry.

        :param document: The preservation action definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created preservation action record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("preservation-actions", document)

    def update_preservation_action(self, guid: str, document) -> str:
        """
        Update an existing preservation action record in the registry.

        :param guid: The unique identifier (GUID) of the preservation action to update.
        :type guid: str
        :param document: The updated preservation action definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated preservation action record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "preservation-actions", document)

    def delete_preservation_action(self, guid) -> str:
        """
        Delete a preservation action record from the registry.

        :param guid: The unique identifier (GUID) of the preservation action to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "preservation-actions")

    def business_rule(self, guid: str) -> str:
        """
        Retrieve a single business rule record by its GUID.

        :param guid: The unique identifier (GUID) of the business rule to retrieve.
        :type guid: str
        :returns: The business rule record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(guid, "business-rules")

    def business_rules(self, action_type: str = None) -> str:
        """
        Retrieve all business rule records from the registry, optionally filtered by action type.

        :param action_type: An optional preservation action type identifier used to filter
            the returned business rules. When provided, it is sent as the
            ``preservation-action-type`` request header. Defaults to ``None`` (no filter).
        :type action_type: str, optional
        :returns: A JSON-encoded string containing the matching business rule records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("business-rules", action_type)

    def add_business_rule(self, document) -> str:
        """
        Create a new business rule record in the registry.

        :param document: The business rule definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created business rule record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("business-rules", document)

    def update_business_rule(self, guid: str, document) -> str:
        """
        Update an existing business rule record in the registry.

        :param guid: The unique identifier (GUID) of the business rule to update.
        :type guid: str
        :param document: The updated business rule definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated business rule record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "business-rules", document)

    def delete_business_rule(self, guid) -> str:
        """
        Delete a business rule record from the registry.

        :param guid: The unique identifier (GUID) of the business rule to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "business-rules")

    def rule_set(self, guid: str) -> str:
        """
        Retrieve a single rule set record by its GUID.

        :param guid: The unique identifier (GUID) of the rule set to retrieve.
        :type guid: str
        :returns: The rule set record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__guid__(guid, "rulesets")

    def rule_sets(self) -> str:
        """
        Retrieve all rule set records from the registry.

        :returns: A JSON-encoded string containing all rule set records.
        :rtype: str
        :raises RuntimeError: If the API request fails (non-200 response).
        """
        return self.__all_("rulesets")

    def add_rule_set(self, document) -> str:
        """
        Create a new rule set record in the registry.

        :param document: The rule set definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created rule set record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__add__("rulesets", document)

    def update_rule_set(self, guid: str, document) -> str:
        """
        Update an existing rule set record in the registry.

        :param guid: The unique identifier (GUID) of the rule set to update.
        :type guid: str
        :param document: The updated rule set definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated rule set record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__update__(guid, "rulesets", document)

    def delete_rule_set(self, guid) -> str:
        """
        Delete a rule set record from the registry.

        :param guid: The unique identifier (GUID) of the rule set to delete.
        :type guid: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the API request fails.
        """
        return self.__delete__(guid, "rulesets")

    def __guid__(self, guid: str, endpoint: str) -> str:
        """
        Retrieve a single PAR registry record by GUID from the given endpoint.

        Issues an HTTP GET to ``/Registry/par/{endpoint}/{guid}`` and returns the
        response body decoded as a UTF-8 string.

        :param guid: The unique identifier of the record to retrieve.
        :type guid: str
        :param endpoint: The PAR API endpoint path segment (e.g. ``"format-families"``).
        :type endpoint: str
        :returns: The registry record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If the server returns a non-200 status code.
        """
        request = self.session.get(f'{self.protocol}://{self.server}/Registry/par/{endpoint}/{guid}')
        if request.status_code == requests.codes.ok:
            return request.content.decode('utf-8')
        else:
            logger.debug(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"{endpoint} failed")

    def __all_(self, endpoint: str, action_type: str = None) -> str:
        """
        Retrieve all PAR registry records from the given endpoint.

        Issues an HTTP GET to ``/Registry/par/{endpoint}`` and returns the response
        body decoded as a UTF-8 string. When ``action_type`` is provided it is
        forwarded as the ``preservation-action-type`` request header to filter results.

        :param endpoint: The PAR API endpoint path segment (e.g. ``"business-rules"``).
        :type endpoint: str
        :param action_type: An optional preservation action type identifier used to filter
            results. Defaults to ``None`` (no filter applied).
        :type action_type: str, optional
        :returns: A JSON-encoded string containing all matching registry records.
        :rtype: str
        :raises RuntimeError: If the server returns a non-200 status code.
        """
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if action_type is not None:
            headers['preservation-action-type'] = action_type
        request = self.session.get(f'{self.protocol}://{self.server}/Registry/par/{endpoint}')
        if request.status_code == requests.codes.ok:
            return request.content.decode('utf-8')
        else:
            logger.debug(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"{endpoint} failed")

    def __add__(self, endpoint: str, document) -> str:
        """
        Create a new PAR registry record at the given endpoint.

        Issues an authenticated HTTP POST to ``/Registry/par/{endpoint}`` with the
        JSON body read from ``document``. Credentials (username and password) are
        required; the call raises ``RuntimeError`` immediately if they are absent.

        :param endpoint: The PAR API endpoint path segment (e.g. ``"tools"``).
        :type endpoint: str
        :param document: The record definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The newly created registry record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the server returns
            a non-201 status code.
        """
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if self.username is None or self.password is None:
            logger.error(f"add {endpoint} is an authenticated call, please provide credentials")
            raise RuntimeError(f"add {endpoint}  is an authenticated call, please provide credentials")

        contents = __get_contents__(document)
        request = self.session.post(f'{self.protocol}://{self.server}/Registry/par/{endpoint}',
                                    auth=HTTPBasicAuth(self.username, self.password), headers=headers, data=contents)

        if request.status_code == requests.codes.created:
            return request.content.decode('utf-8')
        else:
            logger.debug(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"add {endpoint} failed")

    def __update__(self, guid: str, endpoint: str, document) -> str:
        """
        Update an existing PAR registry record at the given endpoint.

        Issues an authenticated HTTP PUT to ``/Registry/par/{endpoint}/{guid}`` with
        the JSON body read from ``document``. Credentials (username and password) are
        required; the call raises ``RuntimeError`` immediately if they are absent.

        :param guid: The unique identifier of the record to update.
        :type guid: str
        :param endpoint: The PAR API endpoint path segment (e.g. ``"tools"``).
        :type endpoint: str
        :param document: The updated record definition, either as a path to a JSON file
            or a JSON-encoded string.
        :type document: str
        :returns: The updated registry record as a JSON-encoded string.
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the server returns
            a non-201 status code.
        """
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if self.username is None or self.password is None:
            logger.error(f"update {endpoint} is an authenticated call, please provide credentials")
            raise RuntimeError(f"update {endpoint}  is an authenticated call, please provide credentials")

        contents = __get_contents__(document)

        request = self.session.put(f'{self.protocol}://{self.server}/Registry/par/{endpoint}/{guid}',
                                   auth=HTTPBasicAuth(self.username, self.password), headers=headers, data=contents)

        if request.status_code == requests.codes.created:
            return request.content.decode('utf-8')
        else:
            logger.debug(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"update {endpoint} failed")

    def __delete__(self, guid: str, endpoint: str) -> str:
        """
        Delete a PAR registry record from the given endpoint.

        Issues an authenticated HTTP DELETE to ``/Registry/par/{endpoint}/{guid}``.
        Credentials (username and password) are required; the call raises
        ``RuntimeError`` immediately if they are absent.

        :param guid: The unique identifier of the record to delete.
        :type guid: str
        :param endpoint: The PAR API endpoint path segment (e.g. ``"tools"``).
        :type endpoint: str
        :returns: An empty string on successful deletion (HTTP 204 No Content).
        :rtype: str
        :raises RuntimeError: If credentials are not provided or the server returns
            a non-204 status code.
        """
        if self.username is None or self.password is None:
            logger.error(f"delete {endpoint} is an authenticated call, please provide credentials")
            raise RuntimeError(f"delete {endpoint}  is an authenticated call, please provide credentials")

        request = self.session.delete(f'{self.protocol}://{self.server}/Registry/par/{endpoint}/{guid}',
                                      auth=HTTPBasicAuth(self.username, self.password))
        if request.status_code == requests.codes.no_content:
            return request.content.decode('utf-8')
        else:
            logger.debug(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"delete {endpoint} failed")
