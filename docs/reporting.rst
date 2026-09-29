=================
Reporting API
=================

The reporting API generates reports about the content of a Preservica repository.

``ReportingAPI`` authenticates in the same way as the other pyPreservica API classes, using explicit arguments,
environment variables or a ``credentials.properties`` file.

.. code-block:: python

    from pyPreservica import *

    client = ReportingAPI()

----------------------------------------------------
Storage Usage Report
----------------------------------------------------

pyPreservica can calculate how much storage is used by a folder hierarchy, or by the whole repository, and render the
result as an interactive HTML page in the style of the KDE Filelight disk usage application.

The page shows a radial "sunburst" chart where the centre is the current folder and each ring outwards is one level
deeper in the hierarchy. The size of each segment is proportional to the storage used by that folder or asset.
Clicking a folder drills down into it, and a list of the folder contents, sorted largest first, is shown alongside the chart.
The tenancy and server name are shown at the top of the page.
The page is self-contained and has no external dependencies, so it can be opened directly in a web browser or emailed.

To scan a folder and write the report use ``storage_usage_report``

.. code-block:: python

    client = ReportingAPI()
    client.storage_usage_report(folder="0f2997f7-728c-4e55-9f92-381ed1260d70", filename="usage.html")

Pass ``folder=None``, or leave out the folder argument, to scan the whole repository.

.. code-block:: python

    client.storage_usage_report(filename="repository.html")

The size of an asset is the total size of the bitstreams in the active generations of its representations.
By default both Preservation and Access representations are included, use ``representation_types`` to count only one of them.

.. code-block:: python

    client.storage_usage_report(folder="0f2997f7-728c-4e55-9f92-381ed1260d70", filename="usage.html",
                                representation_types=[RepresentationType.Preservation])

Calculating the size of an asset needs several API calls, so assets are sized in parallel using ``max_workers`` threads
(the default is 4).

``storage_usage_report`` returns a ``StorageUsageReport`` object. Scanning a large repository can take a long time,
so the scan results can be saved as JSON and the report re-rendered later without connecting to Preservica again.

.. code-block:: python

    report = client.storage_usage_report(folder="0f2997f7-728c-4e55-9f92-381ed1260d70", max_workers=8)
    report.save_json("usage.json")

    for asset in report.largest(10):
        print(asset.title, asset.reference, asset.size)

    for folder in report.largest(10, EntityType.FOLDER):
        print(folder.title, folder.reference, folder.size)

    # later, without connecting to Preservica
    report = StorageUsageReport(None)
    report.load_json("usage.json")
    report.render_html("usage.html")
