"""
pyPreservica WebHooksAPI module definition

A client library for the Preservica Repository web services Webhook API
https://us.preservica.com/api/webhook/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""
from http.server import BaseHTTPRequestHandler
from typing import Generator
from urllib.parse import urlparse, parse_qs
import hmac

from pyPreservica import EntityAPI
from pyPreservica.common import *

logger = logging.getLogger(__name__)

BASE_ENDPOINT = '/api/webhook'


class LambdaURLHandler:

    def __init__(self, secret_key: str, client: EntityAPI):
        """
        Initialise the AWS Lambda URL webhook handler.

        :param secret_key: The shared HMAC secret configured when the webhook subscription was created in Preservica.
        :type secret_key: str
        :param client: An authenticated :class:`EntityAPI` instance used to fetch entities from the repository.
        :type client: EntityAPI
        """
        self.secret_key = secret_key
        self.client = client

    def process_event(self, event) -> Generator[Entity, None, None]:
        """
        Validate the incoming Lambda URL event and yield repository entities for each event reference.

        The method verifies the ``preservica-signature`` HMAC header before processing. Only events
        whose signature matches the configured secret are processed; unverified events are silently
        skipped.

        :param event: The raw AWS Lambda URL event dict, expected to contain ``headers`` and ``body`` keys.
        :type event: dict
        :returns: A generator that yields one :class:`Entity` per event reference found in the body.
        :rtype: Generator[Entity, None, None]
        """
        if 'preservica-signature' in event['headers']:
            verify_body = f"preservica-webhook-auth{event['body']}"
            signature = hmac.new(key=bytes(self.secret_key, 'latin-1'), msg=bytes(verify_body, 'latin-1'),
                                 digestmod=hashlib.sha256).hexdigest()
            if signature == event['headers']['preservica-signature']:
                doc_body = event['body']
                for reference in list(doc_body['events']):
                    entity_ref = reference['entityRef']
                    entity_type = reference['entityType']
                    entity = self.client.entity(EntityType(entity_type), entity_ref)
                    yield entity

    def is_challenge(self, event) -> bool:
        """
        Determine whether an incoming Lambda URL event is a Preservica handshake challenge request.

        Preservica sends a challenge request with a ``challengeCode`` query-string parameter when a
        new webhook subscription is registered. Use this method to decide whether to call
        :meth:`verify_challenge` instead of :meth:`process_event`.

        :param event: The raw AWS Lambda URL event dict, expected to contain a ``queryStringParameters`` key.
        :type event: dict
        :returns: ``True`` if the event contains a non-empty ``challengeCode`` query parameter, ``False`` otherwise.
        :rtype: bool
        """
        if 'queryStringParameters' in event:
            if event['queryStringParameters'] is not None:
                if 'challengeCode' in event['queryStringParameters']:
                    message = event['queryStringParameters']['challengeCode']
                    return True if message else False
        return False

    def verify_challenge(self, event):
        """
        Respond to a Preservica handshake challenge for an AWS Lambda URL endpoint.

        Signs the ``challengeCode`` query-string parameter with the shared HMAC-SHA256 secret and
        returns an AWS Lambda URL-compatible response dict containing both the original challenge
        code and the computed response. If no challenge code is present a minimal 200 response is
        returned.

        :param event: The raw AWS Lambda URL event dict, expected to contain a ``queryStringParameters`` key.
        :type event: dict
        :returns: An AWS Lambda URL response dict with ``statusCode``, ``headers``, and ``body`` keys.
        :rtype: dict
        """
        if 'queryStringParameters' in event:
            if event['queryStringParameters'] is not None:
                if 'challengeCode' in event['queryStringParameters']:
                    message = event['queryStringParameters']['challengeCode']
                    signature = hmac.new(key=bytes(self.secret_key, 'latin-1'), msg=bytes(message, 'latin-1'),
                                         digestmod=hashlib.sha256).hexdigest()
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps({
                            "challengeCode": f"{message}", "challengeResponse": f"{signature}"})
                    }
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            }
        }


class FlaskWebhookHandler:

    def __init__(self, request, secret_key: str):
        """
        Initialise the Flask webhook handler.

        :param request: The Flask ``request`` proxy object for the current HTTP request.
        :param secret_key: The shared HMAC secret configured when the webhook subscription was created in Preservica.
        :type secret_key: str
        """
        self.request = request
        self.secret_key = secret_key

    def response_ok(self):
        """
        Return a generic 200 OK JSON response suitable for Flask route handlers.

        :returns: A three-tuple of ``(body, status_code, headers)`` ready for direct return from a Flask view.
        :rtype: tuple
        """
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

    def is_challenge(self) -> bool:
        """
        Determine whether the current Flask request is a Preservica handshake challenge.

        Preservica sends a challenge request with a ``challengeCode`` query-string parameter when a
        new webhook subscription is registered. Use this method to decide whether to call
        :meth:`verify_challenge` instead of :meth:`process_request`.

        :returns: ``True`` if the request contains a ``challengeCode`` query parameter, ``False`` otherwise.
        :rtype: bool
        """
        challenge_code = self.request.args.get('challengeCode')
        return challenge_code is not None

    def verify_challenge(self):
        """
        Respond to a Preservica handshake challenge for a Flask endpoint.

        Signs the ``challengeCode`` query-string parameter with the shared HMAC-SHA256 secret and
        returns a Flask-compatible three-tuple response containing both the original challenge code
        and the computed response. If no challenge code is present a generic success response is
        returned instead.

        :returns: A three-tuple of ``(body, status_code, headers)`` ready for direct return from a Flask view.
        :rtype: tuple
        """
        challenge_code = self.request.args.get('challengeCode')
        if challenge_code is not None:
            challenge_response: str = hmac.new(key=bytes(self.secret_key, 'latin-1'), msg=bytes(challenge_code, 'latin-1'),
                                 digestmod=hashlib.sha256).hexdigest()
            body = json.dumps({"challengeCode": f"{challenge_code}", "challengeResponse": f"{challenge_response}"})
            return body, 200, {"application/json": 'text/plain; charset=utf-8'}

        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}



    def process_request(self) -> Generator:
        """
        Validate the HMAC signature of the current Flask request and yield each webhook event.

        Reads the raw request body, verifies it against the ``Preservica-Signature`` header using
        the shared secret, and — if verification succeeds — parses the JSON body and yields each
        entry from the ``events`` list. Requests with a missing or invalid signature are silently
        skipped and the generator yields nothing.

        :returns: A generator that yields one event dict per entry in the ``events`` array of the
            verified JSON payload.
        :rtype: Generator
        """
        preservica_signature = self.request.headers.get('Preservica-Signature')
        if preservica_signature is not None:
            message_body = data = self.request.data
            verify_body = f"preservica-webhook-auth{message_body.decode('utf-8')}"
            digest = hmac.new(key=bytes(self.secret_key, 'latin-1'), msg=bytes(verify_body, 'latin-1'),
                              digestmod=hashlib.sha256).hexdigest()
            if preservica_signature == digest:
                json_body = json.loads(message_body.decode('utf-8'))
                for event in json_body['events']:
                    yield event


class WebHookHandler(BaseHTTPRequestHandler):
    """
    A sample web hook web server which provides handshake verification
    The shared secret key is passed in via the HTTPServer

    Extend the class and implement do_WORK() method
    The JSON document is passed into do_WORK()

    """

    def hmac(self, key, message):
        """
        Compute an HMAC-SHA256 hex digest for a given key and message.

        :param key: The secret key used to sign the message.
        :type key: str
        :param message: The message to be signed.
        :type message: str
        :returns: The lowercase hexadecimal HMAC-SHA256 digest.
        :rtype: str
        """
        return hmac.new(key=bytes(key, 'latin-1'), msg=bytes(message, 'latin-1'), digestmod=hashlib.sha256).hexdigest()

    def do_POST(self):
        """
        Handle an incoming HTTP POST request from Preservica.

        Handles two distinct request types:

        1. **Challenge requests** — when the query string contains a ``challengeCode`` parameter,
           signs the code with the server's shared secret and returns the challenge-response JSON
           payload, completing the webhook subscription handshake.
        2. **Event notifications** — for chunked-transfer-encoded POST bodies carrying a
           ``Preservica-Signature`` header, reassembles the payload, verifies the HMAC-SHA256
           signature, logs the result, sends a 200 response, and calls :meth:`do_WORK` with the
           parsed JSON document. Requests with an invalid or missing signature are silently dropped.

        Subclasses should override :meth:`do_WORK` to implement application-specific event processing.
        """
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
    INGEST_FAILED = "INGEST_FAILED"
    CHANGE_ASSET_VISIBILITY  = "CHANGE_ASSET_VISIBILITY"


class WebHooksAPI(AuthenticatedAPI):
    """
    Class to register new webhook endpoints

    """

    def subscriptions(self):
        """
        Return all current active webhook subscriptions.

        Requires the calling user to hold the ``CONFIG_MANAGER`` role.

        :returns: A list of subscription dicts, each describing an active webhook registration.
        :rtype: list
        :raises HTTPException: If the server returns a non-200 response.
        """
        self._check_if_user_has_config_manager_role()
        headers = {HEADER_TOKEN: self.token}
        response = self.session.get(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/subscriptions', headers=headers)
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
        Unsubscribe from all active webhook subscriptions.

        Retrieves the current subscriptions via :meth:`subscriptions` and calls :meth:`unsubscribe`
        for each one. Requires the calling user to hold the ``CONFIG_MANAGER`` role.

        :raises HTTPException: If any individual unsubscribe request fails.
        """
        self._check_if_user_has_config_manager_role()
        subscriptions = self.subscriptions()
        for sub in subscriptions:
            self.unsubscribe(sub['id'])

    def unsubscribe(self, subscription_id: str):
        """
        Unsubscribe from a specific webhook subscription by its identifier.

        Requires the calling user to hold the ``CONFIG_MANAGER`` role.

        :param subscription_id: The unique identifier of the webhook subscription to remove.
        :type subscription_id: str
        :returns: The raw response body returned by the server (typically empty for a 204 No Content).
        :rtype: str
        :raises HTTPException: If the server returns a non-204 response.
        """
        self._check_if_user_has_config_manager_role()
        headers = {HEADER_TOKEN: self.token}
        response = self.session.delete(
            f'{self.protocol}://{self.server}{BASE_ENDPOINT}/subscriptions/{subscription_id}',
            headers=headers)
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
        Create a new webhook subscription.

        Registers the given URL to receive event notifications for the specified trigger type.
        The subscription is created with ``includeIdentifiers`` set to ``true`` so that entity
        references are included in each notification payload. Requires the calling user to hold
        the ``CONFIG_MANAGER`` role.

        :param url: The publicly reachable HTTPS endpoint that Preservica will POST events to.
        :type url: str
        :param triggerType: The type of repository event that should trigger the webhook.
        :type triggerType: TriggerType
        :param secret: The shared HMAC secret used to sign outbound payloads; must also be
            configured in the receiving handler (e.g. :class:`LambdaURLHandler` or
            :class:`FlaskWebhookHandler`).
        :type secret: str
        :returns: The raw JSON response body from the server describing the new subscription.
        :rtype: str
        :raises HTTPException: If the server returns a non-200 response.
        """
        self._check_if_user_has_config_manager_role()
        headers = {HEADER_TOKEN: self.token, 'Accept': 'application/json', 'Content-Type': 'application/json'}

        json_payload = f'{{"url": "{url}", "triggerType": "{triggerType.value}", "secret": "{secret}",  ' \
                       f'"includeIdentifiers": "true"}}'

        response = self.session.post(f'{self.protocol}://{self.server}{BASE_ENDPOINT}/subscriptions', headers=headers,
                                     data=json.dumps(json.loads(json_payload)))
        if response.status_code == requests.codes.ok:
            json_response = str(response.content.decode('utf-8'))
            logger.debug(json_response)
            return json_response
        else:
            exception = HTTPException(str(url), response.status_code, response.url, "subscribe",
                                      response.content.decode('utf-8'))
            logger.error(response.content.decode('utf-8'))
            raise exception
