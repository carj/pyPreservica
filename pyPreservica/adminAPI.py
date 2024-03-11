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
        Delete a system role

        :param role_name: The role to delete
        :type role_name: str

        """
        if (self.major_version < 7) and (self.minor_version < 5):
            raise RuntimeError(
                "delete_system_role API call is only available with a Preservica v6.5.0 system or higher")

        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.delete(f'{self.protocol}://{self.server}/api/admin/security/roles/{role_name}',
                                      headers=headers)
        if request.status_code == requests.codes.no_content:
            return
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.delete_system_role(role_name)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "delete_system_role failed")

    def delete_security_tag(self, tag_name):
        """
        Delete a security tag

        :param tag_name: The security tag to delete
        :type tag_name: str

        """
        if (self.major_version < 7) and (self.minor_version < 4):
            raise RuntimeError(
                "delete_security_tag API call is only available with a Preservica v6.4.0 system or higher")

        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.delete(f'{self.protocol}://{self.server}/api/admin/security/tags/{tag_name}',
                                      headers=headers)
        if request.status_code == requests.codes.no_content:
            return
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.delete_security_tag(tag_name)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "delete_security_tag failed")

    def add_system_role(self, role_name) -> str:
        """
        Create a new user roles

        :param role_name: The new role
        :type role_name: str

        :return: The new role
        :rtype: str

        """
        if (self.major_version < 7) and (self.minor_version < 5):
            raise RuntimeError("add_system_role API call is only available with a Preservica v6.5.0 system or higher")

        self._check_if_user_has_manager_role()
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
            return entity_response.text
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_system_role(role_name)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_system_role failed")

    def add_security_tag(self, tag_name) -> str:
        """
        Create a new security tag

        :param tag_name: The new security tag
        :type tag_name: str

        :return: The new security tag
        :rtype: str

        """

        if (self.major_version < 7) and (self.minor_version < 4):
            raise RuntimeError("add_security_tag API call is only available with a Preservica v6.4.0 system or higher")

        self._check_if_user_has_manager_role()
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
            return entity_response.text
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_security_tag(tag_name)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_security_tag failed")

    def system_roles(self) -> list:
        """
        List all the user access roles in the system

        :return: list of roles
        :rtype: list

        """
        self._check_if_user_has_manager_role()

        if (self.major_version < 7) and (self.minor_version < 5):
            raise RuntimeError(
                "system_roles API call is only available with a Preservica v6.5.0 system or higher")

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/admin/security/roles', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            roles = entity_response.findall(f'.//{{{self.admin_ns}}}Role')
            security_roles = []
            for role in roles:
                security_roles.append(role.text)
            return security_roles
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.roles()
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "roles failed")

    def security_tags(self) -> list:
        """
        List all the security tags in the system

        :return: list of security tags
        :rtype: list

        """
        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/admin/security/tags', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            tags = entity_response.findall(f'.//{{{self.admin_ns}}}Tag')
            security_tags = []
            for tag in tags:
                security_tags.append(tag.text)
            return security_tags
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.security_tags()
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "security_tags failed")

    def delete_user(self, username: str):
        """
        Delete a user

        :param username: email address of the preservica user
        :type username: str

        """
        self._check_if_user_has_manager_role()
        self.disable_user(username)
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.delete(f'{self.protocol}://{self.server}/api/admin/users/{username}', headers=headers)
        if request.status_code == requests.codes.no_content:
            return
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.delete_user(username)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "delete_user failed")

    def add_user(self, username: str, full_name: str, roles: list, externally_authenticated: bool = False):
        """
        Add a new user

        :param externally_authenticated:

        :param username: email address of the preservica user
        :type username: str

        :param full_name: Users real name
        :type full_name: str

        :param roles: List of roles assigned to the user
        :type roles: list

        :return: dictionary of user attributes
        :rtype: dict
        """
        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        xml_object = xml.etree.ElementTree.Element('User ', {"xmlns": self.admin_ns})
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
        request = self.session.post(f'{self.protocol}://{self.server}/api/admin/users', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.created:
            return self.user_details(username)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_user(username, full_name, roles)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_user failed")

    def change_user_display_name(self, username: str, new_display_name: str) -> dict:
        """
         Change the user display name

         :param username: email address of the preservica user
         :type username: str

         :param new_display_name: Users real name
         :type new_display_name: str

         :return: dictionary of user attributes
         :rtype: dict
         """
        self._check_if_user_has_manager_role()
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
            elif update_request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.change_user_display_name(username, new_display_name)
            else:
                logger.error(request.content.decode('utf-8'))
                raise RuntimeError(request.status_code, "change_user_display_name failed")
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.change_user_display_name(username, new_display_name)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "change_user_display_name failed")

    def user_details(self, username: str) -> dict:
        """
        Get the details of a user by their username

        :param username: email address of the preservica user
        :type username: str

        :return: dictionary of user attributes
        :rtype: dict
        """

        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f"{self.protocol}://{self.server}/api/admin/users/{username}", headers=headers)
        return_dict = {}
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            username = entity_response.find(f'.//{{{self.admin_ns}}}UserName')
            return_dict['UserName'] = username.text
            fullname = entity_response.find(f'.//{{{self.admin_ns}}}FullName')
            return_dict['FullName'] = fullname.text
            email = entity_response.find(f'.//{{{self.admin_ns}}}Email')
            return_dict['Email'] = email.text
            tenant = entity_response.find(f'.//{{{self.admin_ns}}}Tenant')
            return_dict['Tenant'] = tenant.text
            enable = entity_response.find(f'.//{{{self.admin_ns}}}Enabled')
            return_dict['Enabled'] = bool(enable.text == "true")

            roles = entity_response.findall(f'.//{{{self.admin_ns}}}Role')
            return_roles = []
            for role in roles:
                return_roles.append(role.text)
            return_dict['Roles'] = return_roles
            return return_dict
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.user_details(username)
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
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._account_status_(username, status, name)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"{name} failed")

    def disable_user(self, username):
        """
         Disable a Preservica User to prevent them logging in

        :param username: email address of the preservica user
        :type username: str

        """
        self._check_if_user_has_manager_role()
        return self._account_status_(username, "false", "disable_user")

    def enable_user(self, username):
        """
        Enable a Preservica User

        :param username: email address of the preservica user
        :type username: str

        """
        self._check_if_user_has_manager_role()
        return self._account_status_(username, "true", "enable_user")

    def user_report(self, report_name="users.csv"):
        """
        Create a report on all tenancy users
        :return:
        """

        self._check_if_user_has_manager_role()

        fieldnames = ['UserName', 'FullName', 'Email', 'Tenant', 'Enabled', 'Roles']

        with open(report_name, newline='', mode="wt", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for username in self.all_users():
                user_details = self.user_details(username)
                writer.writerow(user_details)

    def all_users(self) -> list:
        """
        Return a list of all users in the system

        :return list of usernames:
        :rtype: list
        """

        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f"{self.protocol}://{self.server}/api/admin/users", headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            users = entity_response.findall(f'.//{{{self.admin_ns}}}User')
            system_users = []
            for user in users:
                system_users.append(user.text)
            return system_users
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.all_users()
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "all_users failed")

    def add_xml_schema(self, name: str, description: str, originalName: str, xml_data: Any):
        """
        Add a new XSD document to Preservica

        :param name: Name for the XSD schema
        :type name: str

        :param description: Description for the XSD schema
        :type description: str

        :param originalName: The original file name for the schema on disk
        :type originalName: str

        :param xml_data: The xml schema as a UTF-8 string or a file like object
        :type xml_data: Any

        :return: None
        :rtype: None
        """

        self._check_if_user_has_manager_role()

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
            return
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_xml_schema(name, description, originalName, xml_data)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_xml_schema failed")

    def add_xml_document(self, name: str, xml_data: Any, document_type: str = "MetadataTemplate"):
        """
        Add a new XML document to Preservica
        The default type of XML document is a descriptive metadata template

        Options are:

        MetadataDropdownLists  -> Authority Lists
        CustomIndexDefinition  -> Custom Search Indexes
        MetadataTemplate -> Metadata Template
        UploadWizardConfigurationFile -> Upload Wizard Config
        ConfigurationFile -> Heritrix Config File

        :param name: The name of the xml document
        :type name: str

        :param xml_data: The xml schema as a UTF-8 string or as a file like object
        :type xml_data:

        :param document_type: The type of the XML document, defaults to descriptive metadata templates
        :type document_type: str

        :return: None
        :rtype: None

        """

        self._check_if_user_has_manager_role()

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
            return
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_xml_document(name, xml_data, document_type)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "add_xml_document failed")

    def delete_xml_document(self, uri: str):
        """
        Delete a XML document from Preservica

        :param uri: The URI of the xml document to delete
        :type uri: str

        :return: None
        :rtype: None

        """

        self._check_if_user_has_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        for document in self.xml_documents():
            if document['SchemaUri'] == uri.strip():
                request = self.session.delete(
                    f"{self.protocol}://{self.server}/api/admin/documents/{document['ApiId']}",
                    headers=headers)
                if request.status_code == requests.codes.no_content:
                    return
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.delete_xml_document(uri)
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "delete_xml_document failed")

    def delete_xml_schema(self, uri: str):
        """
        Delete an XML schema from Preservica

        :param uri: The URI of the xml schema to delete
        :type uri: str

        :return: None
        :rtype: None

        """

        self._check_if_user_has_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        for schema in self.xml_schemas():
            if schema['SchemaUri'] == uri.strip():
                request = self.session.delete(f"{self.protocol}://{self.server}/api/admin/schemas/{schema['ApiId']}",
                                              headers=headers)
                if request.status_code == requests.codes.no_content:
                    return
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.delete_xml_schema(uri)
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "delete_xml_schema failed")

    def xml_schema(self, uri: str) -> str:
        """
         fetch the metadata schema XSD document as a string by its URI

        :param uri: The URI of the xml schema
        :type uri: str

        :return: The XML schema as a string
        :rtype: str

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
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.xml_schema(uri)
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "xml_schema failed")

    def xml_document(self, uri: str) -> str:
        """
        fetch the metadata XML document as a string by its URI

        :param uri: The URI of the xml document
        :type uri: str

        :return: The XML document as a string
        :rtype: str

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
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.xml_document(uri)
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "xml_document failed")

    def xml_documents(self) -> List:
        """
        fetch the list of XML documents stored in Preservica

        :return: List of XML documents stored in Preservica
        :rtype: list

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
                document_dict['SchemaUri'] = schema_uri.text
                document_dict['Name'] = name.text
                document_dict['DocumentType'] = document_type.text
                document_dict['ApiId'] = api_id.text
                results.append(document_dict)
            return results
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.xml_documents()
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "xml_documents failed")

    def xml_schemas(self) -> List:
        """
         fetch the list of metadata schema XSD documents stored in Preservica

        :return: List of XML schema's stored in Preservica
        :rtype: list

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
                schema_dict['SchemaUri'] = schema_uri.text
                schema_dict['Name'] = name.text
                if description is not None:
                    schema_dict['Description'] = description.text
                else:
                    schema_dict['Description'] = ""
                schema_dict['ApiId'] = aip_id.text
                results.append(schema_dict)
            return results
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.xml_schemas()
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "xml_schemas failed")

    def xml_transforms(self) -> List:
        """
        fetch the list of xml transforms stored in Preservica

        :return: List of XML transforms stored in Preservica
        :rtype: list

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

                transform_dict['Name'] = name.text
                transform_dict['Purpose'] = purpose.text
                transform_dict['ApiId'] = aip_id.text
                results.append(transform_dict)
            return results

        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.xml_transforms()
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "xml_transforms failed")

    def xml_transform(self, input_uri: str, output_uri: str) -> str:
        """
        fetch the XML transform as a string by its URIs

        :param input_uri: The URI of the input XML document
        :type input_uri: str

        :param output_uri: The URI of the output XML document
        :type output_uri: str

        :return: The XML transform as a string
        :rtype: str

        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        for transform in self.xml_transforms():
            if (transform['FromSchemaUri'] == input_uri.strip()) and (transform['ToSchemaUri'] == output_uri.strip()):
                request = self.session.get(
                    f"{self.protocol}://{self.server}/api/admin/transforms/{transform['ApiId']}/content",
                    headers=headers)
                if request.status_code == requests.codes.ok:
                    return str(request.content.decode('utf-8'))
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.xml_transform(input_uri, output_uri)
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "xml_transform failed")

    def delete_xml_transform(self, input_uri: str, output_uri: str):
        """
        Delete a XSD document from Preservica

        :param input_uri: The URI of the input XML document
        :type input_uri: str

        :param output_uri: The URI of the output XML document
        :type output_uri: str

        :return: None
        :rtype: None

        """

        self._check_if_user_has_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        for transform in self.xml_transforms():
            if (transform['FromSchemaUri'] == input_uri.strip()) and (transform['ToSchemaUri'] == output_uri.strip()):
                request = self.session.delete(
                    f"{self.protocol}://{self.server}/api/admin/transforms/{transform['ApiId']}",
                    headers=headers)
                if request.status_code == requests.codes.no_content:
                    return
                elif request.status_code == requests.codes.unauthorized:
                    self.token = self.__token__()
                    return self.delete_xml_transform(input_uri, output_uri)
                else:
                    logger.error(request.content.decode('utf-8'))
                    raise RuntimeError(request.status_code, "delete_xml_transform failed")

    def add_xml_transform(self, name: str, input_uri: str, output_uri: str, purpose: str, originalName: str,
                          xml_data: Any):
        """
        Add a new XML transform to Preservica

        :param name: The name of the XML transform
        :type name: str

        :param input_uri: The URI of the input XML document
        :type input_uri: str

        :param output_uri: The URI of the output XML document
        :type output_uri: str

        :param purpose: The purpose of the transform, "transform" , "edit", "view"
        :type purpose: str

        :param originalName: The original file name of the transform
        :type originalName: str

        :param xml_data: The transform xml as a string or file like object
        :type xml_data: Any

        :return: None
        :rtype: None

        """

        self._check_if_user_has_manager_role()

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
            return

        if request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_xml_transform(name, input_uri, output_uri, purpose, originalName, xml_data)

        logger.error(request.content.decode('utf-8'))
        raise RuntimeError(request.status_code, "add_xml_transform failed")
