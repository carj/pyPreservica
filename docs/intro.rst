===========================
Why Should I Use This?
===========================

The goal of pyPreservica is to allow you to make use of the Preservica APIs for reading and writing objects within
a Preservica repository without having to manage the underlying REST HTTPS requests and XML parsing.
The library provides a level of abstraction which reflects the underlying data model, such as structural and
information objects.

The pyPreservica library allows Preservica users to build applications which interact with the repository such as metadata
synchronisation with 3rd party systems, high-throughput ingest pipelines etc.

.. note::
    Access to the Preservica API's for the cloud hosted system does depend on which Preservica Edition has been
    licensed.  See https://preservica.com/digital-archive-software/products-editions for details.


==================
SDK Features
==================

-----------------------
Entity API Features
-----------------------

-  Fetch and Update Entity Objects (Folders, Assets, Content Objects)
-  Add, Delete and Update External Identifiers
-  Add, Delete and Update Descriptive Metadata Fragments
-  Change Security tags on Folders and Assets
-  Create new Folder Entities
-  Move Assets and Folders within the repository
-  Deleting Assets and Folders
-  Fetch Folders and Assets belonging to parent Folders
-  Retrieve Representations, Generations & Bitstreams from Assets
-  Download digital files and thumbnails
-  Fetch lists of changed entities over the last n days
-  Request information on completed integrity checks
-  Add or remove asset and folder icons
-  Replace existing content objects within an Asset
-  Export OPEX Package
-  Fetch audit trail events on Entities and across the repository
-  Create Relationships between Assets

-----------------------
Content API Features
-----------------------

-  Fetch a list of indexed Solr Fields
-  Search based on a single query term
-  Filtered searches on indexed fields

-----------------------
Upload API Features
-----------------------

-  Create single Content Object Packages with multiple Representations
-  Create multiple Content Object Packages with multiple Representations
-  Upload packages to Preservica
-  Spreadsheet Metadata
-  Ingest Web Video
-  Ingest Twitter Feeds

-----------------------
Admin API Features
-----------------------

-  Schema Management (XML Templates, XSD Schema's & XSLT Transforms)
-  User Management (create and remove user accounts)
-  Security Tags (add and remove security tags)

------------------------------------
Retention Management API Features
------------------------------------

-  Create new retention policies
-  Delete retention policies
-  Update retention policies
-  Assign retention policies to entities

-----------------------
Workflow API Features
-----------------------

- Get Workflow Contexts
- Get Workflow Instance
- Start Workflow Instances

-----------------------
Webhook API Features
-----------------------

- Subscribe to Webhook endpoints
- Unsubscribe
- List Subscriptions

---------------------------------
Authority Records API Features
---------------------------------

-  Get an Authority table by its reference
-  List all Authority tables
-  Return all records from an Authority table
-  Add records to an Authority table
-  Delete records from an Authority table


---------------------------------------------
Metadata Groups and Forms Features
---------------------------------------------

-  Create new Groups
-  Delete Groups
-  Add new metadata fields to an existing Group
-  Fetch existing Groups


==================
Background
==================

The key to working with the pyPreservica library is that the services follow the Preservica core data model closely.

.. image:: images/entity-API.jpg

The Preservica data model represents a hierarchy of entities, starting with the **structural objects** which are used to
represent aggregations of digital assets. Structural objects define the organisation of the data. In a library context
they may be referred to as collections, in an archival context they may be Fonds, Sub-Fonds, Series etc and in a
records management context they could be simply a hierarchy of folders or directories.

These structural objects may contain other structural objects in the same way as a computer filesystem may contain
folders within folders.

Within the structural objects comes the **information objects**. These objects which are sometimes referred to as the
digital assets are what PREMIS defines as an Intellectual Entity. Information objects are considered a single
intellectual unit for purposes of management and description: for example, a book, document, map, photograph or database etc.

**Representations** are used to define how the information objects are composed in terms of technology and structure.
For example, a book may be represented as a single multiple page PDF, a single eBook file or a set of single page image files.

Representations are usually associated with a use case such as access or long-term preservation.
All Information objects have at least one representation defined by default. Multiple representations can be either
created outside of Preservica through a process such as digitisation or within Preservica through preservation processes such as normalisation.

**Content Objects** represent the components of the asset. Simple assets such as digital images may only contain a
single content object whereas more complex assets such as books or 3d models may contain multiple content objects.
In most cases content objects will map directly to digital files or bitstreams.

**Generations** represent changes to content objects over time, as formats become obsolete new generations may need
to be created to make the information accessible.

**Bitstreams** represent the actual computer files as ingested into Preservica, i.e. the TIFF photograph or the PDF document.

==================
Installation
==================

pyPreservica is available from the Python Package Index (PyPI)

https://pypi.org/project/pyPreservica/

pyPreservica is built and tested against Python 3.11 onwards. Older versions of Python may not work.


To install pyPreservica, simply run this simple command in your terminal of choice:

.. code-block:: console

    $ pip install pyPreservica

or you can install in a virtual python environment using:

.. code-block:: console

    $ pipenv install pyPreservica

pyPreservica is under active development and the latest version is installed using

.. code-block:: console

    $ pip install --upgrade pyPreservica

=======================
Get the Source Code
=======================

pyPreservica is developed on GitHub, where the code is
`always available <https://github.com/carj/pyPreservica>`_.

You can clone the public repository

.. code-block:: console

    $ git clone git://github.com/carj/pyPreservica.git


=======================
Contributing
=======================

Bug reports and pull requests are welcome on GitHub at https://github.com/carj/pyPreservica

=======================
Support
=======================

pyPreservica is 3rd party open source client. There is no official support provided.


.. important::

   There is no support for pyPreservica from `Preservica Ltd <https://preservica.com/>`_


For announcements about new versions and discussion of pyPreservica please subscribe to the google groups
forum https://groups.google.com/g/pypreservica

Bug reports can be raised directly on either `GitHub <https://github.com/carj/pyPreservica>`_
or on the google group forum

General questions and queries about using pyPreservica should be posted on the google group forum above.

=======================
Quick Start
=======================

This section walks through the most common tasks so you can get going quickly. Each step builds on the one before,
and you can type every example straight into the Python console.

The examples assume you have installed pyPreservica and that your credentials are available, either as environment
variables or in a ``credentials.properties`` file. See :ref:`intro:Authentication` below for the options.

.. tip::
    The UUIDs below are placeholders. Replace them with references from your own Preservica system.
    You can find an entity's reference in its metadata panel in Preservica Explorer.

-----------------------------
Step 1: Connect to Preservica
-----------------------------

Each part of the Preservica API has its own client class, such as ``EntityAPI``, ``ContentAPI`` and ``UploadAPI``.
Creating a client logs in to the server. Printing the client shows which server and user you are connected as,
which is a quick way to check you are working on the right system.

.. code-block:: python

    >>> from pyPreservica import *
    >>> client = EntityAPI()
    >>> client
    pyPreservica version: 4.3.0  (Preservica 9.x Compatible) Connected to: eu.preservica.com Preservica version: 8.2.0 as test@test.com in tenancy PREVIEW

If the credentials are wrong, creating the client raises an exception, so you know straight away.

--------------------------------
Step 2: Fetch an Asset or Folder
--------------------------------

Every entity in Preservica has a unique reference, a
`UUID <https://en.wikipedia.org/wiki/Universally_unique_identifier>`_, which you use to fetch it.

.. code-block:: python

    >>> asset = client.asset("9fd239eb-19a3-4a46-9495-40fd9a5d8f93")
    >>> asset.title
    'LC-USZ62-20901'
    >>> asset.description
    'Photograph of the Wright brothers first flight'
    >>> asset.security_tag
    'open'
    >>> asset.entity_type
    <EntityType.ASSET: 'IO'>
    >>> asset.parent
    'ae108c8f-b058-4228-b099-6049175d2f0c'

    >>> folder = client.folder(asset.parent)
    >>> folder.title
    'Library of Congress'

All entities have a ``parent`` attribute. For Assets it points to the parent Folder, and for Folders it points to the
parent Folder if there is one. Folders at the root of the repository have a parent of ``None``.

If you don't know whether a reference belongs to an Asset or a Folder, use ``client.entity()`` with an ``EntityType``:

.. code-block:: python

    >>> entity = client.entity(EntityType.FOLDER, "ae108c8f-b058-4228-b099-6049175d2f0c")

-----------------------------
Step 3: Browse the repository
-----------------------------

``descendants()`` returns the immediate children of a Folder, and ``all_descendants()`` walks the whole tree below it.
Both handle paging for you, so you can loop over the results directly. Call them with no argument to start from the
root of the repository.

.. code-block:: python

    # List the top-level folders
    for entity in client.descendants():
        print(entity.reference, entity.title)

    # Count every Asset below a folder, at any depth
    folder = client.folder("ae108c8f-b058-4228-b099-6049175d2f0c")
    assets = [e for e in client.all_descendants(folder) if e.entity_type == EntityType.ASSET]
    print(f"{len(assets)} assets found")

--------------------------------
Step 4: Read and update metadata
--------------------------------

Change the title or description of an entity, then save it back to the server:

.. code-block:: python

    asset = client.asset("9fd239eb-19a3-4a46-9495-40fd9a5d8f93")
    asset.title = "The Wright Brothers First Flight"
    asset.description = "Kitty Hawk, North Carolina, 17 December 1903"
    asset = client.save(asset)

Descriptive metadata, such as Dublin Core, is stored as XML documents. ``metadata_for_entity()`` returns the XML
for a given schema, or ``None`` if the entity has none:

.. code-block:: python

    xml = client.metadata_for_entity(asset, "http://www.openarchives.org/OAI/2.0/oai_dc/")
    print(xml)

To attach a new XML document, pass the schema namespace and the XML as a string:

.. code-block:: python

    dublin_core = """<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                                xmlns:dc="http://purl.org/dc/elements/1.1/">
                         <dc:creator>Orville Wright</dc:creator>
                     </oai_dc:dc>"""
    client.add_metadata(asset, "http://www.openarchives.org/OAI/2.0/oai_dc/", dublin_core)

--------------------------------
Step 5: Use external identifiers
--------------------------------

External identifiers link Preservica entities to references from other systems, such as a catalogue number,
ISBN or DOI. You can then find entities by those identifiers instead of by UUID.

.. code-block:: python

    client.add_identifier(asset, "ISBN", "978-3-16-148410-0")

    for identifier_type, value in client.identifiers_for_entity(asset):
        print(identifier_type, value)

    # Find entities by an external identifier
    for entity in client.identifier("ISBN", "978-3-16-148410-0"):
        print(entity.reference, entity.title)

-----------------------
Step 6: Create a Folder
-----------------------

``create_folder()`` creates a new Folder. Pass the reference of a parent Folder, or leave it out to create the Folder
at the root of the repository.

.. code-block:: python

    new_folder = client.create_folder("Photographs", "Digitised photograph collection", "open",
                                      parent="ae108c8f-b058-4228-b099-6049175d2f0c")
    print(new_folder.reference)

----------------------
Step 7: Download files
----------------------

``download()`` saves the access copy of an Asset, and ``thumbnail()`` saves its thumbnail image:

.. code-block:: python

    client.download(asset, "access-copy.jpg")
    client.thumbnail(asset, "thumbnail.jpg")

To get the original files, follow the data model down from the Asset through its Representations,
Content Objects and Generations to the Bitstreams:

.. code-block:: python

    for representation in client.representations(asset):
        for content_object in client.content_objects(representation):
            for generation in client.generations(content_object):
                for bitstream in generation.bitstreams:
                    print(representation.rep_type, bitstream.filename, bitstream.length)
                    client.bitstream_content(bitstream, bitstream.filename)

-----------------------------
Step 8: Search the repository
-----------------------------

The ``ContentAPI`` class searches Preservica's full-text index. It returns results one at a time as dictionaries
and handles paging for you.

.. code-block:: python

    search = ContentAPI()

    for hit in search.simple_search_list("Wright brothers"):
        print(hit["xip.reference"], hit["xip.title"])

You can also filter on index fields. Use an empty string to include a field in the results without filtering on it:

.. code-block:: python

    filters = {"xip.document_type": "IO", "xip.title": "", "xip.security_descriptor": "open"}

    for hit in search.search_index_filter_list("%", filter_values=filters):
        print(hit["xip.reference"], hit["xip.title"])

--------------------------------
Step 9: Upload and ingest a file
--------------------------------

The ``UploadAPI`` class sends new content to Preservica. ``simple_asset_package()`` wraps a single file in a
submission package, and ``upload_zip_package()`` uploads it and starts the ingest. The file becomes a new Asset
inside the Folder you choose.

.. code-block:: python

    upload = UploadAPI()
    folder = client.folder("ae108c8f-b058-4228-b099-6049175d2f0c")

    package = simple_asset_package("picture.tiff", parent_folder=folder,
                                   Title="Wright Flyer", Description="First flight photograph")
    upload.upload_zip_package(package)

The ingest runs on the server, so the new Asset appears in the Folder once the ingest workflow finishes.

----------
Next steps
----------

The rest of this documentation covers each API in more detail:

* :doc:`tutorial` for a longer worked example
* :doc:`entity` for the full Entity API, including moving entities and changing security tags
* :doc:`content` for search and reporting
* :doc:`upload` for more packaging options, such as multi-file Assets and access copies
* :doc:`workflow` for monitoring and starting workflows

=======================
Authentication
=======================

pyPreservica provides 4 different methods for authentication. The library requires the username and password of a
Preservica user and an optional Tenant identifier along with the server hostname.

.. tip::
    The Tenant parameter is now optional when connecting to a Preservica 6.3 system.


1 **Method Arguments**

Include the user credentials as arguments to the EntityAPI Class

.. code-block:: python

    from pyPreservica import *

    client = EntityAPI(username="test@test.com", password="123444",
                       tenant="PREVIEW", server="preview.preservica.com")




If you don't want to include your Preservica credentials within your python script because you are sharing scripts or 
using a version control system then one of the following two methods should be used.

2 **Environment Variable**

Export the credentials as environment variables as part of the session

.. code-block:: console

    $ export PRESERVICA_USERNAME="test@test.com"
    $ export PRESERVICA_PASSWORD="123444"
    $ export PRESERVICA_TENANT="PREVIEW"
    $ export PRESERVICA_SERVER="preview.preservica.com"

    $ python3

.. code-block:: python

    from pyPreservica import *

    client = EntityAPI()

3 **Properties File**

Create a properties file called "credentials.properties" with the following property names
and save to the working directory ::

    [credentials]
    username=test@test.com
    password=123444
    tenant=PREVIEW
    server=preview.preservica.com


.. code-block:: python

    from pyPreservica import *

    client = EntityAPI()

You can create a new credentials.properties file automatically using the ``save_config()`` method

.. code-block:: python

    from pyPreservica import *

    client = EntityAPI(username="test@test.com", password="123444",
                          tenant="PREVIEW", server="preview.preservica.com")
    client.save_config()



4 **Shared Secrets**

.. warning::
    The shared secret authentication method is deprecated and may be removed in future releases. It should not be used for new projects.
    See https://developers.preservica.com/blog/developer-blog-api-updates-in-preservica-8-4


pyPreservica supports authentication using shared secrets rather than a login account username and password.
This allows a trusted external applications such as pyPreservica to acquire a Preservica API authentication token
without having to use a set of login credentials.

This option is useful if you want to provide limited API access to a 3rd party without providing login access to Preservica.

To use the shared secret authentication you need to add a secure secret key to your Preservica system.

The username, password, tenant and server attributes are used as normal, the password field now holds the shared
secret and not the users password.

.. code-block:: python

    from pyPreservica import *

    client = EntityAPI(username="test@test.com", password="shared-secret", tenant="PREVIEW",
                          server="preview.preservica.com", use_shared_secret=True)

If you are using a credentials.properties file then

.. code-block:: python

    from pyPreservica import *

    client = EntityAPI(use_shared_secret=True)

========================
2 Factor Authentication
========================

pyPreservica now supports the new 2-Factor authentication for APIs introduced with Preservica 6.8

The Preservica system should be first setup for 2-Factor authentication and the one time password key used to
seed the 2FA (HMAC-Based One-Time Password Algorithm) should be retained and used with the API.

The one time password or seed key is available to view and should be saved when setting up the 2FA for a user.
You can find the two factor seed key from the user 2FA setup page under the "Reveal Key" button at the bottom of the page.

Keep this key secret along with your account password as it will be required when authenticating the API calls.

.. image:: images/2fa.PNG

To call pyPreservica once 2-Factor authentication process has been setup, you need the username and password as normal along
with the additional two factor key.

You can pass the additional two factor key as an argument to the constructor for the API classes or use environment
variables or the credentials file.

.. code-block:: python

    from pyPreservica import *

    client = EntityAPI(username="test@test.com", password="my-login-password", tenant="PREVIEW",
                          server="preview.preservica.com", two_fa_secret_key="AJC5DEGUVM6UQ1TT")



The environment variable for holding the 2 factor seed key is called `PRESERVICA_2FA_TOKEN` and the credential file
property name is `twoFactorToken`.

.. code-block:: console

    $ export PRESERVICA_2FA_TOKEN=AJC5DEGUVM6UQ1TT

i.e ::

    [credentials]
    username=test@test.com
    password=123444
    tenant=PREVIEW
    server=preview.preservica.com
    twoFactorToken=AJC5DEGUVM6UQ1TT

.. tip::
    Preservica uses time based One Time Passwords (OTP), this means the time on your local machine must match time
    on the server.

========================
SSL Certificates
========================

pyPreservica will by default connect to servers which use the https:// protocol and will always validate certificates
when connected via https.

For Enterprise on Premise customers on secure networks, you can change the default protocol to use http:// via the constructor.

.. code-block:: python

    client = EntityAPI(protocol="http")

pyPreservica uses the `Certifi <https://pypi.org/project/certifi/>`_  project to provide SSL certificate validation.

Self-signed certificates used by on-premise deployments are not part of the Certifi certification authority (CA)
bundle and therefore need to be set explicitly.

The CA bundle is a file that contains root and intermediate certificates.
The end-entity certificate along with a CA bundle constitutes the certificate chain.

For on-premise deployments the trusted CAs can be specified through the ``REQUESTS_CA_BUNDLE``
environment variable. e.g.

.. code-block:: console

    $ export REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/my-server.cert


========================
Application Logging
========================

You can add logging to your pyPreservica scripts by simply including the following

.. code-block:: python

    import logging
    from pyPreservica import *

    logging.basicConfig(level=logging.DEBUG)

    client = EntityAPI()

This will log all messages from level DEBUG or higher to standard output, i.e the console.

When logging to files, the main thing to be wary of is that log files need to be rotated regularly.
The application needs to detect the log file being renamed and handle that situation.
While Python provides its own file rotation handler, it is best to leave log rotation to dedicated tools such as logrotate.
The WatchedFileHandler will keep track of the log file and reopen it if it is rotated,
making it work well with logrotate without requiring any specific signals.

Here’s a sample implementation.

.. code-block:: python

    import logging
    import logging.handlers
    import os

    from pyPreservica import *

    handler = logging.handlers.WatchedFileHandler("pyPreservica.log")
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)

    client = EntityAPI()


-----------------------
Low Level Logging
-----------------------

pyPreservica now provides low level event hooks into the underlying API requests to the server.
To use this functionality, create a call back function with the following signature `call_back(r, *args, **kwargs)`

The first argument is the request object which can be queried.

This API allows clients to do things such as audit all the API endpoints which are called for example.



.. code-block:: python

    def print_url(r, *args, **kwargs):
        print(r.url)


    client = EntityAPI(request_hook=print_url)

    for f in client.descendants():
        pass


.. code-block:: text

    https://us.preservica.com/api/accesstoken/login
    https://us.preservica.com/api/entity/versiondetails/version
    https://us.preservica.com/api/user/details
    https://us.preservica.com/api/entity/root/children?start=0&max=100


