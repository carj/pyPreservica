#########################################
Welcome to pyPreservica's documentation
#########################################

Release v\ |version|.

.. container:: badges

    ..  image:: https://pepy.tech/badge/pyPreservica
        :target: https://pepy.tech/project/pyPreservica

    .. image:: https://img.shields.io/pypi/pyversions/pyPreservica.svg
        :target: https://pypi.org/project/pyPreservica/

    .. image:: https://img.shields.io/pypi/l/pyPreservica.svg
        :target: https://pypi.org/project/pyPreservica/

    .. image:: https://img.shields.io/pypi/wheel/pyPreservica.svg
        :target: https://pypi.org/project/pyPreservica/

    .. image:: https://readthedocs.org/projects/pypreservica/badge/?version=latest
        :target: https://pypreservica.readthedocs.io/en/latest


**pyPreservica** is an open source, python client for the Preservica APIs

-------------------------------------------------------------------------

pyPreservica is a 3rd party Python Software Development Kit (SDK) for the Preservica API,
which allows Preservica users to write software that makes use of the Preservica repository services.
This library provides classes for working with a range of the Preservica APIs.

https://developers.preservica.com/api-reference

This version of the documentation is for use against a Preservica 8.x-6.2 systems
For Preservica 6.0 and 6.1 see `the previous version <https://pypreservica.readthedocs.io/en/v6.1/>`_


pyPreservica is an open source 3rd party library and is not affiliated with `Preservica Ltd <https://preservica.com/>`_.
There is no support for use of the library from Preservica Ltd. For support see :ref:`Support <Support>`

-------------------

Quick Start Guide
==============================

Fetch an asset and browse its parent folder:

.. code-block:: python

    from pyPreservica import *

    client = EntityAPI()

    # Fetch an asset by its UUID
    asset = client.asset("dc949259-2c1d-4658-8eee-c17b27a8823d")
    print(asset.title)         # LC-USZ62-20901
    print(asset.security_tag)  # open

    # List all children of a folder
    folder = client.folder(asset.parent)
    for child in client.children(folder.reference):
        print(child.title, child.entity_type)


Upload a file as a new asset into an existing folder:

.. code-block:: python

    from pyPreservica import *

    upload = UploadAPI()
    folder_ref = "ae108c8f-b058-4228-b099-6049175d2f0c"
    package = simple_asset_package(preservation_file="picture.tiff", parent_folder=folder_ref)
    upload.upload_zip_package(package)


Search the repository:

.. code-block:: python

    from pyPreservica import *

    content = ContentAPI()
    for hit in content.simple_search_list("London"):
        print(hit)



------------------------


.. default-domain:: py
.. py:module:: pyPreservica

The User Guide
====================


.. toctree::
   :maxdepth: 4
   :caption: Table of Contents:

   intro
   tutorial
   entity
   content
   upload
   admin
   retention
   legal_hold
   workflow
   webhooks
   authority
   groups
   par
   monitor
   example


The API Documentation
==============================


.. toctree::
   :maxdepth: 4
   :caption: Table of Contents:

   api


Index
==========

* :ref:`genindex`
