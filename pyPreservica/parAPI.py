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


class PreservationActionRegistry:

    def __init__(self, server: str = None, username: str = None, password: str = None, protocol: str = 'https'):
        self.protocol = protocol
        self.session = requests.Session()
        self.session.headers.update({'accept': 'application/json;charset=UTF-8'})
        config = configparser.ConfigParser()
        config.read('credentials.properties')
        if not server:
            server = os.environ.get('PRESERVICA_SERVER')
            if server is None:
                try:
                    server = config['credentials']['server']
                except KeyError:
                    pass
        if not server:
            msg = "No valid server found in method arguments, environment variables or credentials.properties file"
            logger.error(msg)
            raise RuntimeError(msg)
        else:
            self.server = server
        if not username:
            username = os.environ.get('PRESERVICA_USERNAME')
            if username is None:
                try:
                    username = config['credentials']['username']
                except KeyError:
                    pass
        self.username = username
        if not password:
            password = os.environ.get('PRESERVICA_PASSWORD')
            if password is None:
                try:
                    password = config['credentials']['password']
                except KeyError:
                    pass
        self.password = password

    def format_family(self, guid: str) -> str:
        return self.__guid__(guid, "format-families")

    def format_families(self) -> str:
        return self.__all_("format-families")

    def add_format_family(self, document) -> str:
        return self.__add__("format-families", document)

    def update_format_family(self, guid: str, document) -> str:
        return self.__update__(guid, "format-families", document)

    def delete_format_family(self, guid) -> str:
        return self.__delete__(guid, "format-families")

    def preservation_action_type(self, guid: str) -> str:
        return self.__guid__(guid, "preservation-action-types")

    def preservation_action_types(self) -> str:
        return self.__all_("preservation-action-types")

    def add_preservation_action_type(self, document) -> str:
        return self.__add__("preservation-action-types", document)

    def update_preservation_action_type(self, guid: str, document) -> str:
        return self.__update__(guid, "preservation-action-types", document)

    def delete_preservation_action_type(self, guid) -> str:
        return self.__delete__(guid, "preservation-action-types")

    def property(self, guid: str) -> str:
        return self.__guid__(guid, "properties")

    def properties(self) -> str:
        return self.__all_("properties")

    def add_property(self, document) -> str:
        return self.__add__("properties", document)

    def update_property(self, guid: str, document) -> str:
        return self.__update__(guid, "properties", document)

    def delete_property(self, guid) -> str:
        return self.__delete__(guid, "properties")

    def representation_format(self, guid: str) -> str:
        return self.__guid__(guid, "representation-formats")

    def representation_formats(self) -> str:
        return self.__all_("representation-formats")

    def add_representation_format(self, document) -> str:
        return self.__add__("representation-formats", document)

    def update_representation_format(self, guid: str, document) -> str:
        return self.__update__(guid, "representation-formats", document)

    def delete_representation_format(self, guid) -> str:
        return self.__delete__(guid, "representation-formats")

    def file_format(self, puid: str) -> str:
        return self.__guid__(puid, "file-formats")

    def file_formats(self) -> str:
        return self.__all_("file-formats")

    def add_file_format(self, document) -> str:
        return self.__add__("file-formats", document)

    def update_file_format(self, guid: str, document) -> str:
        return self.__update__(guid, "file-formats", document)

    def delete_file_format(self, guid) -> str:
        return self.__delete__(guid, "file-formats")

    def tool(self, guid: str) -> str:
        return self.__guid__(guid, "tools")

    def tools(self) -> str:
        return self.__all_("tools")

    def add_tool(self, document) -> str:
        return self.__add__("tools", document)

    def update_tool(self, guid: str, document) -> str:
        return self.__update__(guid, "tools", document)

    def delete_tool(self, guid) -> str:
        return self.__delete__(guid, "tools")

    def preservation_action(self, guid: str) -> str:
        return self.__guid__(guid, "preservation-actions")

    def preservation_actions(self) -> str:
        return self.__all_("preservation-actions")

    def add_preservation_action(self, document) -> str:
        return self.__add__("preservation-actions", document)

    def update_preservation_action(self, guid: str, document) -> str:
        return self.__update__(guid, "preservation-actions", document)

    def delete_preservation_action(self, guid) -> str:
        return self.__delete__(guid, "preservation-actions")

    def business_rule(self, guid: str) -> str:
        return self.__guid__(guid, "business-rules")

    def business_rules(self) -> str:
        return self.__all_("business-rules")

    def add_business_rule(self, document) -> str:
        return self.__add__("business-rules", document)

    def update_business_rule(self, guid: str, document) -> str:
        return self.__update__(guid, "business-rules", document)

    def delete_business_rule(self, guid) -> str:
        return self.__delete__(guid, "business-rules")

    def rule_set(self, guid: str) -> str:
        return self.__guid__(guid, "rulesets")

    def rule_sets(self) -> str:
        return self.__all_("rulesets")

    def add_rule_set(self, document) -> str:
        return self.__add__("rulesets", document)

    def update_rule_set(self, guid: str, document) -> str:
        return self.__update__(guid, "rulesets", document)

    def delete_rule_set(self, guid) -> str:
        return self.__delete__(guid, "rulesets")

    def __guid__(self, guid: str, endpoint: str) -> str:
        request = self.session.get(f'{self.protocol}://{self.server}/Registry/par/{endpoint}/{guid}')
        if request.status_code == requests.codes.ok:
            return request.content.decode('utf-8')
        else:
            logger.debug(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"{endpoint} failed")

    def __all_(self, endpoint: str) -> str:
        request = self.session.get(f'{self.protocol}://{self.server}/Registry/par/{endpoint}')
        if request.status_code == requests.codes.ok:
            return request.content.decode('utf-8')
        else:
            logger.debug(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, f"{endpoint} failed")

    def __add__(self, endpoint: str, document) -> str:
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
