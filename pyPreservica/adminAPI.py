"""
pyPreservica AdminAPI module definition

A client library for the Preservica Repository web Administration and Management API
https://us.preservica.com/api/admin/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
import csv
import xml.etree.ElementTree
from typing import List, Any

from pyPreservica.common import *

logger = logging.getLogger(__name__)


class AdminAPI(AuthenticatedAPI):

    def delete_system_role(self, role_name):
        """
        Delete an existing system role from the Preservica tenancy.

        :param role_name: The name of the role to delete.
        :type role_name: str
        :returns: None
        :rtype: None
        :raises RuntimeError: If the Preservica server is below v6.5.0, or if the delete request fails.
        """
        if (self.major_version < 6) or (self.major_version == 6 and self.minor_version < 5):
            raise RuntimeError(
                "delete_system_role API call is only available with a Preservica v6.5.0 system or higher")

        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.delete(f'{self.protocol}://{self.server}/api/admin/security/roles/{role_name}',
                                      headers=headers)
        if request.status_code == requests.codes.no_content:
            return None
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "delete_system_role failed")

    def delete_security_tag(self, tag_name):
        """
        Delete an existing security tag from the Preservica tenancy.

        :param tag_name: The name of the security tag to delete.
        :type tag_name: str
        :returns: None
        :rtype: None
        :raises RuntimeError: If the Preservica server is below v6.4.0, or if the delete request fails.
        """
        if (self.major_version < 6) or (self.major_version == 6 and self.minor_version < 4):
            raise RuntimeError(
                "delete_security_tag API call is only available with a Preservica v6.4.0 system or higher")

        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.delete(f'{self.protocol}://{self.server}/api/admin/security/tags/{tag_name}',
                                      headers=headers)
        if request.status_code == requests.codes.no_content:
            return None
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "delete_security_tag failed")

    def add_system_role(self, role_name) -> str:
        """
        Create a new user access role in the Preservica tenancy.

        :param role_name: The name of the new role to create.
        :type role_name: str
        :returns: The name of the newly created role as confirmed by the server.
        :rtype: str
        :raises RuntimeError: If ``role_name`` is empty, if the Preservica server is below v6.5.0,
            or if the creation request fails.
        """
        self._check_if_user_has_user_manager_role()

        if not role_name:
            raise RuntimeError("Invalid Role Name (Empty)")

        if (self.major_version < 6) or ( (self.major_version == 6) and (self.minor_version < 5) ):
            raise RuntimeError("add_system_role API call is only available with a Preservica v6.5.0 system or higher")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}


        xml_tag = xml.etree.ElementTree.Element('Role', {"xmlns": self.admin_ns})
        xml_tag.text = str(role_name).strip()
        xml_request = xml.etree.ElementTree.tostring(xml_tag, encoding='utf-8')
        request = self.session.post(f'{self.protocol}://{self.server}/api/admin/security/roles', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.created:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            if not entity_response.text:
                raise RuntimeError("add_system_role returned an empty role name")
            return entity_response.text
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_system_role failed")

    def add_security_tag(self, tag_name) -> str:
        """
        Create a new security tag in the Preservica tenancy.

        Security tags are used to control access to repository content.

        :param tag_name: The name of the new security tag to create.
        :type tag_name: str
        :returns: The name of the newly created security tag as confirmed by the server.
        :rtype: str
        :raises RuntimeError: If ``tag_name`` is empty, if the Preservica server is below v6.4.0,
            or if the creation request fails.
        """

        self._check_if_user_has_user_manager_role()

        if not tag_name:
            raise RuntimeError("Invalid Tag Name (Empty)")

        if (self.major_version < 6) or (self.major_version == 6 and self.minor_version < 4):
            raise RuntimeError("add_security_tag API call is only available with a Preservica v6.4.0 system or higher")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        xml_tag = xml.etree.ElementTree.Element('Tag', {"xmlns": self.admin_ns})
        xml_tag.text = str(tag_name).strip()
        xml_request = xml.etree.ElementTree.tostring(xml_tag, encoding='utf-8')

        request = self.session.post(f'{self.protocol}://{self.server}/api/admin/security/tags', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.created:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            if not entity_response.text:
                raise RuntimeError("add_security_tag returned an empty tag name")
            return entity_response.text
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_security_tag failed")

    def system_roles(self) -> list[str]:
        """
        Return a list of all  role names defined in the Preservica tenancy.

        :returns: A list of role name strings.
        :rtype: list[str]
        :raises RuntimeError: If the Preservica server is below v6.5.0, or if the request fails.
        """

        if (self.major_version < 6) or (self.major_version == 6 and self.minor_version < 5):
            raise RuntimeError(
                "system_roles API call is only available with a Preservica v6.5.0 system or higher")

        self._check_if_user_has_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/admin/security/roles', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            roles = entity_response.findall(f'.//{{{self.admin_ns}}}Role')
            return [role.text for role in roles if role.text is not None]
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "system_roles failed")

    def security_tags(self) -> list[str]:
        """
        Return a list of all security tag names defined in the Preservica tenancy.

        :returns: A list of security tag name strings.
        :rtype: list[str]
        :raises RuntimeError: If the request fails.
        """
        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/admin/security/tags', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            tags = entity_response.findall(f'.//{{{self.admin_ns}}}Tag')
            return [tag.text for tag in tags if tag.text is not None]
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "security_tags failed")

    def delete_user(self, username: str):
        """
        Permanently delete a user from the Preservica tenancy.

        The user account is disabled before deletion. This operation cannot be undone.

        :param username: The email address of the user to delete.
        :type username: str
        :returns: None
        :rtype: None
        :raises RuntimeError: If the delete request fails.
        """
        self._check_if_user_has_manager_role()
        self.disable_user(username)
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.delete(f'{self.protocol}://{self.server}/api/admin/users/{username}', headers=headers)
        if request.status_code == requests.codes.no_content:
            return None
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "delete_user failed")

    def add_user(self, username: str, full_name: str, roles: list[str], externally_authenticated: bool = False) -> dict:
        """
        Create a new user account to the Preservica tenancy.

        :param username: The email address of the new user (used as the login username).
        :type username: str
        :param full_name: The full display name of the new user.
        :type full_name: str
        :param roles: A list of role names to assign to the new user.
        :type roles: list[str]
        :param externally_authenticated: If ``True``, the user is authenticated via an external
            identity provider (e.g. LDAP/SSO) rather than Preservica's internal authentication.
            Defaults to ``False``.
        :type externally_authenticated: bool
        :returns: A dictionary of the newly created user's attributes with keys:
            ``UserName``, ``FullName``, ``Email``, ``Tenant``, ``Enabled``, ``Roles``.
        :rtype: dict
        :raises RuntimeError: If the creation request fails.
        """
        self._check_if_user_has_user_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        xml_object = xml.etree.ElementTree.Element('User', {"xmlns": self.admin_ns})
        xml.etree.ElementTree.SubElement(xml_object, "FullName").text = full_name
        xml.etree.ElementTree.SubElement(xml_object, "Email").text = username
        if externally_authenticated:
            xml.etree.ElementTree.SubElement(xml_object, "externallyAuthenticated").text = "true"
            xml.etree.ElementTree.SubElement(xml_object, "userName").text = username
        xml_roles = xml.etree.ElementTree.SubElement(xml_object, "Roles")
        for role in roles:
            xml.etree.ElementTree.SubElement(xml_roles, "Role").text = role
        xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8')
        logger.debug(xml_request)
        params = {"source": "UX2"}
        request = self.session.post(f'{self.protocol}://{self.server}/api/admin/users', data=xml_request,
                                    headers=headers, params=params)
        if request.status_code == requests.codes.created:
            return self.user_details(username)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_user failed")

    def change_user_display_name(self, username: str, new_display_name: str) -> dict:
        """
        Change the full display name of an existing Preservica user.

        :param username: The email address of the user whose display name should be changed.
        :type username: str
        :param new_display_name: The new full display name to assign to the user.
        :type new_display_name: str
        :returns: A dictionary of the updated user's attributes with keys:
            ``UserName``, ``FullName``, ``Email``, ``Tenant``, ``Enabled``, ``Roles``.
        :rtype: dict
        :raises RuntimeError: If fetching or updating the user record fails.
        """
        self._check_if_user_has_user_manager_role()
        
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f"{self.protocol}://{self.server}/api/admin/users/{username}", headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            fullname = entity_response.find(f'.//{{{self.admin_ns}}}FullName')
            fullname.text = new_display_name
            xml_request = xml.etree.ElementTree.tostring(entity_response, encoding='utf-8')
            logger.debug(xml_request)
            update_request = self.session.put(f'{self.protocol}://{self.server}/api/admin/users/{username}',
                                              data=xml_request,
                                              headers=headers)
            if update_request.status_code == requests.codes.ok:
                return self.user_details(username)
            else:
                logger.error(update_request.content.decode('utf-8'))
                raise RuntimeError(update_request.status_code, "change_user_display_name failed")
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "change_user_display_name failed")


    def current_user(self):
        """
        Return details about the currently authenticated  user.

        :returns: A dictionary of the current user's attributes
        :rtype: dict
        :raises RuntimeError: If the request fails.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        request = self.session.get(f"{self.protocol}://{self.server}/api/user/details", headers=headers)
        if request.status_code == requests.codes.ok:
            json_response = str(request.content.decode('utf-8'))
            logger.debug(json_response)
            return json.loads(json_response)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "current_user failed")


    def user_details(self, username: str) -> dict:
        """
        Retrieve the full details of a Preservica user by their email address.

        :param username: The email address of the user to look up.
        :type username: str
        :returns: A dictionary of the user's attributes with keys:
            ``UserName`` (str), ``FullName`` (str), ``Email`` (str),
            ``Tenant`` (str), ``Enabled`` (bool), ``Roles`` (list[str]).
        :rtype: dict
        :raises RuntimeError: If the request fails.
        """

        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f"{self.protocol}://{self.server}/api/admin/users/{username}", headers=headers)
        return_dict = {}
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            user_name = entity_response.find(f'.//{{{self.admin_ns}}}UserName')
            return_dict['UserName'] = user_name.text if user_name is not None else None
            fullname = entity_response.find(f'.//{{{self.admin_ns}}}FullName')
            return_dict['FullName'] = fullname.text if fullname is not None else None
            email = entity_response.find(f'.//{{{self.admin_ns}}}Email')
            return_dict['Email'] = email.text  if email is not None else None
            tenant = entity_response.find(f'.//{{{self.admin_ns}}}Tenant')
            return_dict['Tenant'] = tenant.text if tenant is not None else None
            enable = entity_response.find(f'.//{{{self.admin_ns}}}Enabled')
            if enable is not None:
                return_dict['Enabled'] = bool(enable.text == "true")
            roles = entity_response.findall(f'.//{{{self.admin_ns}}}Role')
            return_dict['Roles'] = [role.text for role in roles if role.text is not None]
            return return_dict
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "user_details failed")

    def _account_status_(self, username: str, status: str, name: str):
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'text/plain;charset=UTF-8'}
        data = {"userEnabledStatus": status}
        request = self.session.put(f"{self.protocol}://{self.server}/api/admin/users/{username}/enabled",
                                   headers=headers,
                                   data=data)
        if request.status_code == requests.codes.ok:
            return request.content.decode("utf-8")
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"{name} failed")

    def disable_user(self, username):
        """
        Disable a Preservica user account to prevent the user from logging in.

        :param username: The email address of the user to disable.
        :type username: str
        :returns: The server response body as a string.
        :rtype: str
        :raises RuntimeError: If the request fails.
        """
        self._check_if_user_has_manager_role()
        return self._account_status_(username, "false", "disable_user")

    def enable_user(self, username):
        """
        Enable a previously disabled Preservica user account.

        :param username: The email address of the user to enable.
        :type username: str
        :returns: The server response body as a string.
        :rtype: str
        :raises RuntimeError: If the request fails.
        """
        self._check_if_user_has_manager_role()
        return self._account_status_(username, "true", "enable_user")

    def user_report(self, report_name="users.csv"):
        """
        Write a CSV report of all users in the Preservica tenancy to a file.

        The report contains one row per user with the following columns:
        ``UserName``, ``FullName``, ``Email``, ``Tenant``, ``Enabled``, ``Roles``.

        :param report_name: The file path to write the CSV report to.
            Defaults to ``"users.csv"`` in the current working directory.
        :type report_name: str
        :returns: None
        :rtype: None
        :raises RuntimeError: If any underlying user detail request fails.
        """

        self._check_if_user_has_manager_role()

        fieldnames = ['UserName', 'FullName', 'Email', 'Tenant', 'Enabled', 'Roles']

        with open(report_name, newline='', mode="wt", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for username in self.all_users():
                user_details = self.user_details(username)
                writer.writerow(user_details)

    def all_users(self) -> list[str]:
        """
        Return a list of all user email addresses registered in the Preservica tenancy.

        :returns: A list of username strings, each being the email address of a registered user.
        :rtype: list[str]
        :raises RuntimeError: If the request fails.
        """

        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f"{self.protocol}://{self.server}/api/admin/users", headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            users = entity_response.findall(f'.//{{{self.admin_ns}}}User')
            return [user.text for user in users if user.text is not None]
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "all_users failed")

    def add_xml_schema(self, name: str, description: str, originalName: str, xml_data: Any):
        """
        Upload a new XSD schema document to the Preservica schema store.

        :param name: The display name for the XSD schema within Preservica.
        :type name: str
        :param description: A human-readable description of the XSD schema.
        :type description: str
        :param originalName: The original filename of the schema file on disk (e.g. ``"my-schema.xsd"``).
        :type originalName: str
        :param xml_data: The XSD schema content, either as a UTF-8 encoded string or as a
            file-like object opened in binary mode.
        :type xml_data: str or file-like object
        :returns: None
        :rtype: None
        :raises RuntimeError: If the upload request fails.
        """

        self._check_if_user_has_config_manager_role()

        params = {"name": name, "description": description, "originalName": originalName}

        if isinstance(xml_data, str):
            xml.etree.ElementTree.fromstring(xml_data)
            xml_data = xml_data.encode("utf-8")
        elif hasattr(xml_data, "read"):
            pass

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.post(f"{self.protocol}://{self.server}/api/admin/schemas", headers=headers,
                                    params=params,
                                    data=xml_data)
        if request.status_code == requests.codes.created:
            return None
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_xml_schema failed")

    def add_xml_document(self, name: str, xml_data: Any, document_type: str = "MetadataTemplate"):
        """
        Upload a new XML document to the Preservica XML document store.

        The default document type is a descriptive metadata template. Supported
        ``document_type`` values are:

        - ``"MetadataDropdownLists"`` — Authority Lists
        - ``"CustomIndexDefinition"`` — Custom Search Indexes
        - ``"MetadataTemplate"`` — Descriptive Metadata Template (default)
        - ``"UploadWizardConfigurationFile"`` — Upload Wizard Configuration
        - ``"ConfigurationFile"`` — Heritrix Crawler Configuration File

        :param name: The display name for the XML document within Preservica.
        :type name: str
        :param xml_data: The XML document content, either as a UTF-8 encoded string or as a
            file-like object opened in binary mode.
        :type xml_data: str or file-like object
        :param document_type: The document type identifier. Defaults to ``"MetadataTemplate"``.
        :type document_type: str
        :returns: None
        :rtype: None
        :raises RuntimeError: If the upload request fails.
        """

        self._check_if_user_has_config_manager_role()

        params = {"name": name, "type": document_type}

        if isinstance(xml_data, str):
            xml.etree.ElementTree.fromstring(xml_data)
            xml_data = xml_data.encode("utf-8")
        elif hasattr(xml_data, "read"):
            pass

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.post(f"{self.protocol}://{self.server}/api/admin/documents", headers=headers,
                                    params=params,
                                    data=xml_data)
        if request.status_code == requests.codes.created:
            return None
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_xml_document failed")

    def delete_xml_document(self, uri: str):
        """
        Delete an XML document from Preservica's XML document store by its schema URI.

        If no document with the given URI is found, the method returns without error.

        :param uri: The schema URI of the XML document to delete (as returned in the
            ``SchemaUri`` key from :meth:`xml_documents`).
        :type uri: str
        :returns: None
        :rtype: None
        :raises RuntimeError: If a matching document is found but the delete request fails.
        """

        self._check_if_user_has_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        for document in self.xml_documents():
            if document['SchemaUri'] == uri.strip():
                request = self.session.delete(
                    f"{self.protocol}://{self.server}/api/admin/documents/{document['ApiId']}",
                    headers=headers)
                if request.status_code == requests.codes.no_content:
                    return None
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "delete_xml_document failed")
        return None

    def delete_xml_schema(self, uri: str):
        """
        Delete an XSD schema document from Preservica by its schema URI.

        If no schema with the given URI is found, the method returns without error.

        :param uri: The schema URI of the XSD document to delete (as returned in the
            ``SchemaUri`` key from :meth:`xml_schemas`).
        :type uri: str
        :returns: None
        :rtype: None
        :raises RuntimeError: If a matching schema is found but the delete request fails.
        """

        self._check_if_user_has_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        for schema in self.xml_schemas():
            if schema['SchemaUri'] == uri.strip():
                request = self.session.delete(f"{self.protocol}://{self.server}/api/admin/schemas/{schema['ApiId']}",
                                              headers=headers)
                if request.status_code == requests.codes.no_content:
                    return None
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "delete_xml_schema failed")
        return None

    def xml_schema(self, uri: str) -> str | None:
        """
        Fetch the content of an XSD schema document stored in Preservica by its URI.

        :param uri: The schema URI of the XSD document to fetch (as returned in the
            ``SchemaUri`` key from :meth:`xml_schemas`).
        :type uri: str
        :returns: The XSD schema content as a UTF-8 string, or ``None`` if no schema
            with the given URI exists.
        :rtype: str or None
        :raises RuntimeError: If a matching schema is found but the content fetch fails.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        for schema in self.xml_schemas():
            if schema['SchemaUri'] == uri.strip():
                request = self.session.get(
                    f"{self.protocol}://{self.server}/api/admin/schemas/{schema['ApiId']}/content",
                    headers=headers)
                if request.status_code == requests.codes.ok:
                    xml_response = str(request.content.decode('utf-8'))
                    return xml_response
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "xml_schema failed")
        return None

    def xml_document(self, uri: str) -> str | None:
        """
        Fetch the content of an XML document stored in Preservica by its URI.

        :param uri: The schema URI of the XML document to fetch (as returned in the
            ``SchemaUri`` key from :meth:`xml_documents`).
        :type uri: str
        :returns: The XML document content as a UTF-8 string, or ``None`` if no document
            with the given URI exists.
        :rtype: str or None
        :raises RuntimeError: If a matching document is found but the content fetch fails.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        for document in self.xml_documents():
            if document['SchemaUri'] == uri.strip():
                request = self.session.get(
                    f"{self.protocol}://{self.server}/api/admin/documents/{document['ApiId']}/content",
                    headers=headers)
                if request.status_code == requests.codes.ok:
                    xml_response = str(request.content.decode('utf-8'))
                    return xml_response
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "xml_document failed")
        return None

    def xml_documents(self) -> List:
        """
        Return a list of all XML documents stored in the Preservica XML document store.

        :returns: A list of dictionaries, one per document. Each dictionary contains:
            ``SchemaUri`` (str), ``Name`` (str), ``DocumentType`` (str), ``ApiId`` (str).
        :rtype: list[dict]
        :raises RuntimeError: If the request fails.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/admin/documents', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            documents = entity_response.findall(f'.//{{{self.admin_ns}}}Document')
            results = list()
            for document in documents:
                document_dict = {}
                api_id = document.find(f'.//{{{self.admin_ns}}}ApiId')
                name = document.find(f'.//{{{self.admin_ns}}}Name')
                document_type = document.find(f'.//{{{self.admin_ns}}}DocumentType')
                schema_uri = document.find(f'.//{{{self.admin_ns}}}SchemaUri')
                document_dict['SchemaUri'] = schema_uri.text   if schema_uri is not None else None
                document_dict['Name'] = name.text   if name is not None else None
                document_dict['DocumentType'] = document_type.text if document_type is not None else None
                document_dict['ApiId'] = api_id.text if api_id is not None else None
                results.append(document_dict)
            return results
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "xml_documents failed")

    def xml_schemas(self) -> List:
        """
        Return a list of all XSD schema documents stored in the Preservica schema store.

        :returns: A list of dictionaries, one per schema. Each dictionary contains:
            ``SchemaUri`` (str), ``Name`` (str), ``Description`` (str), ``ApiId`` (str).
        :rtype: list[dict]
        :raises RuntimeError: If the request fails.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        request = self.session.get(f'{self.protocol}://{self.server}/api/admin/schemas', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            schemas = entity_response.findall(f'.//{{{self.admin_ns}}}Schema')
            results = []
            for schema in schemas:
                schema_dict = {}
                schema_uri = schema.find(f'.//{{{self.admin_ns}}}SchemaUri')
                name = schema.find(f'.//{{{self.admin_ns}}}Name')
                description = schema.find(f'.//{{{self.admin_ns}}}Description')
                aip_id = schema.find(f'.//{{{self.admin_ns}}}ApiId')
                schema_dict['SchemaUri'] = schema_uri.text  if schema_uri is not None else None
                schema_dict['Name'] = name.text  if name is not None else None
                if description is not None:
                    schema_dict['Description'] = description.text
                else:
                    schema_dict['Description'] = ""
                schema_dict['ApiId'] = aip_id.text   if aip_id is not None else None
                results.append(schema_dict)
            return results
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "xml_schemas failed")

    def xml_transforms(self) -> List:
        """
        Return a list of all XSLT transforms stored in the Preservica transform store.

        :returns: A list of dictionaries, one per transform. Each dictionary contains:
            ``FromSchemaUri`` (str), ``ToSchemaUri`` (str), ``Name`` (str),
            ``Purpose`` (str), ``ApiId`` (str).
        :rtype: list[dict]
        :raises RuntimeError: If the request fails.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/admin/transforms', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            transforms = entity_response.findall(f'.//{{{self.admin_ns}}}Transform')
            results = []
            for transform in transforms:
                transform_dict = {}
                to_schema_uri = transform.find(f'.//{{{self.admin_ns}}}ToSchemaUri')
                from_schema_uri = transform.find(f'.//{{{self.admin_ns}}}FromSchemaUri')
                name = transform.find(f'.//{{{self.admin_ns}}}Name')
                purpose = transform.find(f'.//{{{self.admin_ns}}}Purpose')
                aip_id = transform.find(f'.//{{{self.admin_ns}}}ApiId')
                if to_schema_uri is not None:
                    transform_dict['ToSchemaUri'] = to_schema_uri.text
                else:
                    transform_dict['ToSchemaUri'] = ""
                if from_schema_uri is not None:
                    transform_dict['FromSchemaUri'] = from_schema_uri.text
                else:
                    transform_dict['FromSchemaUri'] = ""

                transform_dict['Name'] = name.text    if name is not None else None
                transform_dict['Purpose'] = purpose.text  if purpose is not None else None
                transform_dict['ApiId'] = aip_id.text  if aip_id is not None else None
                results.append(transform_dict)
            return results
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "xml_transforms failed")

    def xml_transform(self, input_uri: str, output_uri: str) -> str | None:
        """
        Fetch the content of an XSLT transform stored in Preservica by its input and output URIs.

        :param input_uri: The ``FromSchemaUri`` of the transform to fetch — the URI of the
            input XML schema that the transform accepts.
        :type input_uri: str
        :param output_uri: The ``ToSchemaUri`` of the transform to fetch — the URI of the
            output XML schema that the transform produces.
        :type output_uri: str
        :returns: The XSLT transform content as a UTF-8 string, or ``None`` if no transform
            matching both URIs exists.
        :rtype: str or None
        :raises RuntimeError: If a matching transform is found but the content fetch fails.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        for transform in self.xml_transforms():
            if (transform['FromSchemaUri'] == input_uri.strip()) and (transform['ToSchemaUri'] == output_uri.strip()):
                request = self.session.get(
                    f"{self.protocol}://{self.server}/api/admin/transforms/{transform['ApiId']}/content",
                    headers=headers)
                if request.status_code == requests.codes.ok:
                    return str(request.content.decode('utf-8'))
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "xml_transform failed")
        return None

    def delete_xml_transform(self, input_uri: str, output_uri: str):
        """
        Delete an XSLT transform from Preservica by its input and output schema URIs.

        If no transform matching both URIs is found, the method returns without error.

        :param input_uri: The ``FromSchemaUri`` of the transform to delete — the URI of the
            input XML schema that the transform accepts.
        :type input_uri: str
        :param output_uri: The ``ToSchemaUri`` of the transform to delete — the URI of the
            output XML schema that the transform produces.
        :type output_uri: str
        :returns: None
        :rtype: None
        :raises RuntimeError: If a matching transform is found but the delete request fails.
        """

        self._check_if_user_has_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        for transform in self.xml_transforms():
            if (transform['FromSchemaUri'] == input_uri.strip()) and (transform['ToSchemaUri'] == output_uri.strip()):
                request = self.session.delete(
                    f"{self.protocol}://{self.server}/api/admin/transforms/{transform['ApiId']}",
                    headers=headers)
                if request.status_code == requests.codes.no_content:
                    return None
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "delete_xml_transform failed")
        return None

    def add_xml_transform(self, name: str, input_uri: str, output_uri: str, purpose: str, originalName: str,
                          xml_data: Any):
        """
        Upload a new XSLT transform document to the Preservica transform store.

        :param name: The display name for the XSLT transform within Preservica.
        :type name: str
        :param input_uri: The schema URI of the input (source) XML format that the transform accepts.
        :type input_uri: str
        :param output_uri: The schema URI of the output (target) XML format that the transform produces.
        :type output_uri: str
        :param purpose: The intended use of the transform. Accepted values are
            ``"transform"`` (format conversion), ``"edit"`` (in-place editing), or ``"view"``
            (rendering/display). The value is lowercased before submission.
        :type purpose: str
        :param originalName: The original filename of the XSLT file on disk (e.g. ``"my-transform.xslt"``).
        :type originalName: str
        :param xml_data: The XSLT transform content, either as a UTF-8 encoded string or as a
            file-like object opened in binary mode.
        :type xml_data: str or file-like object
        :returns: None
        :rtype: None
        :raises RuntimeError: If the upload request fails.
        """

        self._check_if_user_has_config_manager_role()

        params = {"name": name, "from": input_uri, "to": output_uri, "purpose": purpose.lower(),
                  "originalName": originalName}

        if isinstance(xml_data, str):
            xml.etree.ElementTree.fromstring(xml_data)
            xml_data = xml_data.encode("utf-8")
        elif hasattr(xml_data, "read"):
            pass

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.post(f"{self.protocol}://{self.server}/api/admin/transforms", headers=headers,
                                    params=params,
                                    data=xml_data)
        if request.status_code == requests.codes.created:
            return None
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_xml_transform failed")
