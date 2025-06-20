Entity API
~~~~~~~~~~~~~~~~~~

Making a call to the Preservica repository is very simple.

Begin by importing the pyPreservica module at the start of the Python script. You can import only the API you need or the
whole library.

To import all the pyPreservica functionality use:

.. code-block:: python

    from pyPreservica import *

Now, let's create the ``EntityAPI`` client object, this can have any name, but lets call it 
``client`` to keep things simple. 

.. code-block:: python

    client = EntityAPI()


The ``client`` object will manage the connection to the server and will be responsible for 
creating the API authentication tokens as needed.


Fetching Entities (Assets, Folders & Content Objects)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Python code examples show how data model entities, (Assets, Folders & Content Objects) 
can be returned from Preservica using their internal Preservica identifiers.

The following shows how you can fetch an Asset by its reference and then print its attributes to the screen.

.. code-block:: python

    from pyPreservica import *

    asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    print(asset.reference)
    print(asset.title)
    print(asset.description)
    print(asset.security_tag)
    print(asset.parent)
    print(asset.entity_type)


We can also fetch the same attributes for both Folders

.. code-block:: python

    folder = client.folder("0b0f0303-6053-4d4e-a638-4f6b81768264")
    print(folder.reference)
    print(folder.title)
    print(folder.description)
    print(folder.security_tag)
    print(folder.parent)
    print(folder.entity_type)

and Content Objects

.. code-block:: python

    content_object = client.content_object("1a2a2101-6053-4d4e-a638-4f6b81768264")
    print(content_object.reference)
    print(content_object.title)
    print(content_object.description)
    print(content_object.security_tag)
    print(content_object.parent)
    print(content_object.entity_type)


Assets, Folders & Content Objects actually have a number of attributes in common, such as ``title``, ``description`` etc. 
Technically they are all objects of type ``Entity``.
    

We can fetch any of Assets, Folders and Content Objects using the entity type and the unique reference

.. code-block:: python

    asset = client.entity(EntityType.ASSET, "9bad5acf-e7a1-458a-927d-2d1e7f15974d")

    folder = client.entity(EntityType.FOLDER, asset.parent)

To get a list of parent Folders of an Asset all the way to the root of the repository

.. code-block:: python

    asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")

    folder = client.folder(asset.parent)
    print(folder.title)
    while folder.parent is not None:
        folder = client.folder(folder.parent)
        print(folder.title)


Fetching Children of Entities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The immediate children of a Folder can also be retrieved using the library.

To get all the top level or root Folders use

.. code-block:: python

    for root_folder in client.descendants(None):
        print(root_folder.title)

or you can leave the arguments empty:

.. code-block:: python

    for root_folder in client.descendants():
        print(root_folder.title)


The ``descendants`` method is a generator function. 
The method behaves like an iterator, i.e. it can be used in a for loop, the advantage of this approach is that
the paging of results is taken care of automatically. If a Folder has many thousands of Assets then the method will
make multiple calls to the server. It will default to 100 items between server requests.

The performance improvement from the use of generators is the result of the lazy (on demand) generation of values, 
which translates to lower memory usage. 
Furthermore, you do not need to wait until all the children have been generated before you start to use them.


To get a set of the immediate children of a particular Folder use

.. code-block:: python

     for entity in client.descendants(folder.reference):
        print(entity.title)

To get the siblings of an Asset you can use

.. code-block:: python

     for entity in client.descendants(asset.parent):
        print(entity.title)

The set of entities returned may contain both Assets and other Folders.


.. note::
    Entities within the returned set only contain the attributes (type, reference and title).
    If you need the full object you have to request it from the server.

    You can request the entity back without knowing exactly what type it is by using the ``entity()`` call

To fetch the full object back you can use:

.. code-block:: python

    for f in client.descendants():
        e = client.entity(f.entity_type, f.reference)
        print(e)


If you only need the Folders or Assets from a parent you can filter the results using a pre-defined filter.

For example the following will only return Asset objects and will ignore Folders:

.. code-block:: python

    for asset in filter(only_assets, client.descendants(asset.parent)):
        print(asset.title)

To return only Folder objects use:

.. code-block:: python

    for folders in filter(only_folders, client.descendants(asset.parent)):
        print(folders.title)



If you want **all** the entities below a point in the hierarchy, i.e a recursive list of all folders and Assets then you can
call ``all_descendants()`` this is also generator function which returns a lazy iterator which will make
repeated calls to the server for each page of results.

The following will return all entities within the repository from the root folders down

.. code-block:: python

    for e in client.all_descendants():
        print(e.title)


.. warning::
    The code above will fetch every Asset or Folder back from the system.
    This could take a long time depending on the size of the repository.

    It may be more efficient to search using the ``ContentAPI`` if you are looking for particular objects in the repository.



again if you need a list of every Asset in the system you can filter using

.. code-block:: python

    for asset in filter(only_assets, client.all_descendants()):
        print(asset.title)



Creating new Folders
^^^^^^^^^^^^^^^^^^^^^^^^

Folder objects can be created directly in the repository, the ``create_folder()`` function takes 3
mandatory parameters, folder title, description and security tag.

.. code-block:: python

    new_folder = client.create_folder("title", "description", "open")
    print(new_folder.reference)

This will create a folder at the top level of the repository. You can create child folders by passing the
reference of the parent as the last argument.

.. code-block:: python

    new_folder = client.create_folder("title", "description", "open", folder.reference)
    print(new_folder.reference)
    assert  new_folder.parent == folder.reference




Adding Physical Assets
^^^^^^^^^^^^^^^^^^^^^^^^

Preservica supports the creation of intellectual entities which correspond to physical objects. These are similar to
regular assets, but they do not point to digital files like regular assets.

To use Physical Assets the system needs a system property set to active the functionality, this can be done by the
Preservica help desk.

.. code-block:: python

    parent = client.folder("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    physical_asset = client.add_physical_asset("title", "description", parent, "open")
    print(physical_asset.reference)


Physical assets support 3rd party identifiers, thumbnails and descriptive metadata in the same way as regular assets.

.. code-block:: python

    client.add_identifier(physical_asset, "ISBN", "978-3-16-148410-0")
    client.add_thumbnail(physical_asset, "icon.png")

Updating Entities
^^^^^^^^^^^^^^^^^^^^^^^^

We can update either the title or description attribute for Assets,
Folders and Content Objects using the ``save()`` method

.. code-block:: python

    asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    asset.title = "New Asset Title"
    asset.description = "New Asset Description"
    asset = client.save(asset)

    folder = client.folder("0b0f0303-6053-4d4e-a638-4f6b81768264")
    folder.title = "New Folder Title"
    folder.description = "New Folder Description"
    folder = client.save(folder)

    content_object = client.content_object("1a2a2101-6053-4d4e-a638-4f6b81768264")
    content_object.title = "New Content Object Title"
    content_object.description = "New Content Object Description"
    content_object = client.save(content_object)


This method can also be used to set the Type of an asset or folder. By default Information objects have a type "Asset"
and Structural objects have a type "Folder". You can use the API to change these defaults for example you may want to
use the type field to set the level of description of a Structural object to "Fonds" or "Series" etc.

To change the type use the *custom_type* attribute on the object, e.g.

.. code-block:: python

    folder = client.folder("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    folder.custom_type = "Series"
    folder = client.save(folder)


.. code-block:: python

    asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    asset.custom_type = "Manuscript"
    asset = client.save(asset)


If you want to change the type back, just set the value to None

.. code-block:: python

    asset = client.asset("9bad5acf-e7a1-458a-927d-2d1e7f15974d")
    asset.custom_type = None
    asset = client.save(asset)



Security Tags
^^^^^^^^^^^^^^^^^^^^^^^^

To change the security tag on an Asset or Folder we have a separate API. Since this may be a long running process.
You can choose either a asynchronous (non-blocking) call which returns immediately or synchronous (blocking call) which
waits for the security tag to be changed before returning.

This is the asynchronous call which returns immediately returning a process id

.. code-block:: python

    pid = client.security_tag_async(entity, new_tag)


You can determine the current status of the asynchronous call by passing the argument to ``get_async_progress``

.. code-block:: python

    status = client.get_async_progress(pid)


The synchronous version will block until the security tag has been updated on the entity.
This call does not recursively change entities within a folder.
It only applies to the named entity passed as an argument.

.. code-block:: python

    entity = client.security_tag_sync(entity, new_tag)


3rd Party External Identifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

3rd party or external identifiers are a useful way to provide additional names or identities to objects to
provide an alternate way of accessing them.
For example if you are synchronising metadata between an external metadata catalogue and Preservica adding the catalogue
identifiers to the Preservica objects allows the catalogue to query Preservica using its own ids.

Each Preservica entity can hold as many external identifiers as you need.

.. note::
    Adding, Updating and Deleting external identifiers is only available in version 6.1 and above

We can add external identifiers to either Assets, Folders or Content Objects. External identifiers have a name or type
and a value. External identifiers do not have to be unique in the same way as internal identifiers.
The same external identifiers can be added to multiple entities to form sets of objects.

.. code-block:: python

    asset = client.asset("9bad5acf-e7ce-458a-927d-2d1e7f15974d")
    client.add_identifier(asset, "ISBN", "978-3-16-148410-0")
    client.add_identifier(asset, "DOI", "https://doi.org/10.1109/5.771073")
    client.add_identifier(asset, "URN", "urn:isan:0000-0000-2CEA-0000-1-0000-0000-Y")


Fetch external identifiers on an entity. This call returns a set of tuples (identifier_type, identifier_value)

.. code-block:: python

    identifiers = client.identifiers_for_entity(folder)
    for identifier in identifiers:
         identifier_type = identifier[0]
         identifier_value = identifier[1]

You can search the repository for entities with matching external identifiers. The call returns a set of objects
which may include any type of entity.

.. code-block:: python

    for e in client.identifier("ISBN", "978-3-16-148410-0"):
        print(e.entity_type, e.reference, e.title)

.. note::
    Entities within the set only contain the attributes (type, reference and title). If you need the full object you have to request it.

For example

.. code-block:: python

    for ident in client.identifier("DOI", "urn:nbn:de:1111-20091210269"):
        entity = client.entity(ident.entity_type, ident.reference)
        print(entity.title)
        print(entity.description)

To delete identifiers attached to an entity

.. code-block:: python

    client.delete_identifiers(entity)

Will delete all identifiers on the entity

.. code-block:: python

    client.delete_identifiers(entity, identifier_type="ISBN")

Will delete all identifiers which have type "ISBN"

.. code-block:: python

    client.delete_identifiers(entity, identifier_type="ISBN", identifier_value="978-3-16-148410-0")

Will only delete identifiers which match the type and value

Descriptive Metadata
^^^^^^^^^^^^^^^^^^^^^^^

You can query an entity to determine if it has any attached descriptive metadata using the metadata attribute.
This returns a dictionary object the dictionary key is a url which can be used to the fetch metadata
and the value is the schema name

.. code-block:: python

    for url, schema in entity.metadata.items():
        print(url, schema)

The descriptive XML metadata document can be returned as a string by passing the key of the map (url)
to the ``metadata()`` method

.. code-block:: python

    for url in entity.metadata:
        xml_string = client.metadata(url)

An alternative is to call the ``metadata_for_entity``  directly

.. code-block:: python

    xml_string = client.metadata_for_entity(entity, "https://person.org/person")

this will fetch the first metadata document which matches the schema argument on the entity

If you need all the descriptive XML fragments attached to an Asset or Folder you can call ``all_metadata``
this is a Generator which returns a Tuple containing the schema as the first item and the xml document in the second.

.. code-block:: python

    for metadata in client.all_metadata(entity):
        schema = metadata[0]
        xml_string = metadata[1]



Metadata can be attached to entities either by passing an XML document as a string

.. code-block:: python

    folder = entity.folder("723f6f27-c894-4ce0-8e58-4c15a526330e")

    xml = "<person:Person  xmlns:person='https://person.org/person'>" \
        "<person:Name>Bob Smith</person:Name>" \
        "<person:Phone>01234 100 100</person:Phone>" \
        "<person:Email>test@test.com</person:Email>" \
        "<person:Address>Abingdon, UK</person:Address>" \
        "</person:Person>"

    folder = client.add_metadata(folder, "https://person.org/person", xml)

or by reading the metadata from a file

.. code-block:: python

    with open("DublinCore.xml", 'r', encoding="utf-8") as md:
        asset = client.add_metadata(asset, "http://purl.org/dc/elements/1.1/", md)


Adding descriptive metadata may change the namespace prefix values, this does not change
the meaning of the XML document as the prefix values are arbitrary labels.
XML namespace prefixes themselves are arbitrary; it's only through their binding to a full
XML namespace name that they derive their significance.

If you want to preserve the namespace prefix you can add the following to the start of your Python scripts


.. code-block:: python

    xml.etree.ElementTree.register_namespace("person", "https://person.org/person")

This will associate the namespace prefix “person” with the actual XML namespace


Descriptive metadata can also be updated to amend values or change the document structure
To update an existing metadata document call

.. code-block:: python

    client.update_metadata(entity, schema, xml_string)

For example the following python fragment appends a new element to an existing document.

.. code-block:: python

    folder = client.folder("723f6f27-c894-4ce0-8e58-4c15a526330e")   # call into the API

    for url, schema in folder.metadata.items():
        if schema == "https://person.org/person":
            xml_string = client.metadata(url)                    # call into the API
            xml_document = ElementTree.fromstring(xml_string)
            postcode = ElementTree.Element('{https://person.org/person}Postcode')
            postcode.text = "OX14 3YS"
            xml_document.append(postcode)
            xml_string = ElementTree.tostring(xml_document, encoding='UTF-8').decode("utf-8")
            client.update_metadata(folder, schema, xml_string)   # call into the API


Relationships Between Entities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Preservica allows arbitrary relationships between entities such as Assets and Folders.
These relationships appear in the Preservica user interface as links from one entity to another.
All entities have existing vertical parent child relationships which determine the level of description for an asset.
These relationships are additional relationships which relate different entities across the repository.

For example relationships may be used to link different editions of the same work,
or a translation of an existing document etc.

Any type of relationship is supported, for example The Dublin Core Metadata Initiative provide a set of standard relationships between entities,
and these have been provided as part of the Relationship class, but any text string is allowed for the relationship type.

.. code-block:: python

    >>>Relationship.DCMI_isVersionOf
    http://purl.org/dc/terms/isVersionOf

    >>>Relationship.DCMI_isReplacedBy
    http://purl.org/dc/terms/isReplacedBy


Relationships are created between two entities A and B and have a type, for example;

A isVersionOf B.

This is a relationship from A to B. You can also create links going in the other direction and have bi-directional links between the same assets.
For example;

A isVersionOf B and B hasVersion A.

To create a relationship between entities use the ``add_relation`` method.

.. code-block:: python

    A_asset = client.asset("de1c32a3-bd9f-4843-a5f1-46df080f83d2")
    B_asset = client.asset("683f9db7-ff81-4859-9c03-f68cfa5d9c3d")

    client.add_relation(A_asset, Relationship.DCMI_isVersionOf, B_asset)
    client.add_relation(B_asset, Relationship.DCMI_hasVersion, A_asset)

    client.add_relation(A_asset, "Supersedes", B_asset)

.. note::
    The Relationship API is only available when connected to Preservica version 6.3.1 or above

You can list the relationships from an asset using:

.. code-block:: python

    for r in client.relationships(A_asset):
        print(r)

This returns a Generator of ``Relationship`` objects.

To delete relationships between assets use:

.. code-block:: python

    client.delete_relationships(A_asset)

This will delete all relationships FROM the specified entity to another entity,
It does not delete relationships TO this entity.

If only need to delete a specific relationship, you can pass the relationship name as a second argument

.. code-block:: python

    client.delete_relationships(A_asset, "Supersedes")

Representations, Content Objects & Generations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each Asset in Preservica contains one or more representations, such as Preservation or Access etc.
All Assets have at least one Preservation representation which is created when the Asset is ingested.

To get a list of all the representations of an Asset use ``representations()`` which returns a set of
``Representation`` objects for the Asset.

The ``Representation`` contains the name and type and also contains a reference back to its parent Asset object.

Currently Preservica supports two representation types "Access" and "Preservation", you can have as many representations of each type
as you need. For example a book may need two "Access" representations one containing a single PDF document and another containing multiple 
JPEG images, one for each page etc.  

.. code-block:: python

    for representation in client.representations(asset):
        print(representation.rep_type)
        print(representation.name)
        print(representation.asset.title)

Each Representation will contain one or more Content Objects.
Simple Assets contain a single Content Object per Representation whereas more complex objects such as 3D models,
books, multi-page documents may have several content objects within each Representation.

Content Objects are similar to Assets and Folders, in that they can also contain descriptive metadata and identifiers etc.
The Content Objects within a Representation do have a natural order which is preserved within the Asset and therefore
are returned as a ``list`` object.

.. code-block:: python

    for content_object in client.content_objects(representation):
        print(content_object.reference)
        print(content_object.title)
        print(content_object.description)
        print(content_object.parent)
        print(content_object.metadata)
        print(content_object.asset.title)

By default the title of a Content Object will probably be the name of the underlying computer file, but it does not have to be. 
You can explicitly set the title and description of each Content Object within an Asset.
Preservica also supports adding external identifiers and descriptive metadata documents to Content Objects.


Each Content Object will contain a least one Generation, migrated content may have multiple Generations.

.. code-block:: python

    for generation in client.generations(content_object):
        print(generation.original)
        print(generation.active)
        print(generation.content_object)
        print(generation.format_group)
        print(generation.effective_date)
        print(generation.bitstreams)




Each Generation has a list of BitStreams which can be used to fetch the actual content from the server or
fetch technical metadata about the bitstream itself.

Technical information such as formats and properties can be accessed from the ``Generation`` object.
The format information is stored as dictionary object within a list as there may be multiple formats associated
with each object.

The key values for the format dictionary are: Valid, PUID, Priority, IdentificationMethod, FormatName, FormatVersion

.. code-block:: python

    for format in generation.formats:
        for key,value in format.items():
            print(key, value)


The technical properties of the file can be accessed via the properties attribute which is a list of dictionary
objects. Each property is a single dictionary object with the following keys: PUID, PropertyName, Value

.. code-block:: python

    for property in generation.properties:
        for key,value in property.items():
            print(key, value)



BitStreams
^^^^^^^^^^^^

Generations also contain a list of bitstreams, these contain information about the bitstreams such as file size
and fixity etc.

.. code-block:: python

    for bitstream in generation.bitstreams:
        print(bitstream.filename)
        print(bitstream.length)
        for algorithm,value in bitstream.fixity.items():
            print(algorithm,  value)



If you have an Asset object and you would like to fetch all the available bitstreams you would use something like:

.. code-block:: python

    for representation in client.representations(asset):
        for content_object in client.content_objects(representation):
            for generation in client.generations(content_object):
                for bitstream in generation.bitstreams:

If you only need the current or active Generations, then you can use the following short cut method
which returns each Bitstream from all the Representations and Content Objects within the Asset.

.. code-block:: python

    for bitstream in client.bitstreams_for_asset(asset):
        do_something(bitstream)


The actual content files can be downloaded to a disk file using ``bitstream_content()``

This will download the bitstream to the file path given by the second argument, to save the object using
the original file name use the following:

.. code-block:: python

    client.bitstream_content(bitstream, bitstream.filename)


To download all the access bitstreams to the current folder you would use.

.. code-block:: python

    for representation in client.representations(asset):
        if representation.rep_type  == "Access":
            for content_object in client.content_objects(representation):
                for generation in client.generations(content_object):
                    for bitstream in generation.bitstreams:
                        client.bitstream_content(bitstream, bitstream.filename)


The content files can be written to a byte array using ``bitstream_bytes()`` this
returns a BytesIO object.

.. code-block:: python

    byte_array = client.bitstream_bytes(bitstream)

If you need to process bitstream content as it is downloaded from Preservica pyPreservica provides the following API.

.. code-block:: python

    for bitstream in client.bitstreams_for_asset(asset):
        for chunk in client.bitstream_chunks(bitstream):
            doSomeThing(chunk)

This function returns a Generator which allows the client to process parts of the file as its downloading.

The method also allows a second argument which defines the size of chunk returned.

.. code-block:: python

    chunk_size8k = 8*1024
    for bitstream in client.bitstreams_for_asset(asset):
        for chunk in client.bitstream_chunks(bitstream, chunk_size8k):
            doSomeThing(chunk)

The storage adapters which hold a copy of the bitstream can be found using:

.. code-block:: python

    chunk_size8k = 8*1024
    for bitstream in client.bitstreams_for_asset(asset):
        locations = client.bitstream_location(bitstream)



BitStream Integrity Check History
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can request the history of all integrity checks which have been carried out on a bitstream

.. code-block:: python

    for bitstream in generation.bitstreams:
        for check in client.integrity_checks(bitstream):
            print(check)

The list of returned checks includes both full and quick integrity checks.

.. note::
    This call does not start a new check, it only returns information about previous checks.

Merging Assets
^^^^^^^^^^^^^^^^^^^^^^^^

You can create a single multi-part Asset from all the Assets in a folder using the ``merge_folder`` call.

This will create a new Asset which contains all the Content Objects from all the Assets in the folder.

.. code-block:: python

    folder = client.folder("723f6f27-c894-4ce0-8e58-4c15a526330e")
    client.merge_folder(folder)


Adding Representations
^^^^^^^^^^^^^^^^^^^^^^^^

Since version Preservica 6.12 the API allows new Access representations to be added to an existing Asset.
This allows organisations to migrate content outside of Preservica or add new access versions after the preservation
versions have been ingested.

To add a new Access representation to an existing Asset call ``add_access_representation`` and pass the Asset
and a new content file. The function returns a process id which can be used to track the status of the ingest.

The Preservica tenancy requires the ``post.new.representation.feature`` flag to be set.


.. code-block:: python

    asset = client.asset("723f6f27-c894-4ce0-8e58-4c15a526330e")
    pid = client.add_access_representation(asset, access_file="access.jpg")



Moving Entities
^^^^^^^^^^^^^^^^

We can move entities between folders using the ``move`` call

.. code-block:: python

    client.move(entity, dest_folder)

Where entity is the object to move either an Asset or Folder and the second argument is
destination folder where the entity is moved to.

Folders can be moved to the root of the repository by passing None as the second argument.

.. code-block:: python

    entity = client.move(folder, None)

The ``move()`` call is an alias for ``move_sync()`` which is a synchronous (blocking call)

.. code-block:: python

    entity = client.move_sync(entity, dest_folder)

An asynchronous (non-blocking) version is also available which returns a progress id.

.. code-block:: python

    pid = client.move_async(entity, dest_folder)

You can determine the completed status of the asynchronous move call by passing the
argument to ``get_async_progress``

.. code-block:: python

    status = client.get_async_progress(pid)


Deleting Entities
^^^^^^^^^^^^^^^^^^^^^^^

You can initiate and approve a deletion request using the API.

.. note::
    Deletion is a two stage process within Preservica and requires two distinct sets of credentials.
    To use the delete functions you must be using the "credentials.properties" authentication method.


.. note::
    The Deletion API is only available when connected to Preservica version 6.2 or above


Add manager.username and manager.password to the credentials file. ::

    [credentials]
    username=
    password=
    server=
    tenant=
    manager.username=
    manager.password=


Deleting an asset

.. code-block:: python

    asset_ref = client.delete_asset(asset, "operator comments", "supervisor comments")
    print(asset_ref)

Deleting a folder

.. code-block:: python

    folder_ref = client.delete_folder(folder, "operator comments", "supervisor comments")
    print(folder_ref)


.. warning::
    This API call deletes entities within the repository, it both initiates and approves the deletion request
    and therefore must be used with care.


Finding Updated Entities
^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can query Preservica for entities which have changed over the last n days using

.. code-block:: python

    for e in client.updated_entities(previous_days=30):
        print(e)

The argument is the number of previous days to check for changes. This call does paging internally.

Downloading Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The pyPreservica library also provides a web service call which is part of the content API which allows downloading of digital
content directly without having to request the Representations and Generations first.
This call is a short-cut to request the Bitstream from the latest Generation of the first Content Object in the Access
Representation of an Asset. If the asset does not have an Access Representation then the
Preservation Representation is used.

For very simple assets which comprise a single digital file in a single Representation
then this call will probably do what you expect.

.. code-block:: python

    asset = client.asset("edf403d0-04af-46b0-ab21-e7a620bfdedf")
    filename = client.download(asset, "asset.jpg")

For complex multi-part assets which have been through preservation actions it may be better to use the data model
and the ``bitstream_content()`` function to fetch the exact bitstream you need.



Events on Specific Entities
^^^^^^^^^^^^^^^^^^^^^^^^^^^

List actions performed against this entity

``entity_events()`` returns a iterator which contains events on an entity, either an asset or folder

.. code-block:: python

    asset = client.asset("edf403d0-04af-46b0-ab21-e7a620bfdedf")
    for event in client.entity_events(asset)
        print(event)



Events Across Entities
^^^^^^^^^^^^^^^^^^^^^^^^^^^

List actions performed against all entities within the repository. The event is a ``dict()`` object containing
the event attributes. This call is generator function which returns the events as needed.

.. code-block:: python

    for event in client.all_events():
        print(event)


Ingest Events
^^^^^^^^^^^^^^^^^

Return a generator of ingest events over the last n days

.. code-block:: python

    for ingest_event in client.all_ingest_events(previous_days=1):
        print(ingest_event)


Asset and Folder Thumbnail Images
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can now add and remove icons on Assets and Folders using the API. 
The icons will be displayed in the Explorer and Universal Access interfaces.

.. code-block:: python

    folder = client.folder("edf403d0-04af-46b0-ab21-e7a620bfdedf")
    client.add_thumbnail(folder, "../my-icon.png")

    client.remove_thumbnail(folder)

and for assets

.. code-block:: python

    asset = client.asset("edf403d0-04af-46b0-ab21-e7a620bfdedf")
    client.add_thumbnail(asset, "../my-icon.png")

    client.remove_thumbnail(asset)


We also have a function to fetch the thumbnail image for an asset or folder

.. code-block:: python

    asset = client.asset("edf403d0-04af-46b0-ab21-e7a620bfdedf")
    filename = client.thumbnail(asset, "thumbnail.png")

You can specify the size of the thumbnail by passing a second argument

.. code-block:: python

    asset = client.asset("edf403d0-04af-46b0-ab21-e7a620bfdedf")
    filename = client.thumbnail(asset, "thumbnail.png", Thumbnail.LARGE)     ## 400×400   pixels
    filename = client.thumbnail(asset, "thumbnail.png", Thumbnail.MEDIUM)    ## 150×150   pixels
    filename = client.thumbnail(asset, "thumbnail.png", Thumbnail.SMALL)     ## 64×64     pixels




Replacing Content Objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Preservica now supports replacing individual Content Objects within an Asset. The use case here is you have uploaded
a large digitised object such as book and you subsequently discover that a page has been digitised incorrectly.
You would like to replace a single page (Content Object) without having to delete and re-ingest the complete Asset.

The non-blocking (asynchronous) API call will replace the last active Generation of the Content Object

.. code-block:: python

    content_object = client.content_object('0f2997f7-728c-4e55-9f92-381ed1260d70')
    file = "C:/book/page421.tiff"
    pid = client.replace_generation_async(content_object, file)

This will return a process id which can be used to monitor the replacement workflow using

.. code-block:: python

    status = client.get_async_progress(pid)

By default the API will generate a new fixity value on the client using the same fixity algorithm as the original Generation you are replacing.
If you want to use a different fixity algorithm or you want to use a pre-calculated or existing fixity value you can specify the
algorithm and value.

.. code-block:: python

    content_object = client.content_object('0f2997f7-728c-4e55-9f92-381ed1260d70')
    file = "C:/book/page421.tiff"
    pid = client.replace_generation_async(content_object, file, fixity_algorithm='SHA1', fixity_value='2fd4e1c67a2d28fced849ee1bb76e7391b93eb12')

There is also an synchronous or blocking version which will wait for the replace workflow to complete before returning
back to the caller.

.. code-block:: python

    content_object = client.content_object('0f2997f7-728c-4e55-9f92-381ed1260d70')
    file = "C:/book/page421.tiff"
    workflow_status = client.replace_generation_sync(content_object, file)


Export OPEX Package
^^^^^^^^^^^^^^^^^^^^^^^^^^^

pyPreservica allows clients to request a full package export from the system by folder or asset,
this will start an export workflow and download the resulting dissemination package when the export workflow has completed.

The resulting package will be a zipped OPEX formatted package containing the digital content and metadata.
The ``export_opex`` API is a blocking call which will wait for the export workflow to complete before downloading the package.

.. code-block:: python

    folder = client.folder('0f2997f7-728c-4e55-9f92-381ed1260d70')
    opex_zip = client.export_opex(folder)

The output is the name of the downloaded zip file in the current working directory.

By default the OPEX package includes metadata, digital content with the latest active generations
and the parent hierarchy.

The API can be called on either a folder or a single asset.

.. code-block:: python

    asset = client.asset('1f2129f7-728c-4e55-9f92-381ed1260d70')
    opex_zip = client.export_opex(asset)

The call also takes the following optional arguments

* ``IncludeContent``            "Content" or "NoContent"
* ``IncludeMetadata``           "Metadata" or "NoMetadata" or "MetadataWithEvents"
* ``IncludedGenerations``       "LatestActive" or "AllActive" or "All"
* ``IncludeParentHierarchy``    "true" or "false"

e.g.

.. code-block:: python

    folder = client.folder('0f2997f7-728c-4e55-9f92-381ed1260d70')
    opex_zip = client.export_opex(folder, IncludeContent="Content", IncludeMetadata="MetadataWithEvents")


.. note::
    You need a valid export workflow enabled in Preservica with the same settings as the API call. The API call is
    only looking for a matching export workflow and will not create a new one. If there is no matching workflow then
    the API call will fail.

