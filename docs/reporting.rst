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


    entity = EntityAPI()

    folder = entity.folder('uuid')

    client = ReportingAPI()

    client.storage_usage_report(folder=folder)


.. warning::
    The report can take a while to run for large collections.

``storage_usage_report`` returns a ``StorageUsageReport`` object which can also be saved as a CSV file for use in a
spreadsheet. The CSV file has one row per folder and asset, in tree order with each folder followed by its contents,
largest first. The first row is the scanned folder, or the repository, with the overall totals.

The columns are ``type``, ``reference``, ``title``, ``folder_path``, ``depth``, ``size_bytes``, ``size``,
``percent_of_parent``, ``percent_of_total``, ``assets`` and ``files``.

.. code-block:: python

    report = client.storage_usage_report(folder=folder)

    report.save_csv("storage.csv")

For large collections you can limit the CSV file to folders only, or to the top levels of the hierarchy.

.. code-block:: python

    # folders only, no assets
    report.save_csv("folders.csv", entity_type=EntityType.FOLDER)

    # the scanned folder and the two levels of folders and assets below it
    report.save_csv("top_levels.csv", max_depth=2)

The scan results can also be saved as JSON, so the HTML and CSV reports can be re-created later without scanning
the repository again.

.. code-block:: python

    report.save_json("storage.json")

    # later, without connecting to Preservica
    report = StorageUsageReport(None)
    report.load_json("storage.json")
    report.save_csv("storage.csv")
    report.render_html("storage.html")


The completed report will look something like this:

.. raw:: html

    <iframe src="_static/storage_usage_demo.html" style="width:100%; height:600px; border:1px solid #ccc;"
            title="Example storage usage report"></iframe>

`Open the example report full screen <_static/storage_usage_demo.html>`__


--------------------------
Duplicate Content Report
--------------------------

Finds digital files (bitstreams) which are held more than once in a folder hierarchy or the whole repository.
Two files are reported as duplicates when they have the same size and the same fixity value, so the report does not
need to download any content. Files are matched on any fixity algorithm they have in common, so a file with only a
SHA-1 value will still match a copy which has both SHA-1 and SHA-256 values.

The report shows how much space could be reclaimed by keeping only one copy of each file, and lists each set of
duplicates with the asset, folder and representation that holds every copy.

.. code-block:: python

    from pyPreservica import *

    client = ReportingAPI()

    report = client.duplicate_content_report(folder='uuid', filename="duplicates.html")

    print(f"{report.duplicate_files} extra copies using {report.reclaimable} bytes")

.. warning::
    The report can take a long time to run for large collections. The report is designed to be run infrequently.

.. raw:: html

    <iframe src="_static/duplicate_demo.html" style="width:100%; height:600px; border:1px solid #ccc;"
            title="Example duplicate usage report"></iframe>

`Open the example report full screen <_static/duplicate_demo.html>`__


By default only the active generations of Preservation representations are compared, and empty files are ignored
because they would all be reported as duplicates of each other. Use ``representation_types`` to include
Access representations, and ``min_size`` to ignore small files.

.. code-block:: python

    report = client.duplicate_content_report(folder='uuid', filename="duplicates.html",
                                             representation_types=[RepresentationType.Preservation, RepresentationType.Access],
                                             min_size=1024 * 1024)

The report returned can be saved as a CSV file with one row per duplicate file, which can be opened in a spreadsheet,
or as JSON so the HTML report can be re-created later without scanning the repository again.

.. code-block:: python

    report.save_csv("duplicates.csv")
    report.save_json("duplicates.json")

    for group in report.largest(10):
        print(group.copies, group.size, group.reclaimable)
        for file in group.files:
            print("    ", file.filename, file.reference, file.folder_path)

    # later, without connecting to Preservica
    report = DuplicateContentReport(None)
    report.load_json("duplicates.json")
    report.render_html("duplicates.html")

.. note::
    The report reads the fixity values stored in Preservica, it does not re-calculate them. Files without a fixity
    value or have different fixity algorithms cannot be directly compared and are counted separately in the report.

