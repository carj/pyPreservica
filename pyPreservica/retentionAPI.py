"""
pyPreservica RetentionAPI module definition

A client library for the Preservica Repository web services Entity API
https://us.preservica.com/api/entity/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""


import xml.etree.ElementTree
from typing import Set, Callable

from pyPreservica.common import *

logger = logging.getLogger(__name__)


class RetentionAssignment:
    def __init__(self, entity_reference: str, policy_reference: str, api_id: str, start_date, expired=False):
        self.entity_reference = entity_reference
        self.policy_reference = policy_reference
        self.api_id = api_id
        self.start_date = start_date
        self.expired = expired

    def __str__(self):
        return f"Entity Reference:\t\t\t{self.entity_reference}\n" \
               f"Policy Reference:\t\t\t{self.policy_reference}\n"

    def __repr__(self):
        return self.__str__()


class RetentionPolicy:
    def __init__(self, name: str, reference: str):
        self.name = name
        self.reference = reference
        self.description = ""
        self.security_tag = ""
        self.start_date_field = ""
        self.period = ""
        self.expiry_action = ""
        self.assignable = True
        self.restriction = ""
        self.period_unit = ""

    def __str__(self):
        return f"Ref:\t\t\t{self.reference}\n" \
               f"Name:\t\t\t{self.name}\n" \
               f"Description:\t{self.description}\n"

    def __repr__(self):
        return self.__str__()


class RetentionAPI(AuthenticatedAPI):

    def __init__(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False,
                 two_fa_secret_key: str = None, protocol: str = "https", request_hook: Callable = None, credentials_path: str = 'credentials.properties'):
        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook, credentials_path)

        if self.major_version < 7 and self.minor_version < 2:
            raise RuntimeError("Retention API is only available when connected to a v6.2 System")

    def policy(self, reference: str) -> RetentionPolicy:
        """
         Return a retention policy by reference

        :param reference: The policy reference
        :type reference: str

        :return: The retention policy
        :rtype: RetentionPolicy

         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/retention-policies/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            ref = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Ref').text
            assert ref == reference
            name = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Name').text
            rp = RetentionPolicy(name, ref)
            description = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Description').text
            rp.description = description
            security_tag = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}SecurityTag').text
            rp.security_tag = security_tag
            start_date_field = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}StartDateField')
            if start_date_field is not None:
                rp.start_date_field = start_date_field.text
            else: 
                start_date_field = None
            period = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Period')
            if period is not None:
                rp.period = period.text
            else:
                rp.period = None
            period_unit = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}PeriodUnit')
            if period_unit is not None:
                rp.period_unit = period_unit.text
            else:
                rp.period_unit = None
            expiry_action = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}ExpiryAction')
            if expiry_action is not None:
                rp.expiry_action = expiry_action.text
            else:
                rp.expiry_action = None
            restriction = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Restriction')
            if restriction is not None:
                rp.restriction = restriction.text
            else:
                rp.restriction = None
            assignable = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Assignable')
            rp.assignable = strtobool(assignable.text)
            return rp
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.policy(reference)
        else:
            logger.error(f"policy failed with error code {request.status_code}")
            raise RuntimeError(request.status_code, "policy failed")

    def assignable_policy(self, reference: str, status: bool):
        """
        Make a policy assignable

        :param reference:  The policy ID
        :type reference: str

        :param status:     The assignable status
        :type status: bool


        :return:
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'text/plain;charset=UTF-8'}
        data = str(status)
        request = self.session.put(f'{self.protocol}://{self.server}/api/entity/retention-policies/{reference}/assignable',
                                   headers=headers, data=data)
        if request.status_code == requests.codes.ok:
            pass
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.assignable_policy(reference, status)
        else:
            logger.error(f"assignable_policy failed with error code {request.status_code}")
            raise RuntimeError(request.status_code, "assignable_policy failed")

    def update_policy(self, reference: str, **kwargs):
        """
        Update an existing policy

        Arguments are kwargs map

        Name
        Description
        SecurityTag
        StartDateField
        Period
        PeriodUnit
        ExpiryAction
        ExpiryActionParameters
        Restriction
        Assignable
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        retention_policy = xml.etree.ElementTree.Element('RetentionPolicy ', {"xmlns": self.rm_ns})

        if 'Name' in kwargs:
            name = kwargs.get("Name")
        else:
            raise RuntimeError("No Name specified in kwargs argument")

        if 'Description' in kwargs:
            description = kwargs.get("Description")
        else:
            raise RuntimeError("No Description specified in kwargs argument")

        if 'SecurityTag' in kwargs:
            security_tag = kwargs.get("SecurityTag")
        else:
            raise RuntimeError("No SecurityTag specified in kwargs argument")

        if 'StartDateField' in kwargs:
            start_date_field = kwargs.get("StartDateField")
        else:
            raise RuntimeError("No StartDateField specified in kwargs argument")

        if 'Period' in kwargs:
            period = kwargs.get("Period")
        else:
            raise RuntimeError("No Period specified in kwargs argument")

        if 'PeriodUnit' in kwargs:
            period_unit = kwargs.get("PeriodUnit")
        else:
            raise RuntimeError("No PeriodUnit specified in kwargs argument")

        if 'ExpiryAction' in kwargs:
            expiry_action = kwargs.get("ExpiryAction")
        else:
            raise RuntimeError("No ExpiryAction specified in kwargs argument")

        if 'ExpiryActionParameters' in kwargs:
            expiry_action_parameters = kwargs.get("ExpiryActionParameters")
        else:
            raise RuntimeError("No ExpiryActionParameters specified in kwargs argument")

        if 'Restriction' in kwargs:
            restriction = kwargs.get("Restriction")
        else:
            raise RuntimeError("No Restriction specified in kwargs argument")

        if 'Assignable' in kwargs:
            assignable = bool(kwargs.get("Assignable"))
        else:
            raise RuntimeError("No Assignable specified in kwargs argument")

        xml.etree.ElementTree.SubElement(retention_policy, "Ref").text = reference
        xml.etree.ElementTree.SubElement(retention_policy, "Name").text = name
        xml.etree.ElementTree.SubElement(retention_policy, "Description").text = description
        xml.etree.ElementTree.SubElement(retention_policy, "SecurityTag").text = security_tag
        xml.etree.ElementTree.SubElement(retention_policy, "StartDateField").text = start_date_field
        xml.etree.ElementTree.SubElement(retention_policy, "Period").text = period
        xml.etree.ElementTree.SubElement(retention_policy, "PeriodUnit").text = period_unit
        xml.etree.ElementTree.SubElement(retention_policy, "ExpiryAction").text = expiry_action
        xml.etree.ElementTree.SubElement(retention_policy, "ExpiryActionParameters").text = expiry_action_parameters
        xml.etree.ElementTree.SubElement(retention_policy, "Restriction").text = restriction
        xml.etree.ElementTree.SubElement(retention_policy, "Assignable").text = str(assignable)

        xml_request = xml.etree.ElementTree.tostring(retention_policy, encoding='utf-8')

        request = self.session.put(f'{self.protocol}://{self.server}/api/entity/retention-policies/{reference}', data=xml_request,
                                   headers=headers)
        if request.status_code == requests.codes.ok:
            return self.policy(reference)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.update_policy(reference, **kwargs)
        else:
            logger.error(str(request.content.decode('utf-8')))
            raise RuntimeError(request.status_code, "update_policy failed " + str(request.content.decode('utf-8')))

    def create_policy(self, **kwargs):
        """
        Create a new policy

        Arguments are kwargs map

        Name
        Description
        SecurityTag
        StartDateField
        Period
        PeriodUnit
        ExpiryAction
        ExpiryActionParameters
        Restriction
        Assignable
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        retention_policy = xml.etree.ElementTree.Element('RetentionPolicy ', {"xmlns": self.rm_ns})

        if 'Name' in kwargs:
            name = kwargs.get("Name")
        else:
            raise RuntimeError("No Name specified in kwargs argument")

        if 'Description' in kwargs:
            description = kwargs.get("Description")
        else:
            raise RuntimeError("No Description specified in kwargs argument")

        if 'SecurityTag' in kwargs:
            security_tag = kwargs.get("SecurityTag")
        else:
            raise RuntimeError("No SecurityTag specified in kwargs argument")

        if 'StartDateField' in kwargs:
            start_date_field = kwargs.get("StartDateField")
        else:
            raise RuntimeError("No StartDateField specified in kwargs argument")

        if 'Period' in kwargs:
            period = kwargs.get("Period")
        else:
            raise RuntimeError("No Period specified in kwargs argument")

        if 'PeriodUnit' in kwargs:
            period_unit = kwargs.get("PeriodUnit")
        else:
            raise RuntimeError("No PeriodUnit specified in kwargs argument")

        if 'ExpiryAction' in kwargs:
            expiry_action = kwargs.get("ExpiryAction")
        else:
            raise RuntimeError("No ExpiryAction specified in kwargs argument")

        if 'ExpiryActionParameters' in kwargs:
            expiry_action_parameters = kwargs.get("ExpiryActionParameters")
        else:
            raise RuntimeError("No ExpiryActionParameters specified in kwargs argument")

        if 'Restriction' in kwargs:
            restriction = kwargs.get("Restriction")
        else:
            raise RuntimeError("No Restriction specified in kwargs argument")

        if 'Assignable' in kwargs:
            assignable = bool(kwargs.get("Assignable"))
        else:
            raise RuntimeError("No Assignable specified in kwargs argument")

        xml.etree.ElementTree.SubElement(retention_policy, "Name").text = name
        xml.etree.ElementTree.SubElement(retention_policy, "Description").text = description
        xml.etree.ElementTree.SubElement(retention_policy, "SecurityTag").text = security_tag
        xml.etree.ElementTree.SubElement(retention_policy, "StartDateField").text = start_date_field
        xml.etree.ElementTree.SubElement(retention_policy, "Period").text = period
        xml.etree.ElementTree.SubElement(retention_policy, "PeriodUnit").text = period_unit
        xml.etree.ElementTree.SubElement(retention_policy, "ExpiryAction").text = expiry_action
        xml.etree.ElementTree.SubElement(retention_policy, "ExpiryActionParameters").text = expiry_action_parameters
        xml.etree.ElementTree.SubElement(retention_policy, "Restriction").text = restriction
        xml.etree.ElementTree.SubElement(retention_policy, "Assignable").text = str(assignable)

        xml_request = xml.etree.ElementTree.tostring(retention_policy, encoding='utf-8')

        request = self.session.post(f'{self.protocol}://{self.server}/api/entity/retention-policies', data=xml_request,
                                    headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            retention_policy = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy')
            ref = retention_policy.find(f'.//{{{self.rm_ns}}}Ref').text
            return self.policy(ref)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.create_policy(**kwargs)
        else:
            logger.error(f'create_policy failed {request.status_code}')
            logger.error(str(request.content.decode('utf-8')))
            raise RuntimeError(request.status_code, "create_policy failed")

    def delete_policy(self, reference: str):
        """
        Delete a retention policy

        :param reference: The policy reference
        :type reference: str

        """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.delete(f'{self.protocol}://{self.server}/api/entity/retention-policies/{reference}',
                                      headers=headers)
        if request.status_code == requests.codes.no_content:
            pass
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.delete_policy(reference)
        else:
            logger.error(f'delete_policy failed {request.status_code}')
            raise RuntimeError(request.status_code, "delete_policy failed")

    def policy_by_name(self, name: str) -> RetentionPolicy:
        """
         Return a retention policy by name

        :param name: The policy name
        :type name: str

        :return: The retention policy
        :rtype: RetentionPolicy

         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        data = {'start': str(0), 'max': "250"}
        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/retention-policies', data=data, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            for assignment in entity_response.findall(f'.//{{{self.entity_ns}}}RetentionPolicy'):
                ref = assignment.attrib['ref']
                policy_name = assignment.attrib['name']
                if policy_name == name:
                    return self.policy(reference=ref)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.policy_by_name(name)
        else:
            raise RuntimeError(request.status_code, "policies failed")

    def policies(self, maximum: int = 250, next_page: str = None) -> PagedSet:
        """
        Return a list of all retention policies
        Returns a maxmium of 250 policies by default


        :return: Set of retention policies
        :rtype: Set[RetentionPolicy]

        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        params = {'start': str(0), 'max': str(maximum)}
        
        if next_page is None:
            params = {'start': '0', 'max': str(maximum)}
            request = self.session.get(f'{self.protocol}://{self.server}/api/entity/retention-policies', params=params, headers=headers)
        else:
            request = self.session.get(next_page,params=params)
        
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            logger.debug(xml_response)
            result = set()
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Paging/{{{self.entity_ns}}}Next')
            total_results = int(entity_response.find(
                f'.//{{{self.entity_ns}}}TotalResults').text)
            for assignment in entity_response.findall(f'.//{{{self.entity_ns}}}RetentionPolicy'):
                ref = assignment.attrib['ref']
                name = assignment.attrib['name']
                result.add(self.policy(reference=ref))
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result,has_more,total_results,url)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.policies()
        else:
            raise RuntimeError(request.status_code, "policies failed")

    def add_assignments(self, entity: Entity, policy: RetentionPolicy) -> RetentionAssignment:
        """
        Assign a retention policy to an Asset.

        :param entity: The Preservica Entity to assign a policy to
        :type entity: Entity

        :param policy: The RetentionAssignment
        :type policy: RetentionPolicy

        :return: The RetentionAssignment
        :rtype: RetentionAssignment

        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        if not isinstance(entity, Asset):
            raise RuntimeError("Retention policies can only be assigned to Assets")

        assignment = xml.etree.ElementTree.Element('RetentionAssignment', {"xmlns": self.rm_ns})
        xml.etree.ElementTree.SubElement(assignment, "RetentionPolicy").text = policy.reference
        xml_request = xml.etree.ElementTree.tostring(assignment, encoding='utf-8').decode('utf-8')
        logger.debug(xml_request)
        request = self.session.post(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/retention-assignments',
            headers=headers, data=xml_request)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            api_id = entity_response.find(f'.//{{{self.rm_ns}}}ApiId').text
            policy_ref = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy').text
            entity_ref = entity_response.find(f'.//{{{self.rm_ns}}}Entity').text
            start_date = entity_response.find(f'.//{{{self.rm_ns}}}StartDate')
            if start_date is not None:
                start_date = start_date.text
            else:
                start_date = None
            assert entity_ref == entity.reference
            assert policy_ref == policy.reference
            return RetentionAssignment(entity_ref, policy_ref, api_id, start_date)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.add_assignments(entity, policy)
        else:
            logger.debug(f"add_assignments failed {request.status_code}")
            logger.error(str(request.content.decode('utf-8')))
            raise RuntimeError(request.status_code, "add_assignments failed")

    def remove_assignments(self, retention_assignment: RetentionAssignment):
        """
        Delete a retention policy from an asset

        :param retention_assignment: The Preservica Entity to assign a policy to
        :type retention_assignment: RetentionAssignment


        :return: The Asset Reference
        :rtype: str

        """

        headers = {HEADER_TOKEN: self.token}

        request = self.session.delete(
            f'{self.protocol}://{self.server}/api/entity/information-objects/{retention_assignment.entity_reference}/retention'
            f'-assignments/{retention_assignment.api_id}', headers=headers)
        if request.status_code == requests.codes.no_content:
            return retention_assignment.entity_reference
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.remove_assignments(retention_assignment)
        else:
            raise RuntimeError(request.status_code, "remove_assignments failed")

    def assignments(self, entity: Entity) -> Set[RetentionAssignment]:
        """
          Return a list of retention policies for an entity.

          :param entity: The entity to fetch assignments for
          :type entity: class:`Entity`

          :return: Set of policy assignments
          :rtype: Set[RetentionAssignment]

        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/retention-assignments',
            headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            result = set()
            for assignment in entity_response.findall(f'.//{{{self.rm_ns}}}RetentionAssignment'):
                entity_ref = assignment.find(f'.//{{{self.rm_ns}}}Entity').text
                assert entity_ref == entity.reference
                policy = assignment.find(f'.//{{{self.rm_ns}}}RetentionPolicy').text
                start_date = assignment.find(f'.//{{{self.rm_ns}}}StartDate')
                if start_date is not None:
                    start_date = start_date.text
                else:
                    start_date = None
                expired = bool(assignment.find(f'.//{{{self.rm_ns}}}Expired').text == 'true')
                api_id = assignment.find(f'.//{{{self.rm_ns}}}ApiId').text
                ra = RetentionAssignment(entity_ref, policy, api_id, start_date, expired)
                result.add(ra)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.assignments(entity)
        else:
            raise RuntimeError(request.status_code, "assignments failed")
