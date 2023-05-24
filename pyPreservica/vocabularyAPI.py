"""
pyPreservica ControlledVocabularyAPI module definition

A client library for the Preservica Repository web services Webhook API
https://us.preservica.com/api/reference-metadata/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""

from pyPreservica.common import *

logger = logging.getLogger(__name__)

BASE_ENDPOINT = '/api/reference-metadata'


class Table:
    def __init__(self, reference: str, name: str, security_tag: str, displayField: str, metadataConnections: list):
        self.reference = reference
        self.name = name
        self.security_tag = security_tag
        self.displayField = displayField
        self.metadataConnections = metadataConnections
        self.fields = None

    def __str__(self):
        return f"Ref:\t\t\t{self.reference}\n" \
               f"Name:\t\t\t{self.name}\n" \
               f"Security Tag:\t{self.security_tag}\n" \
               f"Display Field:\t\t\t{self.displayField}\n" \
               f"Metadata Connections:\t\t\t{self.metadataConnections}\n" \
               f"Fields:\t\t\t{self.fields}\n"


class ControlledVocabularyAPI(AuthenticatedAPI):

    def record(self, reference: str):
        """
        Get individual record by its ref.
        :param reference:
        :return:
        """
        headers = {HEADER_TOKEN: self.token, 'accept': 'application/json;charset=UTF-8'}
        response = self.session.get(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/records/{reference}',
                                    headers=headers)
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.record(reference)
        if response.status_code == requests.codes.ok:
            json_response = str(response.content.decode('utf-8'))
            return json.loads(json_response)
        else:
            exception = HTTPException("", response.status_code, response.url, "record",
                                      response.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def records(self, table: Table):
        """
        Get all records from a table.
        :return:
        """
        headers = {HEADER_TOKEN: self.token, 'accept': 'application/json;charset=UTF-8'}
        response = self.session.get(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/tables/{table.reference}/records',
                                    headers=headers)
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.records(table)
        if response.status_code == requests.codes.ok:
            json_response = str(response.content.decode('utf-8'))
            return json.loads(json_response)['records']
        else:
            exception = HTTPException("", response.status_code, response.url, "records",
                                      response.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def table(self, reference: str):
        """
        fetch a metadata table by id

        :param reference:
        :return:
        """
        headers = {HEADER_TOKEN: self.token, 'accept': 'application/json;charset=UTF-8'}
        response = self.session.get(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/tables/{reference}',
                                    headers=headers)
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.table(reference)
        if response.status_code == requests.codes.ok:
            json_response = str(response.content.decode('utf-8'))
            doc = json.loads(json_response)
            table = Table(doc['ref'], doc['name'], doc['securityDescriptor'], doc['displayField'],
                          doc['metadataConnections'])
            table.fields = doc['fields']
            return table
        else:
            exception = HTTPException("", response.status_code, response.url, "table",
                                      response.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def tables(self):
        """
        List reference metadata tables, optionally filtering by metadata connections.
        :return:
        """
        headers = {HEADER_TOKEN: self.token, 'accept': 'application/json;charset=UTF-8'}
        response = self.session.get(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/tables', headers=headers)
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.tables()
        if response.status_code == requests.codes.ok:
            json_response = str(response.content.decode('utf-8'))
            doc = json.loads(json_response)
            results = set()
            for table in doc['tables']:
                t = Table(table['ref'], table['name'], table['securityDescriptor'], table['displayField'],
                          table['metadataConnections'])
                results.add(t)
            return results
        else:
            exception = HTTPException("", response.status_code, response.url, "tables",
                                      response.content.decode('utf-8'))
            logger.error(exception)
            raise exception
