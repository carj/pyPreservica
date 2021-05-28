Content API
~~~~~~~~~~~~~~~

pyPreservica now contains some experimental interfaces to the content API

https://us.preservica.com/api/content/documentation.html

The content API is a readonly interface which returns json documents rather than XML and which has some duplication
with the entity API, but it does contain search capabilities.

The content API client is created using

.. code-block:: python

    from pyPreservica import *

    client = ContentAPI()


object-details
^^^^^^^^^^^^^^^^^

Get the details for a Asset or Folder as a raw json document

.. code-block:: python

    client = ContentAPI()

    client.object_details("IO", "uuid")
    client.object_details("SO", "uuid")


indexed-fields
^^^^^^^^^^^^^^^^^

Get a list of all the indexed metadata fields within the solr server. This includes the default
xip.* fields and any custom indexes which have been created through custom index files.

.. code-block:: python

    client = ContentAPI()

    client.indexed_fields():

Search
^^^^^^^^^

Search the repository using a single expression which matches on any indexed field.

.. code-block:: python

    client = ContentAPI()

    client.simple_search_csv()

Searches for everything and writes the results to a csv file called "search.csv", by default the csv
columns contain reference, title, description, document_type, parent_ref, security_tag.

You can pass the query term as the first argument (% is the wildcard character) and
the csv file name as the second argument.

.. code-block:: python

    client = ContentAPI()

    client.simple_search_csv("%", "everything.csv")

    client.simple_search_csv("Oxford", "oxford.csv")

    client.simple_search_csv("History of Oxford", "history.csv")

The last argument is an optional list of indexed fields which are the csv file columns.

.. code-block:: python

    client = ContentAPI()

    metadata_fields = ["xip.reference", "xip.title", "xip.description", "xip.document_type", "xip.parent_ref", "xip.security_descriptor"]
    client.simple_search_csv("%", "results.csv", metadata_fields)


or to include everything except the full text index value

.. code-block:: python

    client = ContentAPI()

    everything = list(filter(lambda x: x != "xip.full_text", client.indexed_fields()))
    client.simple_search_csv("%", "results.csv", everything)


There is an equivalent call which does not write the output to CSV, but returns a generator of dictionary objects.
This is useful if you want to process the results within the script and not generate a report directly.

.. code-block:: python

    client = ContentAPI()

    for hit in client.simple_search_list("History of Oxford"):
        print(hit)

and

.. code-block:: python

    client = ContentAPI()

    metadata_fields = ["xip.reference", "xip.title", "xip.description", "xip.document_type", "xip.parent_ref", "xip.security_descriptor"]
    for hit in client.simple_search_list("History of Oxford", metadata_fields):
        print(hit['xip.title'])


If you want to do searches with advanced filter terms then the following calls can be used.
These calls use a Python dictionary to allow the caller to specify filter values on the indexed terms.

.. code-block:: python

    client = ContentAPI()

    filters = {"dc.rights": "Public Domain", "xip.security_descriptor": "public"}
    client.search_index_filter_list(query="History of Oxford", filter_values=filters)


If you want to generate a report which can be opened directly in Excel, the use the csv version.

.. code-block:: python

    client = ContentAPI()

    filters = {"oai_dc.contributor": "*", "xip.security_descriptor": "public"}
    client.search_index_filter_csv(query="History of Oxford", csv_file="my-report.csv", filter_values=filters)

The special filter value "*" is used to filter indexes which have a value, i.e. are values are not empty or missing.
The filter value "%" is used to specify any value including empty values.

For example to create a report on the security tags of all assets within a folder you can use

.. code-block:: python

    client = ContentAPI()

    filters = {"xip.title": "%", "xip.description": "%", "xip.security_descriptor": "*", "xip.parent_ref": "48c79abd-01f3-4b77-8132-546a76e0d337"}
    client.search_index_filter_csv(query="%", csv_file="security.csv", filter_values=filters)


Search Progress
^^^^^^^^^^^^^^^^^^^^^

Searching across a large Preservica repository is very quick, but returning very large datasets back to the client
can be slow. To avoid putting undue load on the server pyPreservica will request a single page of results at a time for
each server request.

If you are using the ```simple_search_csv``` or ```search_index_filter_csv``` functions which write directly to a csv
file then it can be difficult to monitor the report generation progress.

To allow allow monitoring of search result downloads, you can add a callback to the search client.
The callback class will be called for every page of search results returned to the client. The value passed to the
callback contains the total number of search hits for the query and the current number of results processed.

.. code-block:: python

    class CallBack:
        def __init__(self):
            self.current = 0
            self.total = 0
            self._lock = threading.Lock()

        def __call__(self, value):
            with self._lock:
                values = value.split(":")
                self.total = int(values[1])
                self.current = int(values[0])
                percentage = (self.current / self.total) * 100
                sys.stdout.write("\r%s / %s  (%.2f%%)" % (self.current, self.total, percentage))
                sys.stdout.flush()

    client.search_callback(CallBack())
