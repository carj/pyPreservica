"""
pyPreservica ControlledVocabularyAPI module definition

A client library for the Preservica Repository web services Webhook API
https://us.preservica.com/api/reference-metadata/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
import json
import csv
import requests

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


class AuthorityAPI(AuthenticatedAPI):

    def delete_record(self, reference: str):
        """
          Delete a record from a table by its reference

          :param reference:    The reference of the record to delete
          :type: reference:    str

          """
        headers = {HEADER_TOKEN: self.token, 'accept': 'application/json;charset=UTF-8'}
        response = self.session.delete(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/records/{reference}',
                                       headers=headers)
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.delete_record(reference)
        if response.status_code == requests.codes.no_content:
            return
        else:
            exception = HTTPException("", response.status_code, response.url, "delete_record",
                                      response.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def add_records(self, table: Table, csv_file, encoding=None):
        """
         Add new records to an existing table from a CSV document

         :param table:    The Table to add the record to
         :type: table:    Table

         :param csv_file:    The path to the CSV document
         :type: csv_file:    str

         :param encoding:    The encoding used to open the csv document
         :type: encoding:    str

         """
        with open(csv_file, newline='', encoding=encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if ('ID' in row) or ('id' in row):
                    pass
                else:
                    row['id'] = reader.line_num
                self.add_record(table, row)

    def add_record(self, table: Table, record: dict):
        """
         Add a new record to an existing table

         :param table:    The Table to add the record to
         :type: table:    Table

         :param record:    The record
         :type: record:    dict

         :return: A single record
         :rtype: dict

         """
        headers = {HEADER_TOKEN: self.token, 'accept': 'application/json;charset=UTF-8'}

        body = {"securityDescriptor": "open", "fieldValues": []}
        for key, val in record.items():
            body["fieldValues"].append({"name": str(key).lower(), "value": val})

        response = self.session.post(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/tables/{table.reference}/records',
                                     headers=headers, json=body)

        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_record(table, record)
        if response.status_code == requests.codes.created:
            return str(response.content.decode('utf-8'))
        else:
            exception = HTTPException("", response.status_code, response.url, "add_record",
                                      response.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def record(self, reference: str) -> dict:
        """
         Return a record by its reference

         :param reference:    The record reference
         :type: reference:    str

         :return: A single record
         :rtype: dict

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

    def records(self, table: Table) -> list[dict]:
        """
         Return all records from a table

         :param table:    The authority table
         :type: table:    Table

         :return: List of records
         :rtype: list[dict]

         """
        headers = {HEADER_TOKEN: self.token, 'accept': 'application/json;charset=UTF-8'}
        response = self.session.get(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/tables/{table.reference}/records',
                                    headers=headers, params={"expand": "true"})
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

    def table(self, reference: str) -> Table:
        """
        fetch an authority table by its reference

        :param reference:    The reference for the authority table
        :type: reference:    str

        :return: An authority table
        :rtype: Table

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

    def tables(self) -> set[Table]:
        """
        List reference metadata tables

        :return: Set of authority tables
        :rtype: set(Table)

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
