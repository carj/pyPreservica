Web Hook API
~~~~~~~~~~~~~~~

pyPreservica now contains APIs for accessing the web hook API.

Webhooks are "user-defined HTTP callbacks". They are triggered by some Preservica event, such as ingesting objects
into the repository. When that event occurs, Preservica makes an HTTP request to the URL configured for the webhook.

Unlike the traditional process of "polling" in which a client asks the repository if anything has changed, web hooks
automatically send out information to subscribed systems when certain events have happened.

To receive web hook notifications the 3rd party application requires a web server which can process HTTP POST requests.

To authenticate messages from Preservica to prevent spoofing attacks, the messages are verified through the use of a
shared secret key.

The Webhook API requires the user to have at least the repository manager role, ROLE_SDB_MANAGER_USER


Subscribing
^^^^^^^^^^^^^

Before a system can receive notifications from Preservica, it must subscribe to a notification trigger.

Preservica currently supports two different triggers, "Moved" and "Indexed".

The "Indexed" notification is sent after an object has been ingested and the full text index has been extracted,
at this point the thumbnail and search contents are available.

When creating a new subscription service you need to generate a shared secret key and pass it as an argument to the
subscribe method. This is used to verify the web service which will receive the web hooks.

The URL must be a publicly addressable web server.

.. code-block:: python

    webhook = WebHooksAPI()

    webhook.subscribe("http://my-webhook-server.com:8080/", TriggerType.INDEXED, "my_shared_secret")

The given URL host will need to respond to a validation challenge during the subscription request.
Preservica will make a POST request to the URL with a challengeCode query parameter.
The receiver must respond with the expected challenge response or the subscription will fail.
The challenge response must take the form:

.. code-block:: python

    {
            "challengeCode": "challengeCode",
            "challengeResponse": "hexHmac256Response"
    }

where hexHmac256Response is a hex hmac256 of the challengeCode using the shared secret as the hmac key.

If the web server is unable to correctly verify the subscription then an exception is thrown.


Listing Subscriptions
^^^^^^^^^^^^^^^^^^^^^

You can query the system for a list of current subscriptions for a tenancy.

.. code-block:: python

    webhook = WebHooksAPI()

    json_doc = webhook.subscriptions()

    print(json_doc)



Unsubscribe
^^^^^^^^^^^^^^^^^^^^^

To unsubscribe to a web hook, you need the subscription id

.. code-block:: python

    webhook = WebHooksAPI()

     webhook.un_subscribe("c306c99ca3a736124fa711bec53c737d")


