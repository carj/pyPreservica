=================
Reporting API
=================

API for generating reports about the content of the repository, such as storage usage.

--------------------
Storage Report
--------------------

Walks a Preservica folder hierarchy (or the whole repository), sums the size of the
bitstreams held by each asset and folder, and renders the result as an interactive,
self-contained HTML page with a radial "sunburst" chart in the style of a disk usage application.

You can pass a folder argument to limit the report to a particular collection, or leave the argument empty
to analyse the whole repository.

.. code-block:: python

    from pyPreservica import *


    entity: EntityAPI()

    folder = entity.folder('uuid')

    client: ReportingAPI = ReportingAPI()

    client.storage_usage_report(folder=folder)

The report will look something like this:

.. note::
    The report can take a while to run for large collections.

.. raw:: html

    <iframe src="_static/storage_usage_demo.html" style="width:100%; height:600px; border:1px solid #ccc;"
            title="Example storage usage report"></iframe>

`Open the example report full screen <_static/storage_usage_demo.html>`_