"""
pyPreservica Settings API  module definition

API for retrieving information about configuration settings.

author:     James Carr
licence:    Apache License 2.0

"""

from typing import Callable

from pyPreservica.common import *

logger = logging.getLogger(__name__)


class SettingsAPI(AuthenticatedAPI):
    """
    API for retrieving information about configuration settings.

    Includes  methods for:

    *  metadata-enrichment

    """

    def __init__(
        self,
        username=None,
        password=None,
        tenant=None,
        server=None,
        use_shared_secret=False,
        two_fa_secret_key: str = None,
        protocol: str = "https",
        request_hook: Callable = None,
        credentials_path: str = "credentials.properties",
    ):
        super().__init__(
            username,
            password,
            tenant,
            server,
            use_shared_secret,
            two_fa_secret_key,
            protocol,
            request_hook,
            credentials_path,
        )

        if self.major_version < 7 and self.minor_version < 7:
            raise RuntimeError(
                "Settings API is only available when connected to a v7.7 System or higher"
            )

        self.base_url = "api/settings"

    def metadata_enrichment_rules(self, profile_id: str = None) -> dict:
        """
        Returns a list of metadata enrichment rules.
        An empty selection implies that the rule is applied to all content.
        Rules define where particular behaviours, defined by profiles, will be applied.
        Rules are evaluated in order, with the first matching rule being applied.

        :param profile_id: The rules for a specific profile id, Set to None for all rules
        :type profile_id: str

        """
        headers = {
            HEADER_TOKEN: self.token,
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        endpoint: str = "/metadata-enrichment/config/rules"

        request = self.session.get(
            f"{self.protocol}://{self.server}/{self.base_url}{endpoint}",
            headers=headers)

        if request.status_code == requests.codes.ok:
            rules: dict = json.loads(request.content.decode("utf-8"))
            if profile_id is None:
                return rules
            else:
                profile_rules = []
                for rule in rules["rules"]:
                    if rule["profileId"] == profile_id:
                        profile_rules.append(rule)
                return {"rules": profile_rules}
        else:
            logger.debug(request.content.decode("utf-8"))
            raise RuntimeError(request.status_code, f"metadata_enrichment_rules failed")

    def metadata_enrichment_delete_rule(self, rule_id: str):
        """
        Deletes a metadata enrichment rule.

        :param rule_id: The rule id
        :type rule_id: str

        :return: No return value
        :rtype: None

        """
        headers = {
            HEADER_TOKEN: self.token,
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        endpoint: str = f"/metadata-enrichment/config/rules/{rule_id}"

        request = self.session.delete(
            f"{self.protocol}://{self.server}/{self.base_url}{endpoint}", headers=headers)

        if request.status_code == requests.codes.no_content:
            return
        else:
            logger.debug(request.content.decode("utf-8"))
            raise RuntimeError(request.status_code, f"metadata_enrichment_delete_rule failed")

    def metadata_enrichment_add_rule(self, profile_id: str, priority: int = 1):
        """
        Create a metadata enrichment rule to control when metadata enrichment profiles are applied and return it.
        Rules define where particular behaviours, defined by profiles, will be applied.
        Rules are evaluated in order, with the first matching rule being applied.
        Note that not specifying, or specifying an empty selection implies that the rule will be applied to all content.
        Currently only securityDescriptorSelector, representationSelector and hierarchySelector are supported selectors.
        If a rule already exists for the requested priority, existing rules will be shifted down priority to accommodate the new entry.

        :param profile_id: The profile id
        :type profile_id: str

        :param priority: The rule priority
        :type priority: int

        :return: The metadata enrichment rule
        :rtype: dict
        """

        headers = {
            HEADER_TOKEN: self.token,
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        endpoint: str = "/metadata-enrichment/config/rules"

        rule: dict = {
            "profileId": profile_id,
            "priority": str(priority),
            "selectorSettings": {},
        }

        request = self.session.post(
            f"{self.protocol}://{self.server}/{self.base_url}/{endpoint}",
            headers=headers,
            json=rule,
        )
        if request.status_code == requests.codes.created:
            return json.loads(request.content.decode("utf-8"))
        else:
            logger.debug(request.content.decode("utf-8"))
            raise RuntimeError(
                request.status_code, f"metadata_enrichment_add_rule failed"
            )

    def metadata_enrichment_add_profile(self, name: str, active: bool = True):
        """
        Create a metadata enrichment profile to control automatic metadata enrichment of content and return it.
        Profiles define a set of behaviours that will be applied when the profile is selected by a rule.
        A profile has no effect if it is not used by a rule. Includes settings for PII identification.
        PII detection tools may be run against the full text extracted from content.


        :param name: The profile name
        :type name: str

        :param active: The profile active status
        :type active: bool

        :return: The metadata enrichment profile
        :rtype: dict

        """

        headers = {
            HEADER_TOKEN: self.token,
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        endpoint: str = "/metadata-enrichment/config/profiles"

        profile: dict = {"name": name, "piiSettings": {"active": str(active).lower()}}

        request = self.session.post(
            f"{self.protocol}://{self.server}/{self.base_url}{endpoint}",
            headers=headers, json=profile)

        if request.status_code == requests.codes.created:
            return json.loads(request.content.decode("utf-8"))
        else:
            logger.debug(request.content.decode("utf-8"))
            raise RuntimeError(request.status_code, f"metadata_enrichment_add_profile failed")

    def metadata_enrichment_profile(self, profile_id: str) -> dict:
        """
        Returns a single profile by its ID
        Profiles define a set of behaviours that will be applied when the profile is selected by a rule.
        A profile has no effect if it is not used by a rule. Includes settings for PII identification.
        PII detection tools may be run against the full text extracted from content.

        :param profile_id: The profile name
        :type profile_id: str

        :return: The metadata enrichment profile
        :rtype: dict

        """
        headers = {
            HEADER_TOKEN: self.token,
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        endpoint: str = f"/metadata-enrichment/config/profiles/{profile_id}"

        request = self.session.get(
            f"{self.protocol}://{self.server}/{self.base_url}{endpoint}", headers=headers)

        if request.status_code == requests.codes.ok:
            return json.loads(request.content.decode("utf-8"))
        else:
            logger.debug(request.content.decode("utf-8"))
            raise RuntimeError(request.status_code, f"metadata_enrichment_profile failed")

    def metadata_enrichment_delete_profile(self, profile_id: str) -> None:
        """
        Deletes a metadata enrichment profile

        :param profile_id: The profile name
        :type profile_id: str

        :return: No return value
        :rtype: None

        """
        headers = {
            HEADER_TOKEN: self.token,
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        endpoint: str = f"/metadata-enrichment/config/profiles/{profile_id}"

        request = self.session.delete(
            f"{self.protocol}://{self.server}/{self.base_url}{endpoint}", headers=headers)

        if request.status_code == requests.codes.forbidden:
            logger.debug(request.content.decode("utf-8"))
            raise RuntimeError(request.status_code, f"Can't delete a profile with rules assigned")

        if request.status_code == requests.codes.no_content:
            return
        else:
            logger.debug(request.content.decode("utf-8"))
            raise RuntimeError(request.status_code, f"metadata_enrichment_delete_profile failed")

    def metadata_enrichment_profiles(self) -> dict:
        """
        Returns the list of all metadata enrichment profiles.
        Profiles define a set of behaviours that will be applied when the profile is selected by a rule.
        A profile has no effect if it is not used by a rule. Includes settings for PII identification.
        PII detection tools may be run against the full text extracted from content.
        """

        headers = {
            HEADER_TOKEN: self.token,
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

        endpoint: str = "/metadata-enrichment/config/profiles"

        request = self.session.get(
            f"{self.protocol}://{self.server}/{self.base_url}{endpoint}", headers=headers)

        if request.status_code == requests.codes.ok:
            return json.loads(request.content.decode("utf-8"))
        else:
            logger.debug(request.content.decode("utf-8"))
            raise RuntimeError(request.status_code, f"metadata_enrichment_profiles failed")
