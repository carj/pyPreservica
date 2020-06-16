Welcome to pyPreservica's documentation
========================================

pyPreservica is python library for the Preservica API

This library provides a Python class for working with the Preservica Entity Rest API

https://us.preservica.com/api/entity/documentation.html

-------------------


.. contents:: Table of Contents
    :local:

Why Should I Use This?
----------------------

The goal of pyPreservica is to allow people to make use of the Preservica Entity API for reading and writing objects within a Preservica repository without having to manage the underlying REST HTTPS requests and XML parsing.
The library provides a level of abstraction which reflects the underlying data model.

.. hint::
    Access to the Preservica API's for the cloud hosted system does depend on which Preservica Edition has been
    licensed.  See https://preservica.com/digital-archive-software/products-editions for details.



Features
--------

-  Fetch and Update Entity Objects (Folders, Assets, Content Objects)
-  Add and Update External Identifiers
-  Add and Update Descriptive Metadata fragments
-  Retrieve Representations, Generations & Bistreams
-  Download digital files

Background
-----------

They key to working with the pyPreservica library is that the services follow the Preservica core data model closely.

.. image:: images/entity-API.jpg

The Preservica data model represents a hierarchy of entities, starting with the **structural objects** which are used to represent aggregations of digital assets. Structural objects define the organisation of the data. In a library context they may be referred to as collections, in an archival context they may be Fonds, Sub-Fonds, Series etc and in a records management context they could be simply a hierarchy of folders or directories.

These structural objects may contain other structural objects in the same way as a computer filesystem may contain folders within folders.

Within the structural objects comes the **information objects**. These objects which are sometimes referred to as the digital assets are what PREMIS defines as an Intellectual Entity. Information objects are considered a single intellectual unit for purposes of management and description: for example, a book, document, map, photograph or database etc.

**Representations** are used to define how the information object are composed in terms of technology and structure. For example, a book may be represented as a single multiple page PDF, a single eBook file or a set of single page image files.

Representations are usually associated with a use case such as access or long-term preservation. All Information objects have a least one representation defined by default. Multiple representations can be either created outside of Preservica through a process such as digitisation or within Preservica through preservation processes such a normalisation.

**Content Objects** represent the components of the asset. Simple assets such as digital images may only contain a single content object whereas more complex assets such as books or 3d models may contain multiple content objects. In most cases content objects will map directly to digital files or bitstreams.

**Generations** represent changes to content objects over time, as formats become obsolete new generations may need to be created to make the information accessible.

**Bitstreams** represent the actual computer files as ingested into Preservica, i.e. the TIFF photograph or the PDF document.

Installation
------------

.. code-block:: console

    $ pip install pyPreservica


Example
------------

Create the entity client and request an asset by its identifier ::
    
    >>> from pyPreservica.entityAPI import EntityAPI
    >>> client = EntityAPI()
    >>> asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    >>> print(asset.title)
    


Authentication
-----------------

pyPreservica provides 3 different methods for authentication. The library requires the username and password of a Preservica user and a Tenant identifier along with the server hostname.


1 **Method Arguments**

Include the user credentials as arguments to the Entity Class ::

    >>> from pyPreservica.entityAPI import EntityAPI
    >>> client = EntityAPI(username="test@test.com", password="123444", tenant="PREVIEW", server="preview.preservica.com")


2 **Environment Variable**

Export environment variables as part of the sesssion ::

    $ EXPORT PRESERVICA_USERNAME="test@test.com"
    $ EXPORT PRESERVICA_PASSWORD="123444"
    $ EXPORT PRESERVICA_TENANT="PREVIEW"
    $ EXPORT PRESERVICA_SERVER="preview.preservica.com"
    
    >>> from pyPreservica.entityAPI import EntityAPI
    >>> client = EntityAPI()
    
3 **Properties File**

Create a properties file called "credentials.properties" in the working directory ::

    [credentials]
    username=test@test.com
    password=123444
    tenant=PREVIEW
    server=preview.preservica.com
    
    >>> from pyPreservica.entityAPI import EntityAPI
    >>> client = EntityAPI()


The User Guide
--------------


QuickStart
==========

Making a call to the Preservica repository is very simple.

Begin by importing the pyPreservica module::

    >>> from pyPreservica.entityAPI import EntityAPI
    
Now, let's create the entity class::

    >>> client = EntityAPI()
    
and fetch an asset and print its attributes::

    >>> asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    >>> print(asset.reference)
    >>> print(asset.title)
    >>> print(asset.description)
    >>> print(asset.security_tag)
    >>> print(asset.parent)
    >>> print(asset.type)
    

The same code can be used to fetch folders and content objects::

    >>> folder = client.folder("0b0f0303-6053-4d4e-a638-4f6b81768264")
    >>> print(folder.reference)
    >>> print(folder.title)
    >>> print(folder.description)
    >>> print(folder.security_tag)
    >>> print(folder.parent)
    >>> print(folder.type)

    >>> content_object = client.content_object("1a2a2101-6053-4d4e-a638-4f6b81768264")
    >>> print(content_object.reference)
    >>> print(content_object.title)
    >>> print(content_object.description)
    >>> print(content_object.security_tag)
    >>> print(content_object.parent)
    >>> print(content_object.type)

We can update either the title or description attribute for assets, folders and content objects using the save() method::

    >>> asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    >>> asset.title = "New Asset Title"
    >>> asset.description = "New Asset Description"
    >>> asset = client.save(asset)

    >>> folder = client.folder("0b0f0303-6053-4d4e-a638-4f6b81768264")
    >>> folder.title = "New Folder Title"
    >>> folder.description = "New Folder Description"
    >>> folder = client.save(folder)

    >>> content_object = client.content_object("1a2a2101-6053-4d4e-a638-4f6b81768264")
    >>> content_object.title = "New Content Object Title"
    >>> content_object.description = "New Content Object Description"
    >>> content_object = client.save(content_object)


Example Applications
---------------------

The following is a short python script which uses pyPreservica to update assets within Preservica
with Dublin Core Metadata held in a spreadsheet.

The metadata should be saved as a UTF-8 CSV file called dublincore.csv::

    import xml
    import csv
    from EntityAPI.entityAPI import EntityAPI

    OAI_DC = "http://www.openarchives.org/OAI/2.0/oai_dc/"
    DC = "http://purl.org/dc/elements/1.1/"
    XSI = "http://www.w3.org/2001/XMLSchema-instance"

    entity = EntityAPI()

    headers = list()
    with open('dublincore.csv', encoding='utf-8-sig', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for header in row:
                headers.append(header)
            break
        if 'assetId' in headers:
            for row in reader:
                assetID = None
                xml_object = xml.etree.ElementTree.Element('oai_dc:dc', {"xmlns:oai_dc": OAI_DC, "xmlns:dc": DC, "xmlns:xsi": XSI})
                for value, header in zip(row, headers):
                    if header.startswith('dc:'):
                        xml.etree.ElementTree.SubElement(xml_object, header).text = value
                    elif header.startswith('assetId'):
                        assetID = value
                xml_request = xml.etree.ElementTree.tostring(xml_object, encoding='utf-8', xml_declaration=True).decode('utf-8')
                asset = entity.asset(assetID)
                entity.add_metadata(asset, OAI_DC, xml_request)
        else:
            print("The CSV file should contain a assetId column containing the Preservica identifier for the asset to be updated")

