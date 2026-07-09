"""
pyPreservica RetentionAPI module definition

A client library for the Preservica Repository web services Entity API
https://us.preservica.com/api/entity/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
import uuid
import xml.etree.ElementTree
from typing import Set, Callable, Generator

from pyPreservica.common import *

logger = logging.getLogger(__name__)


class RetentionAssignment:
    def __init__(self, entity_reference: str, policy_reference: str, api_id: str, start_date, expired=False):
        self.entity_reference = entity_reference
        self.policy_reference = policy_reference
        self.policy_name = None
        self.api_id = api_id
        self.start_date = start_date
        self.expired = expired

    def __str__(self):
        """
        Return a human-readable string representation of the retention assignment.

        :returns: A formatted string showing the entity reference and the policy reference.
        :rtype: str
        """
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
        """
        Return a human-readable string representation of the retention policy.

        :returns: A formatted string showing the reference, name, and description.
        :rtype: str
        """
        return f"Ref:\t\t\t{self.reference}\n" \
               f"Name:\t\t\t{self.name}\n" \
               f"Description:\t{self.description}\n"

    def __repr__(self):
        return self.__str__()




class LegalHold:
    def __init__(self, name: str, reference: str):
        self.name = name
        self.reference = reference
        self.description = ""
        self.create_date = None
        self.user = None


    def __str__(self):
        """
        Return a human-readable string representation of the Legal Hold.

        :returns: A formatted string showing the reference, name, and description.
        :rtype: str
        """
        return f"Ref:\t\t\t{self.reference}\n" \
               f"Name:\t\t\t{self.name}\n" \
               f"Description:\t{self.description}\n"

    def __repr__(self):
        return self.__str__()


class LegalHoldAssignment:
    def __init__(self, entity_ref: str, legal_hold_ref: str, assigned_date: datetime = None):
        self.entity_ref: str = entity_ref
        self.legal_hold_ref: str = legal_hold_ref
        self.assigned_date: datetime = assigned_date

    def __str__(self):
        """
        Return a human-readable string representation of the LegalHoldAssignment.

        """

        return f"Asset Ref:\t\t\t{self.entity_ref}\n" \
               f"Legal Hold Ref:\t\t\t{self.legal_hold_ref}\n" \
               f"Assigned Date:\t{self.assigned_date}\n"

    def __repr__(self):
        return self.__str__()


class LegalHoldAPI(AuthenticatedAPI):

    def __init__(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False,
                 two_fa_secret_key: str|None = None, protocol: str = "https", request_hook: Callable|None = None,
                 credentials_path: str = 'credentials.properties'):

        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook, credentials_path)

        if self.major_version < 10 and self.minor_version < 1:
            raise RuntimeError("Legal Hold API is only available when connected to a v9.1 System")

    def find(self, legal_hold: LegalHold | None = None) -> Generator:
        """

        Find all Assets which are under the given legal hold


        :param legal_hold:
        :type legal_hold:
        :return:
        :rtype:
        """

        def _find_entities(legal_hold_ref: str | None = None, start_index: int = 0, page_size: int = 25) -> PagedSet:
            start_from = str(start_index)
            headers = {'Content-Type': 'application/x-www-form-urlencoded', HEADER_TOKEN: self.token}
            filter_values = {'xip.legal_hold_ref': f"{legal_hold_ref}", "xip.title": "", "xip.reference": "*"}
            field_list = []
            for key, value in filter_values.items():
                field_list.append('{' f' "name": "{key}", "values": ["{value}"] ' + '}')
            filter_terms = ','.join(field_list)
            query_term = ('{ "q":  "%s",  "fields":  [ %s ] }' % ("*", filter_terms))
            payload = {'start': start_from, 'max': str(page_size), 'metadata': list(filter_values.keys()),
                       'q': query_term}
            results = self.session.post(f'{self.protocol}://{self.server}/api/content/search', data=payload,
                                        headers=headers)
            if results.status_code == requests.codes.ok:
                json_doc = results.json()
                results_list = []
                hits = int(json_doc['value']['totalHits'])
                metadata = json_doc['value']['metadata']
                refs = list(map(lambda x: content_api_identifier_to_type(x), list(json_doc['value']['objectIds'])))

                for m_row, r_row in zip(metadata, refs):
                    results_map = {'xip.reference': r_row[1]}
                    for li in m_row:
                        results_map[li['name']] = li['value']
                    results_list.append(results_map)

                ps = PagedSet(results=results_list, has_more=(hits > (page_size + start_index)), total=hits,
                              next_page="")
                return ps

            else:
                logger.error(f"find failed with error code {results.status_code}")
                raise RuntimeError(results.status_code, "find failed")

        if legal_hold is None:
            legal_hold_value = "*"
        else:
            legal_hold_value = legal_hold.reference

        page_size_value = 25
        start_index_value = 0
        paged_set = _find_entities(legal_hold_ref=legal_hold_value, start_index=start_index_value, page_size=page_size_value)
        for entity in paged_set.results:
            entity_ref = entity['xip.reference']
            hold_ref = entity['xip.legal_hold_ref']
            yield LegalHoldAssignment(entity_ref, hold_ref)

        start_index_value = start_index_value + page_size_value
        while paged_set.has_more:
            paged_set = _find_entities(legal_hold_ref=legal_hold_value, start_index=start_index_value, page_size=page_size_value)
            for entity in paged_set.results:
                entity_ref = entity['xip.reference']
                hold_ref = entity['xip.legal_hold_ref']
                yield LegalHoldAssignment(entity_ref, hold_ref)



    def remove_legal_hold_assignment(self, asset: Asset, legal_hold: LegalHold) -> Asset:
        """

        Remove an asset from a legal hold

        :param asset:
        :type asset:
        :param legal_hold:
        :type legal_hold:
        :return:
        :rtype:
        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        request = self.session.delete(f'{self.protocol}://{self.server}/api/entity/{asset.path}/{asset.reference}/legal-holds/{legal_hold.reference}',headers=headers)

        if request.status_code == requests.codes.no_content:
            return asset
        else:
            raise RuntimeError(request.status_code, "remove_legal_hold_assignment failed")

    def assign_legal_hold(self, asset: Asset, legal_hold: LegalHold) -> LegalHold:
        """
        Assign a legal hold to an Asset

        :param asset:
        :type asset:
        :param legal_hold:
        :type legal_hold:
        :return:
        :rtype: LegalHold
        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        structural_object = xml.etree.ElementTree.Element('LegalHoldAssignmentRequest ', {"xmlns": self.xip_ns})
        xml.etree.ElementTree.SubElement(structural_object, "LegalHoldRef").text = legal_hold.reference
        xml_request = xml.etree.ElementTree.tostring(structural_object, encoding='utf-8')
        logger.debug(xml_request)

        request = self.session.post(f'{self.protocol}://{self.server}/api/entity/{asset.path}/{asset.reference}/legal-holds',
                                   data=xml_request, headers=headers)

        if request.status_code == requests.codes.ok:
            return legal_hold
        else:
            raise RuntimeError(request.status_code, "assign_legal_hold failed")

    def _legal_holds_(self, name: str|None, maximum: int = 100, next_page: str = None) -> PagedSet:
        """

        :param maximum:
        :type maximum:
        :param next_page:
        :type next_page:
        :return:
        :rtype:
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        if next_page is None:
            if name is None:
                params = {'start': '0', 'max': str(maximum), 'expand': 'true'}
            else:
                params = {'start': '0', 'max': str(maximum), 'expand': 'true', 'name': name}
            request = self.session.get(f'{self.protocol}://{self.server}/api/entity/legal-holds', params=params,
                                       headers=headers)
        else:
            request = self.session.get(next_page, headers=headers)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            logger.debug(xml_response)
            result = set()
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Paging/{{{self.entity_ns}}}Next')
            total_results = int(entity_response.find(f'.//{{{self.entity_ns}}}TotalResults').text)
            for hold in entity_response.findall(f'.//{{{self.entity_ns}}}LegalHold'):
                ref = hold.find(f'.//{{{self.entity_ns}}}Ref').text
                name = hold.find(f'.//{{{self.entity_ns}}}Name').text
                description = hold.find(f'.//{{{self.entity_ns}}}Description').text
                user = hold.find(f'.//{{{self.entity_ns}}}User').text
                created =  datetime.fromisoformat(hold.find(f'.//{{{self.entity_ns}}}CreatedDate').text.replace("Z", "+00:00"))
                lh = LegalHold(name, ref)
                lh.description = description
                lh.user = user
                lh.create_date = created
                result.add(lh)
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result, has_more, total_results, url)
        else:
            raise RuntimeError(request.status_code, "policies failed")


    def _create_hold_from_xml(self, xml_request: str) -> LegalHold:

        entity_response = xml.etree.ElementTree.fromstring(xml_request)
        logger.debug(xml_request)
        ref = entity_response.find(f'.//{{{self.entity_ns}}}Ref').text
        name = entity_response.find(f'.//{{{self.entity_ns}}}Name').text
        description = entity_response.find(f'.//{{{self.entity_ns}}}Description').text
        user = entity_response.find(f'.//{{{self.entity_ns}}}User').text
        created = datetime.fromisoformat(
            entity_response.find(f'.//{{{self.entity_ns}}}CreatedDate').text.replace("Z", "+00:00"))
        lh = LegalHold(name, ref)
        lh.description = description
        lh.user = user
        lh.create_date = created
        return lh

    def update_legal_hold(self, legal_hold: LegalHold) -> LegalHold:
        """

        Update an existing legal hold


        :param legal_hold:
        :type legal_hold:
        :return:
        :rtype:
        """

        self._check_if_user_has_config_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        structural_object = xml.etree.ElementTree.Element('LegalHold', {"xmlns": self.xip_ns})
        xml.etree.ElementTree.SubElement(structural_object, "Name").text = legal_hold.name
        xml.etree.ElementTree.SubElement(structural_object, "Description").text = legal_hold.description

        xml_request = xml.etree.ElementTree.tostring(structural_object, encoding='utf-8')
        logger.debug(xml_request)

        request = self.session.put(f'{self.protocol}://{self.server}/api/entity/legal-holds/{legal_hold.reference}',
                                   headers=headers, data=xml_request)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            return self._create_hold_from_xml(xml_response)
        else:
            logger.error(f"create_hold failed with error code {request.status_code}")
            raise RuntimeError(request.status_code, "create_hold failed")

    def create_hold(self, name: str,  description: str|None = None) -> LegalHold:
        """
        Create a new system legal hold

        This just creates the object and does not assign the hold to any assets

        :param name: The name of the new hold
        :type name:  str
        :param description: The description of the legal hold
        :type description:  str
        :return:
        :rtype: LegalHold
        """

        self._check_if_user_has_config_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        structural_object = xml.etree.ElementTree.Element('LegalHold', {"xmlns": self.xip_ns})
        xml.etree.ElementTree.SubElement(structural_object, "Name").text = name
        if description is not None:
            xml.etree.ElementTree.SubElement(structural_object, "Description").text = description

        xml_request = xml.etree.ElementTree.tostring(structural_object, encoding='utf-8')
        logger.debug(xml_request)

        request = self.session.post(f'{self.protocol}://{self.server}/api/entity/legal-holds', data=xml_request,
                                   headers=headers)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            return self._create_hold_from_xml(xml_response)
        else:
            logger.error(f"create_hold failed with error code {request.status_code}")
            raise RuntimeError(request.status_code, "create_hold failed")


    def legal_hold(self, reference) -> LegalHold:
        """
        Fetch a legal hold by its reference

        :param reference:
        :type reference:
        :return:
        :rtype:
        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/legal-holds/{reference}', headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            return self._create_hold_from_xml(xml_response)
        else:
            logger.error(f"hold failed with error code {request.status_code}")
            raise RuntimeError(request.status_code, "hold failed")


    def delete_legal_hold(self, reference: str):
        """
        Delete an existing legal hold by its reference or name

        :param reference:
        :type reference:
        :return:
        :rtype:
        """

        self._check_if_user_has_config_manager_role()

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        ref = None
        try:
            uuid.UUID(f'urn:uuid:{reference}')
            ref = reference
        except ValueError:
            holds = list(self.legal_holds(name=reference))
            if len(holds) == 0:
                raise RuntimeError("No legal holds found with that name")
            if len(holds) > 1:
                raise RuntimeError("No unique legal hold found with that name")
            ref = holds[0].reference
        finally:
            if ref is not None:
                request = self.session.delete(f'{self.protocol}://{self.server}/api/entity/legal-holds/{ref}', headers=headers)
                if request.status_code == requests.codes.no_content:
                    return
                else:
                    logger.error(f"delete_hold failed with error code {request.status_code}")
                    raise RuntimeError(request.status_code, "delete_hold failed")




    def legal_holds(self, name: str|None = None) -> Generator[LegalHold, None, None]:
        """
        List all the system legal holds

        :return: Generator of legal holds
        :rtype: Generator[LegalHold]
        """

        paged_set = self._legal_holds_(name, maximum=20, next_page=None)

        for hold in paged_set.results:
            yield hold

        while paged_set.has_more:
            paged_set = self._legal_holds_(name, maximum=20, next_page=paged_set.next_page)
            for hold in paged_set.results:
                yield hold


    def asset_holds(self, asset: Asset) -> list[LegalHoldAssignment]:
        """
        Return all the holds on an entity

        :param asset: The asset to query for holds
        :type asset:  Asset
        :return:      The list of holds put on this asset
        :rtype:       list
        """

        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{asset.path}/{asset.reference}/legal-holds',
            headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            assignments = []
            for hold in entity_response.findall(f'.//{{{self.entity_ns}}}LegalHoldAssignment'):
                entity_ref = hold.find(f'.//{{{self.entity_ns}}}Entity').text
                assert entity_ref ==  asset.reference
                assigned_date = hold.find(f'.//{{{self.entity_ns}}}AssignedDate').text
                hold_ref = hold.find(f'.//{{{self.entity_ns}}}LegalHold').text
                assignment: LegalHoldAssignment = LegalHoldAssignment(entity_ref, hold_ref, parse_date_to_iso_date(assigned_date))
                assignments.append(assignment)

            return assignments

        else:
            logger.error(f"holds failed with error code {request.status_code}")
            raise RuntimeError(request.status_code, "holds failed")




class RetentionAPI(AuthenticatedAPI):

    def __init__(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False,
                 two_fa_secret_key: str = None, protocol: str = "https", request_hook: Callable = None, credentials_path: str = 'credentials.properties'):
        """
        Initialise the RetentionAPI client and authenticate against the Preservica server.

        Credentials may be supplied directly as arguments or loaded from environment variables
        (``PRESERVICA_USERNAME``, ``PRESERVICA_PASSWORD``, ``PRESERVICA_TENANT``,
        ``PRESERVICA_SERVER``) or a ``credentials.properties`` file.

        :param username: Preservica account username.
        :type username: str
        :param password: Preservica account password.
        :type password: str
        :param tenant: Preservica tenant name.
        :type tenant: str
        :param server: Hostname of the Preservica server (e.g. ``us.preservica.com``).
        :type server: str
        :param use_shared_secret: Use a shared-secret token instead of username/password.
        :type use_shared_secret: bool
        :param two_fa_secret_key: TOTP secret key for two-factor authentication.
        :type two_fa_secret_key: str
        :param protocol: HTTP protocol to use, either ``"https"`` (default) or ``"http"``.
        :type protocol: str
        :param request_hook: Optional callable invoked as a requests event hook on each response.
        :type request_hook: Callable
        :param credentials_path: Path to a ``credentials.properties`` file used as a fallback
            when credentials are not provided as arguments or environment variables.
        :type credentials_path: str
        :raises RuntimeError: If the connected Preservica system is older than v6.2.
        """
        super().__init__(username, password, tenant, server, use_shared_secret, two_fa_secret_key,
                         protocol, request_hook, credentials_path)

        if self.major_version < 7 and self.minor_version < 2:
            raise RuntimeError("Retention API is only available when connected to a v6.2 System")


    def find(self, policy: RetentionPolicy|None = None) -> Generator:
        """
        Find all entities which have a retention policy

        Find entities with a specific policy

        :param policy:  Find entities with this specific policy
        :type policy:   RetentionPolicy
        :return:  entities with the policy or policies
        :rtype:   Generator of entities
        """


        def _find_entities(policy_ref: str|None = None, start_index: int = 0, page_size: int = 25) -> PagedSet:
            start_from = str(start_index)
            headers = {'Content-Type': 'application/x-www-form-urlencoded', HEADER_TOKEN: self.token}
            filter_values = {"xip.retention_policy_assignment_ref": f"{policy_ref}", "xip.retention_policy_assignment_name": "", "xip.title": "", "xip.reference": "*"}
            field_list = []
            for key, value in filter_values.items():
                field_list.append('{' f' "name": "{key}", "values": ["{value}"] ' + '}')
            filter_terms = ','.join(field_list)
            query_term = ('{ "q":  "%s",  "fields":  [ %s ] }' % ("*", filter_terms))
            payload = {'start': start_from, 'max': str(page_size), 'metadata': list(filter_values.keys()), 'q': query_term}
            results = self.session.post(f'{self.protocol}://{self.server}/api/content/search', data=payload, headers=headers)
            if results.status_code == requests.codes.ok:
                json_doc = results.json()
                results_list = []
                hits = int(json_doc['value']['totalHits'])
                metadata = json_doc['value']['metadata']
                refs = list(map(lambda x: content_api_identifier_to_type(x), list(json_doc['value']['objectIds'])))

                for m_row, r_row in zip(metadata, refs):
                    results_map = {'xip.reference': r_row[1]}
                    for li in m_row:
                        results_map[li['name']] = li['value']
                    results_list.append(results_map)

                ps = PagedSet(results=results_list, has_more=(hits > (page_size+start_index)), total=hits, next_page="")
                return ps

            else:
                logger.error(f"find failed with error code {results.status_code}")
                raise RuntimeError(results.status_code, "find failed")


        if policy is None:
            policy_ref_value = "*"
        else:
            policy_ref_value = policy.reference

        page_size_value = 25
        start_index_value = 0
        paged_set = _find_entities(policy_ref = policy_ref_value,  start_index=start_index_value, page_size=page_size_value)
        for entity in paged_set.results:
            ra = RetentionAssignment(entity['xip.reference'], entity['xip.retention_policy_assignment_ref'], api_id=None, start_date=None)
            ra.policy_name = entity['xip.retention_policy_assignment_name']
            yield ra
        start_index_value = start_index_value + page_size_value
        while paged_set.has_more:
            paged_set = _find_entities(policy_ref = policy_ref_value, start_index=start_index_value, page_size=page_size_value)
            for entity in paged_set.results:
                ra = RetentionAssignment(entity['xip.reference'], entity['xip.retention_policy_assignment_ref'],
                                         api_id=None, start_date=None)
                ra.policy_name = entity['xip.retention_policy_assignment_name']
                yield ra

    def policy(self, reference: str) -> RetentionPolicy:
        """
         Return a retention policy by reference

        :param reference: The policy reference
        :type reference: str

        :return: The retention policy
        :rtype: RetentionPolicy

         """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/entity/retention-policies/{reference}',
                                   headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            logger.debug(xml_response)
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            ref_element = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Ref')
            ref: str = ref_element.text
            assert ref is not None
            assert ref == reference
            name = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Name').text
            rp = RetentionPolicy(name, ref)
            description = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}Description')
            rp.description = description.text if description is not None else ""
            security_tag = entity_response.find(f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}SecurityTag').text
            rp.security_tag = security_tag
            start_date_field = entity_response.find(
                f'.//{{{self.rm_ns}}}RetentionPolicy/{{{self.rm_ns}}}StartDateField')
            if start_date_field is not None:
                rp.start_date_field = start_date_field.text
            else:
                rp.start_date_field = None
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

        :returns: No return value.
        :rtype: None
        :raises RuntimeError: If the API request fails.
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'text/plain;charset=UTF-8'}
        data = str(status)
        request = self.session.put(
            f'{self.protocol}://{self.server}/api/entity/retention-policies/{reference}/assignable',
            headers=headers, data=data)
        if request.status_code == requests.codes.ok:
            return None
        else:
            logger.error(f"assignable_policy failed with error code {request.status_code}")
            raise RuntimeError(request.status_code, "assignable_policy failed")

    def update_policy(self, reference: str, **kwargs):
        """
        Update an existing retention policy and return the updated policy.

        All keyword arguments listed below are required.

        :param reference: The unique reference (UUID) of the policy to update.
        :type reference: str
        :param kwargs: Policy field values. The following keys are all required:

            * ``Name`` (str) -- Display name of the policy.
            * ``Description`` (str) -- Human-readable description.
            * ``SecurityTag`` (str) -- Security tag applied to the policy.
            * ``StartDateField`` (str) -- Metadata field used as the retention start date.
            * ``Period`` (str) -- Numeric retention period value.
            * ``PeriodUnit`` (str) -- Unit of the retention period (e.g. ``"years"``).
            * ``ExpiryAction`` (str) -- Action taken when the retention period expires.
            * ``ExpiryActionParameters`` (str) -- Parameters for the expiry action.
            * ``Restriction`` (str) -- Restriction applied during the retention period.
            * ``Assignable`` (bool) -- Whether the policy may be assigned to new assets.

        :returns: The updated retention policy fetched from the server.
        :rtype: RetentionPolicy
        :raises RuntimeError: If any required kwarg is missing or if the API request fails.
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

        request = self.session.put(f'{self.protocol}://{self.server}/api/entity/retention-policies/{reference}',
                                   data=xml_request,
                                   headers=headers)
        if request.status_code == requests.codes.ok:
            return self.policy(reference)
        else:
            logger.error(str(request.content.decode('utf-8')))
            raise RuntimeError(request.status_code, "update_policy failed " + str(request.content.decode('utf-8')))

    def create_policy(self, **kwargs):
        """
        Create a new retention policy and return it.

        All keyword arguments listed below are required.

        :param kwargs: Policy field values. The following keys are all required:

            * ``Name`` (str) -- Display name of the policy.
            * ``Description`` (str) -- Human-readable description.
            * ``SecurityTag`` (str) -- Security tag applied to the policy.
            * ``StartDateField`` (str) -- Metadata field used as the retention start date.
            * ``Period`` (str) -- Numeric retention period value.
            * ``PeriodUnit`` (str) -- Unit of the retention period (e.g. ``"years"``).
            * ``ExpiryAction`` (str) -- Action taken when the retention period expires.
            * ``ExpiryActionParameters`` (str) -- Parameters for the expiry action.
            * ``Restriction`` (str) -- Restriction applied during the retention period.
            * ``Assignable`` (bool) -- Whether the policy may be assigned to new assets.

        :returns: The newly created retention policy fetched from the server.
        :rtype: RetentionPolicy
        :raises RuntimeError: If any required kwarg is missing or if the API request fails.
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
        else:
            logger.error(f'create_policy failed {request.status_code}')
            logger.error(str(request.content.decode('utf-8')))
            raise RuntimeError(request.status_code, "create_policy failed")

    def delete_policy(self, reference: str):
        """
        Delete a retention policy

        :param reference: The policy reference
        :type reference: str

        :returns: No return value.
        :rtype: None
        :raises RuntimeError: If the API request fails.
        """
        headers = {HEADER_TOKEN: self.token}
        request = self.session.delete(f'{self.protocol}://{self.server}/api/entity/retention-policies/{reference}',
                                      headers=headers)
        if request.status_code == requests.codes.no_content:
            return None
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

        for policy in self.policies():
            if policy.name == name:
                return self.policy(reference=policy.reference)
        return None

    def policies(self) -> Generator[RetentionPolicy, None, None]:
        """
            Return a list of all retention policies
            Returns a maximum of 100 policies for each call to the server

            :return: Generator of retention policies
            :rtype: Generator[RetentionPolicy]

        """

        paged_set = self._policies_set(maximum=100, next_page=None)

        for policy in paged_set.results:
            yield policy

        while paged_set.has_more:
            paged_set = self._policies_set(maximum=100, next_page=paged_set.next_page)
            for policy in paged_set.results:
                yield policy


    def _policies_set(self, maximum: int = 250, next_page: str = None) -> PagedSet:
        """
        Return a list of all retention policies
        Returns a maximum of 250 policies by default

        Internal helper function not part of the public API


        :return: Set of retention policies
        :rtype: Set[RetentionPolicy]

        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}

        if next_page is None:
            params = {'start': '0', 'max': str(maximum)}
            request = self.session.get(f'{self.protocol}://{self.server}/api/entity/retention-policies', params=params,
                                       headers=headers)
        else:
            request = self.session.get(next_page, headers=headers)

        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
            logger.debug(xml_response)
            result = set()
            next_url = entity_response.find(f'.//{{{self.entity_ns}}}Paging/{{{self.entity_ns}}}Next')
            total_results = int(entity_response.find(f'.//{{{self.entity_ns}}}TotalResults').text)
            for assignment in entity_response.findall(f'.//{{{self.entity_ns}}}RetentionPolicy'):
                ref = assignment.attrib['ref']
                result.add(self.policy(reference=ref))
            has_more = True
            url = None
            if next_url is None:
                has_more = False
            else:
                url = next_url.text
            return PagedSet(result, has_more, total_results, url)
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
        else:
            raise RuntimeError(request.status_code, "remove_assignments failed")


    def assignments(self, entity: Entity) -> Generator[RetentionPolicy, None, None]:

        """
          Return a list of retention policies for an entity.

          :param entity: The entity to fetch assignments for
          :type entity: class:`Entity`

          :return: Policy assignments
          :rtype: Generator[RetentionAssignment]

        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/xml;charset=UTF-8'}
        request = self.session.get(
            f'{self.protocol}://{self.server}/api/entity/{entity.path}/{entity.reference}/retention-assignments',
            headers=headers)
        if request.status_code == requests.codes.ok:
            xml_response = str(request.content.decode('utf-8'))
            entity_response = xml.etree.ElementTree.fromstring(xml_response)
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
                yield ra
        else:
            raise RuntimeError(request.status_code, "assignments failed")
