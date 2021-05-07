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
    client.simple_search_csv("%", "results.csv")

    client = ContentAPI()
    client.simple_search_csv("Oxford", "oxford.csv")

    client = ContentAPI()
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


There is an equivalent call which does not write the output to CSV, but returns a list of dictionary objects. This is useful if you want
to process the results within the script and not generate a report directly.

.. code-block:: python

    client = ContentAPI()
    results = simple_search_list("History of Oxford")

and

.. code-block:: python

    client = ContentAPI()
    metadata_fields = ["xip.reference", "xip.title", "xip.description", "xip.document_type", "xip.parent_ref", "xip.security_descriptor"]
    results = simple_search_list("History of Oxford", metadata_fields)


If you want to do searches with advanced filter terms then the following calls can be used.

.. code-block:: python

    client = ContentAPI()


