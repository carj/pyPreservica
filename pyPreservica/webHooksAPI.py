"""
pyPreservica WebHooksAPI module definition

A client library for the Preservica Repository web services Webhook API
https://us.preservica.com/api/webhook/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import hmac
from pyPreservica.common import *

logger = logging.getLogger(__name__)

BASE_ENDPOINT = '/api/webhook'


class WebHookHandler(BaseHTTPRequestHandler):
    """
    A sample web hook web server which provides handshake verification
    The shared secret key is passed in via the HTTPServer

    Extend the class and implement do_WORK() method
    The JSON document is passed into do_WORK()

    """

    def hmac(self, key, message):
        return hmac.new(key=bytes(key, 'latin-1'), msg=bytes(message, 'latin-1'), digestmod=hashlib.sha256).hexdigest()

    def do_POST(self):
        result = urlparse(self.path)
        q = parse_qs(result.query)
        if 'challengeCode' in q:
            code = q['challengeCode'][0]
            signature = self.hmac(self.server.secret_key, code)
            response = f'{{ "challengeCode": "{code}",     "challengeResponse": "{signature}" }}'
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(response.encode('utf-8')))
            self.log_message(f"Handshake Completed. {response.encode('utf-8')}")
        else:
            verif_sig = self.headers.get("Preservica-Signature", None)
            if "chunked" in self.headers.get("Transfer-Encoding", "") and (verif_sig is not None):
                payload = ""
                while True:
                    line = self.rfile.readline().strip()
                    chunk_length = int(line, 16)
                    if chunk_length != 0:
                        chunk = self.rfile.read(chunk_length)
                        payload = payload + chunk.decode("utf-8")
                    self.rfile.readline()
                    if chunk_length == 0:
                        verify_body = f"preservica-webhook-auth{payload}"
                        signature = self.hmac(self.server.secret_key, verify_body)
                        if signature == verif_sig:
                            self.log_message("Signature Verified. Doing Work...")
                            self.log_message(payload)
                            self.send_response(200)
                            self.end_headers()
                            self.do_WORK(json.loads(payload))
                        break


class TriggerType(Enum):
    """
    Enumeration of the Web hooks Trigger Types
    """
    MOVED = "MOVED"
    INDEXED = "FULL_TEXT_INDEXED"
    SECURITY_CHANGED = "CHANGED_SECURITY_DESCRIPTOR"


class WebHooksAPI(AuthenticatedAPI):
    """
    Class to register new webhook endpoints

    """

    def subscriptions(self):
        """
        Return all the current active web hook subscriptions as a json document

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

    def unsubscribe_all(self):
        """
        Unsubscribe from all webhooks.
        :return:
        """
        self._check_if_user_has_manager_role()
        subscriptions = self.subscriptions()
        for sub in subscriptions:
            self.unsubscribe(sub['id'])

    def unsubscribe(self, subscription_id: str):
        """
        Unsubscribe from the provided webhook.

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
            return self.unsubscribe(subscription_id)
        if response.status_code == requests.codes.no_content:
            json_response = str(response.content.decode('utf-8'))
            logger.debug(json_response)
            return json_response
        else:
            exception = HTTPException(str(subscription_id), response.status_code, response.url, "unsubscribe",
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
