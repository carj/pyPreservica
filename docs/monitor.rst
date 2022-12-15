Monitor API
~~~~~~~~~~~~~~~~~~


This is an API for monitoring certain types of long running process within Preservica, for example OPEX ingests.

You can find Swagger UI for this API at https://us.preservica.com/api/processmonitor/documentation.html

Monitors
^^^^^^^^^^^^^

Returns a generator of monitors. The ID returned for each monitor can be used as an ID parameter in other endpoints.
These IDs might change between releases, so you should not persist them as permanent object links.
Filters are additive, e.g. if both category and status filters are applied then only processes matching
both category and status will be included.

This call returns a Generator which can be used to enumerate over all the monitor objects. The result is a
monitor object which is dictionary created from the returned json.


.. code-block:: python

    client = MonitorAPI()

    for monitor in client.monitors():
        print(monitor)

Filters can be applied to limit the returned data, for example:

.. code-block:: python

    client = MonitorAPI()

    for monitor in client.monitors(category=MonitorCategory.INGEST, status=MonitorStatus.SUCCEEDED):
        print(monitor)





Messages
^^^^^^^^^^^^^^^

Returns a generator of process messages for each Monitor.

.. code-block:: python

    client = MonitorAPI()

    for monitor in client.monitors(category=MonitorCategory.INGEST, status=MonitorStatus.SUCCEEDED):
        print(monitor)
        for message in client.messages(monitor['MonitorId']):
            print(message)

Messages can be filtered

.. code-block:: python

    client = MonitorAPI()

    for monitor in client.monitors(category=MonitorCategory.INGEST, status=MonitorStatus.SUCCEEDED):
        print(monitor)
        for message in client.messages(monitor['MonitorId'], status=MessageStatus.ERROR):
            print(message)


Monitor Timeseries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the historical record of progress for a single monitor.

.. code-block:: python

    for monitor in client.monitors(category=MonitorCategory.INGEST, status=MonitorStatus.RUNNING):
        print(monitor)
        for series in client.timeseries(monitor['MonitorId']):
            print(series)

