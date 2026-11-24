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
    client = ReportingAPI()

    folder = entity.folder('uuid')

    client.storage_usage_report(folder=folder, filename="storage_report.html")


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



--------------------------
Unknown File Format Report
--------------------------

Finds digital files (bitstreams) whose file format is not known, in a folder hierarchy or the whole repository.
The report uses the format identification which Preservica has already recorded for each file, so it does not need
to download any content. Two kinds of file are reported:

* **No PUID**: none of the format candidates for the file has a PRONOM unique identifier (PUID), so the format is unknown.
* **Extension only**: the file has a PUID, but it was identified only from its file extension. None of its format
  candidates was matched from the file content by a signature or container match, so the format may be wrong.

The report groups the files by file extension and by folder, which usually shows that most of the unknown files
come from a small number of file types or ingests. It also shows whether each file is in the original generation
or was created by a migration.

.. code-block:: python

    from pyPreservica import *

    client = ReportingAPI()

    report = client.unknown_format_report(folder='uuid', filename="unknown_formats.html")

    print(f"{len(report.no_puid_files)} files with no PUID")
    print(f"{len(report.extension_only_files)} files identified by extension only")

.. warning::
    The report can take a long time to run for large collections. The report is designed to be run infrequently.

.. raw:: html

    <iframe src="_static/unknown_formats_demo.html" style="width:100%; height:600px; border:1px solid #ccc;"
            title="Example unknown file format report"></iframe>

`Open the example report full screen <_static/unknown_formats_demo.html>`__


By default only the active generations of Preservation representations are checked. Use ``representation_types``
to include Access representations, and set ``include_extension_only`` to ``False`` to list only the files with no PUID.
The number of files identified by extension only is still shown in the report summary.

.. code-block:: python

    report = client.unknown_format_report(folder='uuid', filename="unknown_formats.html",
                                          include_extension_only=False)

The report returned can be saved as a CSV file with one row per file, which can be opened in a spreadsheet,
or as JSON so the HTML report can be re-created later without scanning the repository again.
The ``formats`` column of the CSV file lists the format candidates for each file.

.. code-block:: python

    report.save_csv("unknown_formats.csv")
    report.save_json("unknown_formats.json")

    for group in report.by_extension():
        print(group["extension"] or "(none)", group["files"], group["no_puid"], group["extension_only"], group["size"])

    for file in report.no_puid_files:
        print(file.filename, file.reference, file.folder_path, file.original)

    # later, without connecting to Preservica
    report = UnknownFormatReport(None)
    report.load_json("unknown_formats.json")
    report.render_html("unknown_formats.html")

.. note::
    The report reads the format identification stored in Preservica, it does not re-identify the files.
    A file with a PUID which was not identified by its extension, is treated as a known format.
