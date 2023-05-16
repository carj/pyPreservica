"""
pyPreservica EntityAPI module definition

A client library for the Preservica Repository web services Webhook API
https://us.preservica.com/api/webhook/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""

from pyPreservica.common import *

logger = logging.getLogger(__name__)

BASE_ENDPOINT = '/api/webhook'


class TriggerType(Enum):
    """
    Enumeration of the Web hooks Trigger Types
    """
    MOVED = "MOVED"
    INDEXED = "FULL_TEXT_INDEXED"


class WebHooksAPI(AuthenticatedAPI):
    """
    Class to register new webhook endpoints

    """

    def subscriptions(self):
        """
        Return all the current active web hook subscriptions

        :return: list of web hooks
        """
        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token}
        response = self.session.get(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/subscriptions', headers=headers)
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.subscriptions()
        if response.status_code == requests.codes.ok:
            json_response = str(response.content.decode('utf-8'))
            doc = json.loads(json_response)
            return doc
        else:
            exception = HTTPException("", response.status_code, response.url, "subscriptions",
                                      response.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def un_subscribe(self, subscription_id: str):
        """
        Unsubscribe from provided webhook.

        :param subscription_id:
        :return:
        """
        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token}
        response = self.session.delete(
            f'{self.protocol}://{self.server}{BASE_ENDPOINT}/subscriptions/{subscription_id}',
            headers=headers)
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.un_subscribe(subscription_id)
        if response.status_code == requests.codes.no_content:
            json_response = str(response.content.decode('utf-8'))
            logger.debug(json_response)
            return json_response
        else:
            exception = HTTPException(str(subscription_id), response.status_code, response.url, "un_subscribe",
                                      response.content.decode('utf-8'))
            logger.error(exception)
            raise exception

    def subscribe(self, url: str, triggerType: TriggerType, secret: str):
        """
        Subscribe to a new web hook

        :param url:
        :param triggerType:
        :param secret:
        :return: json_response
        """
        self._check_if_user_has_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Accept': 'application/json', 'Content-Type': 'application/json'}

        json_payload = f'{{"url": "{url}", "triggerType": "{triggerType.value}", "secret": "{secret}",  ' \
                       f'"includeIdentifiers": "true"}}'

        response = self.session.post(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/subscriptions', headers=headers,
                                     data=json.dumps(json.loads(json_payload)))
        if response.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.subscribe(url, triggerType, secret)
        if response.status_code == requests.codes.ok:
            json_response = str(response.content.decode('utf-8'))
            logger.debug(json_response)
            return json_response
        else:
            exception = HTTPException(str(url), response.status_code, response.url, "subscribe",
                                      response.content.decode('utf-8'))
            logger.error(response.content.decode('utf-8'))
            raise exception
