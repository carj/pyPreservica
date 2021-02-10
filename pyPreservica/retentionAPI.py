import xml.etree.ElementTree
from pyPreservica.common import *


class RetentionPolicy:
    def __init__(self, name, ref):
        self.name = name
        self.ref = ref

    def __str__(self):
        return f"Ref:\t\t\t{self.ref}\n" \
               f"Name:\t\t\t{self.name}\n"

    def __repr__(self):
        return self.__str__()


class RetentionAPI(AuthenticatedAPI):

    def __init__(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False):
        super().__init__(username, password, tenant, server, use_shared_secret)
        if self.major_version < 7 and self.minor_version < 2:
            raise RuntimeError("Retention API is only available when connected to a v6.2 System")

    def policy(self, reference: str) -> RetentionPolicy:
        """
           Return a retention policy by its reference
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = requests.get(f'https://{self.server}/api/entity/retention-policies/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            ref = entity_response.find('.//{*}RetentionPolicy/{*}Ref').text
            assert ref == reference
            name = entity_response.find('.//{*}RetentionPolicy/{*}Name').text
            rp = RetentionPolicy(name, ref)
            description = entity_response.find('.//{*}RetentionPolicy/{*}Description').text
            rp.description = description
            security_tag = entity_response.find('.//{*}RetentionPolicy/{*}SecurityTag').text
            rp.security_tag = security_tag
            start_date_field = entity_response.find('.//{*}RetentionPolicy/{*}StartDateField').text
            rp.start_date_field = start_date_field
            period = entity_response.find('.//{*}RetentionPolicy/{*}Period').text
            rp.period = period
            period_unit = entity_response.find('.//{*}RetentionPolicy/{*}PeriodUnit').text
            rp.period_unit = period_unit
            expiry_action = entity_response.find('.//{*}RetentionPolicy/{*}ExpiryAction').text
            rp.expiry_action = expiry_action
            restriction = entity_response.find('.//{*}RetentionPolicy/{*}Restriction')
            if restriction is not None:
                rp.restriction = restriction.text
            else:
                rp.restriction = None
            assignable = entity_response.find('.//{*}RetentionPolicy/{*}Assignable')
            rp.assignable = bool(assignable.text == "true")
            return rp
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.policy(reference)
        else:
            raise RuntimeError(request.status_code, "policy failed")

    def create_policy(self, name: str, description: str = None, security_tag: str = "open"):
        pass

    def delete_policy(self, reference: str):
        pass

    def policies(self):
        """
        Return a list of all retention policies
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        data = {'start': str(0), 'max': "250"}
        request = requests.get(f'https://{self.server}/api/entity/retention-policies', data=data, headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            result = set()
            for assignment in entity_response.findall('.//{*}RetentionPolicy'):
                ref = assignment.attrib['ref']
                name = assignment.attrib['name']
                rp = RetentionPolicy(name, ref)
                result.add(rp)
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.policies()
        else:
            raise RuntimeError(request.status_code, "policies failed")

    def add_assignments(self, entity: Entity, policy: RetentionPolicy):
        pass

    def remove_assignments(self, entity: Entity, policy: RetentionPolicy):
        pass

    def assignments(self, entity: Entity):
        """
          Return a list of retention policies for an entity.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = requests.get(
            f'https://{self.server}/api/entity/{entity.path}/{entity.reference}/retention-assignments',
            headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            result = set()
            for assignment in entity_response.findall('.//{*}RetentionAssignment'):
                entity_ref = assignment.find('./{*}Entity').text
                assert entity_ref == entity.reference
                policy = assignment.find('./{*}RetentionPolicy').text
                date = assignment.find('./{*}StartDate').text
                expired = bool(assignment.find('./{*}Expired').text == 'true')
                api_id = assignment.find('./{*}ApiId').text
                result.add(self.policy(policy))
            return result
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.assignments(entity)
        else:
            raise RuntimeError(request.status_code, "assignments failed")
