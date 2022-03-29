Why Should I Use This?
----------------------

The goal of pyPreservica is to allow you to make use of the Preservica Entity API for reading and writing objects within
a Preservica repository without having to manage the underlying REST HTTPS requests and XML parsing.
The library provides a level of abstraction which reflects the underlying data model, such as structural and
information objects.

The pyPreservica library allows Preservica users to build applications which interact with the repository such as metadata
synchronisation with 3rd party systems etc.

.. hint::
    Access to the Preservica API's for the cloud hosted system does depend on which Preservica Edition has been
    licensed.  See https://preservica.com/digital-archive-software/products-editions for details.



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

Content API Features
---------------------

-  Fetch a list of indexed Solr Fields
-  Search based on a single query term
-  Filtered searches on indexed fields

Upload API Features
---------------------

-  Create single Content Object Packages with multiple Representations
-  Create multiple Content Object Packages with multiple Representations
-  Upload packages to Preservica
-  Spreadsheet Metadata
-  Ingest Web Video
-  Ingest Twitter Feeds

Admin API Features
---------------------
-  Schema Management (XML Templates, XSD Schema's & XSLT Transforms) (**New**)
-  User Management (create and remove user accounts)  (**New**)
-  Security Tags (add and remove security tags)   (**New**)

Retention Management API Features
------------------------------------
-  Create new retention policies (**New**)
-  Delete retention policies (**New**)
-  Update retention policies (**New**)
-  Assign retention policies to entities (**New**)


Background
-----------

They key to working with the pyPreservica library is that the services follow the Preservica core data model closely.

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

**Representations** are used to define how the information object are composed in terms of technology and structure.
For example, a book may be represented as a single multiple page PDF, a single eBook file or a set of single page image files.

Representations are usually associated with a use case such as access or long-term preservation.
All Information objects have a least one representation defined by default. Multiple representations can be either
created outside of Preservica through a process such as digitisation or within Preservica through preservation processes such a normalisation.

**Content Objects** represent the components of the asset. Simple assets such as digital images may only contain a
single content object whereas more complex assets such as books or 3d models may contain multiple content objects.
In most cases content objects will map directly to digital files or bitstreams.

**Generations** represent changes to content objects over time, as formats become obsolete new generations may need
to be created to make the information accessible.

**Bitstreams** represent the actual computer files as ingested into Preservica, i.e. the TIFF photograph or the PDF document.

PIP Installation
----------------

pyPreservica is available from the Python Package Index (PyPI)

https://pypi.org/project/pyPreservica/

pyPreservica is built and tested against Python 3.8. Older versions of Python may not work.


To install pyPreservica, simply run this simple command in your terminal of choice:

.. code-block:: console

    $ pip install pyPreservica

or you can install in a virtual python environment using:

.. code-block:: console

    $ pipenv install pyPreservica

pyPreservica is under active development and the latest version is installed using

.. code-block:: console

    $ pip install --upgrade pyPreservica

Get the Source Code
-------------------

pyPreservica is developed on GitHub, where the code is
`always available <https://github.com/carj/pyPreservica>`_.

You can clone the public repository

.. code-block:: console

    $ git clone git://github.com/carj/pyPreservica.git


Contributing
------------

Bug reports and pull requests are welcome on GitHub at https://github.com/carj/pyPreservica


Support
------------

pyPreservica is 3rd party open source client and is
not affiliated or supported by `Preservica Ltd <https://preservica.com/>`_

For announcements about new versions and discussion of pyPreservica please subscribe to the google groups
forum https://groups.google.com/g/pypreservica

Bug reports can be raised directly on either `GitHub <https://github.com/carj/pyPreservica>`_ or on the google group forum

General questions and queries about using pyPreservica posted on the google group forum above.

Examples
------------

Using the python console, create the entity API client object and request an Asset
(Information Object) by its unique reference and display some of its attributes.

All entities within the Preservica system have one unique reference which can be used to retrieve them.

The reference used to fetch entities (Assets, Folders) is the Preservica internal unique identifier.
This is a universally unique identifier `(UUID) <https://en.wikipedia.org/wiki/Universally_unique_identifier>`_

You can find the reference when viewing the object metadata within Explorer. Later on we will look at how we can fetch
entities using other 3rd party external identifiers which may be more meaningful such as ISBNs DOIs etc.

.. code-block:: python

    >>> from pyPreservica import *
    >>> client = EntityAPI()
    >>> client
    pyPreservica version: 0.8.5  (Preservica 6.2 Compatible)
    Connected to: us.preservica.com Version: 6.2.0 as test@test.com
    >>> asset = client.asset("dc949259-2c1d-4658-8eee-c17b27a8823d")
    >>> asset.reference
    'dc949259-2c1d-4658-8eee-c17b27a8823d'
    >>> asset.title
    'LC-USZ62-20901'
    >>> asset.parent
    'ae108c8f-b058-4228-b099-6049175d2f0c'
    >>> asset.security_tag
    'open'
    >>> asset.entity_type
    <EntityType.ASSET: 'IO'>


All entities have a parent reference attribute, for Assets this always points to the parent Folder.
For Content Objects the parent points to the Asset and for Folders it points to the parent Folder if it exists.
Folders at the root level of the repository do not have a parent and the attribute returns the special Python
value of ``None``

This example shows how pyPreservica can be used to upload and ingest a local file into Preservica using the UploadAPI
class.

.. code-block:: python

    >>> from pyPreservica import *

    >>> client = UploadAPI()
    >>> folder = "dc949259-2c1d-4658-8eee-c17b27a8823d"
    >>> zip_p = simple_asset_package(preservation_file="picture.tiff", parent_folder=folder)
    >>> client.upload_zip_package(zip_p)


Authentication
-----------------

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




If you don't want to include your Preservica credentials within your python script then the following two methods should
be used.

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

pyPreservica now supports authentication using shared secrets rather than a login account username and password.
This allows a trusted external applications such as pyPreservica to acquire a Preservica API authentication token
without having to use a set of login credentials.

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


SSL Certificates
-----------------

pyPreservica will only connect to servers which use the https:// protocol and will always validate certificates.

pyPreservica uses the `Certifi <https://pypi.org/project/certifi/>`_  project to provide SSL certificate validation.

Self-signed certificates used by on-premise deployments are not part of the Certifi certification authority (CA)
bundle and therefore need to be set explicitly.

The CA bundle is a file that contains root and intermediate certificates.
The end-entity certificate along with a CA bundle constitutes the certificate chain.

For on-premise deployments the trusted CAs can be specified through the ``REQUESTS_CA_BUNDLE``
environment variable. e.g.

.. code-block:: console

    $ export REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/my-server.cert


Application Logging
-------------------

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
