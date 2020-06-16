Welcome to pyPreservica's documentation!
=================================

pyPreservica is python library for the Preservica API

This library provides a Python class for working with the Preservica Entity Rest API

-------------------


https://us.preservica.com/api/entity/documentation.html

.. contents:: Table of Contents
    :local:

Why Should I Use This?
----------------------

The goal of pyPreservica is to allow people to make use of the Preservica REST API without having to manage the underlying REST HTTPS requests and XML parsing.


Features
--------

-  Fetch and Update Entity Objects (Folders, Assets, Content Objects)
-  Add and Update External Identifiers
-  Add and Update Descriptive Metadata fragments
-  Retrive Representations, Generations & Bistreams
-  Download digital files


Installation
------------

.. code-block:: console

    $ pip install pyPreservica


Example
------------

Create the entity client ::
    
    >>> from pyPreservica.entityAPI import EntityAPI
    >>> client = EntityAPI()


Authentication
-----------------

pyPreservica provides 3 different methods for authentication. The library requires the username and password of a Preservica user and a Tenant identifier along with the server hostname.


1 **Method Arguments**

Include the user crendentials as arguments to the Entity Class::
    >>> from pyPreservica.entityAPI import EntityAPI
    >>> client = EntityAPI(username="test@test.com", password="123444", tenant="PREVIEW", server="preview.preservica.com")


2 **Environment Variable**

Export environment variables as part of the sesssion::
    $ EXPORT PRESERVICA_USERNAME="test@test.com"
    $ EXPORT PRESERVICA_PASSWORD="123444"
    $ EXPORT PRESERVICA_TENANT="PREVIEW"
    $ EXPORT PRESERVICA_SERVER="preview.preservica.com"
    
    >>> from pyPreservica.entityAPI import EntityAPI
    >>> client = EntityAPI()
    
3 **Properties File**

Create a properties file called "credentials.properties" in the working directory::
    [credentials]
    username=test@test.com
    password=123444
    tenant=PREVIEW
    server=preview.preservica.com
    
    >>> from pyPreservica.entityAPI import EntityAPI
    >>> client = EntityAPI()



