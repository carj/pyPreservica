Admin API
~~~~~~~~~~~~~~~

pyPreservica 1.2 onwards now provides interfaces to the Administration and Management API

https://eu.preservica.com/api/admin/documentation.html

.. note::
    Administration and Management API is a system management API for repository
    managers who have at least the role ROLE_SDB_MANAGER_USER

The Administration and Management API client is created using

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()


Metadata Management (XSD Schema's, XML Documents & XSLT Transforms)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Preservica holds XML metadata schema's, XML templates and XSLT transforms, you can access the document stores
programmatically via the admin API.

To list all the XML templates use

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    client.xml_documents()

This will return a list of dictionary objects containing the template attributes, e.g.

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    for doc in client.xml_documents():
        print(doc['Name'])

You can access the XSD schema and XSLT templates in the same way

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    for schema in client.xml_schemas():
        print(schema['Name'])



.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    for transform in client.xml_transforms():
        print(transform['Name'])

Individual xml documents can be requested via their namespace URI.

For example, to save a MODS xml template held in Preservica with a given URI to a local file, use:

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    with open("mods-template.xml", encoding="utf-8", mode="wt") as f:
        f.write(client.xml_document("http://www.loc.gov/mods/v3"))


This now allows you to fetch a template from Preservica, update it and add it to a submission.

.. code-block:: python

    admin = AdminAPI()

    dublin_core_template = admin.xml_document("http://www.openarchives.org/OAI/2.0/oai_dc/")
    entity_response = xml.etree.ElementTree.fromstring(dublin_core_template)
    entity_response.find(".//{http://purl.org/dc/elements/1.1/}title").text = "My Asset Title"
    dublin_core_metadata = xml.etree.ElementTree.tostring(entity_response).decode("utf-8")

    package = simple_asset_package(preservation_file="my-image.tiff",
                                   Asset_Metadata={"http://www.openarchives.org/OAI/2.0/oai_dc/", dublin_core_metadata})

You can use similar code to fetch the XSD schema documents

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    with open("dublin-core.xsd", encoding="utf-8", mode="wt") as f:
        f.write(client.xml_schema("http://purl.org/dc/elements/1.1/"))


To fetch a transform you need to provide both an input URI and output URI

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    with open("ead-cmis.xslt", encoding="utf-8", mode="wt") as f:
        f.write(client.xml_transform("urn:isbn:1-931666-22-9", "http://www.w3.org/1999/xhtml"))


To add a new XML descriptive metadata template you can either pass an XML document held as a string or
a file like object. If using a file, then make sure the file descriptor is opened in binary mode.

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    with open("my-template.xml", mode="rb") as f:
        f.write(client.add_xml_document("my-template-name", f))

or via a string


.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    client.add_xml_document("my-template-name", xml_document)

To delete an existing XML template use the URI identifier


.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    client.delete_xml_document("http://purl.org/dc/elements/1.1/")


XSD Schema's and XSLT Transforms can be added and deleted in a similar way

Using a file like object

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    with open("my-schema.xsd", mode="rb") as f:
        f.write(client.add_xml_schema(name="my-schema", description="", originalName="my-schema.xsd", f))

or via a string

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    client.add_xml_schema(name="my-schema", description="", originalName="my-schema.xsd", xml_document)


and deletion is via the URI

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    client.delete_xml_schema("http://purl.org/dc/elements/1.1/")


User Management
^^^^^^^^^^^^^^^^^^^

List all the users within the tenancy by their username

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    for username in client.all_users():
        print(username)

Fetch the full set of user details, such as full name, email address and roles

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    user = client.user_details(username):
    print(user['FullName'])
    print(user['Email'])


Create new user accounts

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    username = "admin@example.com"
    roles = ['SDB_MANAGER_USER', 'SDB_INGEST_USER']

    user = client.add_user(username, full_name, roles)


Delete a user from the system

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    client.delete_user(username)


Change the display name of a user

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    client.change_user_display_name(username, "New Display Name")


Security Tags
^^^^^^^^^^^^^^^^^^^

To get a list of all security tags in the system use:


.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    tags = client.security_tags()

.. note::
    This call may produce a different set of tags than the ``user_security_tags()`` function from the content API
    which only returns security tags that the current user has available.

You can generate a report of security tag frequency usage using the pygal library for example.

.. code-block:: python

        import pygal
        from pygal.style import BlueStyle
        from pyPreservica import *

        client = AdminAPI()
        search = ContentAPI()
        security_tags = client.security_tags()
        results = {}
        for tag in security_tags:
            filters = {"xip.security_descriptor": tag, "xip.document_type": "IO"}
            hits = search.search_index_filter_hits(query="%", filter_values=filters)
            results[tag] = hits

        bar_chart = pygal.HorizontalBar(show_legend=False)
        bar_chart.title = "Security Tag Frequency"
        bar_chart.style = BlueStyle
        bar_chart.x_title = "Number of Assets"
        bar_chart.x_labels = results.keys()
        bar_chart.add("Security Tag", results)

        bar_chart.render_to_file("chart.svg")


This creates a graphical report which displays the frequency of each security tag with the ability to hover
over the values.


.. raw:: html
    :file: images/security_report.svg


The following calls are only available against a 6.4.x Preservica system.

To add a new security tag

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    tags = client.add_security_tag("my new tag")

and to delete a tag

.. code-block:: python

    from pyPreservica import *

    client = AdminAPI()

    tags = client.delete_security_tag("my new tag")