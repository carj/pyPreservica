"""
pyPreservica MDFormsAPI module definition

A client library for the Preservica Repository web services Metadata API
https://demo.preservica.com/api/metadata/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
import json
import xml.etree.ElementTree
from typing import Callable

from pyPreservica.common import *


class MDFormsAPI(AuthenticatedAPI):
    def __init__(self, username: str = None, password: str = None, tenant: str = None, server: str = None,
                 use_shared_secret: bool = False, two_fa_secret_key: str = None,
                 protocol: str = "https", request_hook: Callable = None):

        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook)

        xml.etree.ElementTree.register_namespace("oai_dc", "http://www.openarchives.org/OAI/2.0/oai_dc/")
        xml.etree.ElementTree.register_namespace("ead", "urn:isbn:1-931666-22-9")

    def delete_group(self, id: str):
        """
        Delete a group
        :param id: Group ID
        :return:
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{id}'
        with self.session.delete(url, headers=headers) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.delete_group(id)
            elif request.status_code == requests.codes.no_content:
                return None
            else:
                exception = HTTPException(None, request.status_code, request.url, "delete_group",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def add_group(self, document):
        """
        Add a new group
        :return:
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/'
        with self.session.post(url, headers=headers, json=document) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.add_group(document)
            elif request.status_code == requests.codes.created:
                return json.loads(str(request.content.decode('utf-8')))
            else:
                exception = HTTPException(None, request.status_code, request.url, "group",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def group(self, id: str):
        """
        Fetch a metadata Group by its id
        :param id: The group ID
        :return: JSON Document
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups/{id}'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.group(id)
            elif request.status_code == requests.codes.ok:
                return json.loads(str(request.content.decode('utf-8')))
            else:
                exception = HTTPException(None, request.status_code, request.url, "group",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception

    def groups(self):
        """
        Fetch all the Metadata Groups as JSON
        :return: JSON Document
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        url = f'{self.protocol}://{self.server}/api/metadata/groups'
        with self.session.get(url, headers=headers) as request:
            if request.status_code == requests.codes.unauthorized:
                self.token = self.__token__()
                return self.groups()
            elif request.status_code == requests.codes.ok:
                return json.loads(str(request.content.decode('utf-8')))['groups']
            else:
                exception = HTTPException(None, request.status_code, request.url, "groups",
                                          request.content.decode('utf-8'))
                logger.error(exception)
                raise exception
