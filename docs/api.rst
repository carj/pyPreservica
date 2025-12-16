.. py:currentmodule:: pyPreservica

Developer Interface
~~~~~~~~~~~~~~~~~~~~

Entity API
^^^^^^^^^^^^^^

This part of the documentation covers all the interfaces of pyPreservica :class:`EntityAPI <EntityAPI>` object.

.. autoclass:: pyPreservica.EntityAPI

   .. py:method:: asset(reference)

    Returns an asset object back by its internal reference identifier

    :param reference: The unique identifier for the asset usually its uuid
    :type  reference: str
    :return: The Asset object
    :rtype: Asset
    :raises RuntimeError: if the identifier is incorrect


   .. py:method::  folder(reference)

    Returns a folder object back by its internal reference identifier

    :param reference: The unique identifier for the asset usually its uuid
    :type  reference: str
    :return: The Folder object
    :rtype: Folder
    :raises RuntimeError: if the identifier is incorrect

   .. py:method:: content_object(reference)

    Returns a content object back by its internal reference identifier

    :param  reference: The unique identifier for the asset usually its uuid
    :type  reference: str
    :return: The content object
    :rtype: ContentObject
    :raises RuntimeError: if the identifier is incorrect

   .. py:method:: entity(entity_type, reference)

    Returns an generic entity based on its reference identifier

    :param  entity_type: The type of entity
    :type  entity_type: EntityType
    :param reference: The unique identifier for the entity
    :type  reference: str
    :return: The entity either Asset, Folder or ContentObject
    :rtype: Entity
    :raises RuntimeError: if the identifier is incorrect

   .. py:method:: save(entity)

    Updates the title and description of an entity
    The security tag and parent are not saved via this method call

    :param entity: The entity (asset, folder, content_object) to be updated
    :type  entity: Entity
    :return: The updated entity
    :rtype: Entity

   .. py:method:: security_tag_async(entity, new_tag)

    Change the security tag of an asset or folder
    This is a non blocking call which returns immediately.

    :param entity: The entity (asset, folder) to be updated
    :type  entity: Entity
    :param  new_tag: The new security tag to be set on the entity
    :type  new_tag: str
    :return: A progress id which can be used to monitor the workflow
    :rtype: str

   .. py:method:: security_tag_sync(entity, new_tag)

    Change the security tag of an asset or folder
    This is a blocking call which returns after all entities have been updated.

    :param entity: The entity (asset, folder) to be updated
    :type  entity: Entity
    :param new_tag: The new security tag to be set on the entity
    :type  new_tag: str
    :return: The updated entity
    :rtype: Entity

   .. py:method::  create_folder(title, description, security_tag, parent=None)

    Create a new folder in the repository below the specified parent folder.
    If parent is missing or None then a root level folder is created.

    :param str title: The title of the new folder
    :param str description: The description of the new folder
    :param str security_tag: The security tag of the new folder
    :param str parent: The identifier for the parent folder
    :return: The new folder object
    :rtype: Folder

   .. py:method::  representations(asset)

    Return a set of representations for the asset

    Representations are used to define how the information object are composed in terms of technology and structure.

    :param asset: The asset containing the required representations
    :type  asset: Asset
    :return: Set of Representation objects
    :rtype: set(Representation)

   .. py:method::  content_objects(representation)

    Return a list of content objects for a representation

    :param  representation: The representation
    :type  representation: Representation
    :return: List of content objects
    :rtype: list(ContentObject)

   .. py:method::  generations(content_object)

    Return a list of Generation objects for a content object

    :param  content_object: The content object
    :type  content_object: ContentObject
    :return: list of generations
    :rtype: list(Generation)

  .. py:method::  bitstream(url)

    Fetch a bitstream object from the server using its URL

    :param  url: The URL to the bitstream
    :type  url: str
    :return: a bitstream object
    :rtype: Bitstream



  .. py:method::  bitstream_bytes(bitstream, chunk_size)

    Download a file represented as a Bitstream to a byteIO array

    :param  bitstream: A bitstream object
    :type  url: Bitstream
    :param  chunk_size: Optional size of the chunks to be downloaded
    :type  chunk_size: int
    :return: A Byte Array
    :rtype: BytesIO


  .. py:method::  bitstream_chunks(bitstream, chunk_size)

    Generator function to return bitstream chunks, allows the clients to
    process chunks as they are downloaded.

    :param  bitstream: A bitstream object
    :type  url: Bitstream
    :param  chunk_size: Optional size of the chunks to be downloaded
    :type  chunk_size: int
    :return: Iterator
    :rtype: Generator


   .. py:method::  bitstream_content(bitstream, filename)

    Downloads the bitstream object to a local file

    :param Bitstream bitstream: The content object
    :param str filename: The name of the file the bytes are written to
    :return: the number of bytes written
    :rtype: int


   .. py:method::  identifiers_for_entity(entity)

    Return a set of identifiers which belong to the entity

    :param Entity entity: The entity
    :return: Set of identifiers as tuples
    :rtype: set(Tuple)


   .. py:method::  identifier(identifier_type, identifier_value)

    Return a set of entities with external identifiers which match the type and value

    :param str identifier_type: The identifier type
    :param str identifier_value: The identifier value
    :return: Set of entity objects which have a reference and title attribute
    :rtype: set(Entity)

   .. py:method::  add_identifier(entity, identifier_type, identifier_value)

    Add a new external identifier to an Entity object

    :param Entity entity: The entity the identifier is added to
    :param str identifier_type: The identifier type
    :param str identifier_value: The identifier value
    :return: An internal id for this external identifier
    :rtype: str

   .. py:method::  delete_identifiers(entity, identifier_type=None, identifier_value=None)

    Delete identifiers on an Entity object

    :param Entity entity: The entity the identifiers are deleted from
    :param str identifier_type: The identifier type
    :param str identifier_value: The identifier value
    :return: entity
    :rtype: Entity


   .. py:method::  metadata(uri)

    Fetch the metadata document by its identifier, this is the key from the entity metadata map

    :param str uri: The metadata identifier
    :return: An XML document as a string
    :rtype: str

   .. py:method::  metadata_for_entity(entity, schema)

    Fetch the first metadata document which matches the schema URI from an entity

    :param Entity entity: The entity containing the metadata
    :param str schema: The metadata schema URI
    :return: The first XML document on the entity matching the schema URI
    :rtype: str

   .. py:method::  add_metadata(entity, schema, data)

    Add a new descriptive XML document to an entity

    :param Entity entity: The entity to add the metadata to
    :param str schema: The metadata schema URI
    :param data data: The XML document as a string or as a file bytes
    :return: The updated Entity
    :rtype: Entity


   .. py:method::  update_metadata(entity, schema, data)

    Update an existing descriptive XML document on an entity

    :param Entity entity: The entity to add the metadata to
    :param str schema: The metadata schema URI
    :param data data: The XML document as a string or as a file bytes
    :return: The updated Entity
    :rtype: Entity

   .. py:method::  delete_metadata(entity, schema)

    Delete an existing descriptive XML document on an entity by its schema
    This call will delete all fragments with the same schema

    :param Entity entity: The entity to add the metadata to
    :param str schema: The metadata schema URI
    :return: The updated Entity
    :rtype: Entity


   .. py:method::  move_sync(entity, dest_folder)

    Move an entity (asset or folder) to a new folder
    This call blocks until the move is complete

    :param Entity entity: The entity to move either asset or folder
    :param Entity dest_folder: The new destination folder. This can be None to move a folder to the root of the repository
    :return: The updated entity
    :rtype: Entity


   .. py:method::  move_async(entity, dest_folder)

    Move an entity (asset or folder) to a new folder
    This call returns immediately and does not block

    :param Entity entity: The entity to move either asset or folder
    :param Entity dest_folder: The new destination folder. This can be None to move a folder to the root of the repository
    :return: Progress ID token
    :rtype: str


   .. py:method::   move(entity, dest_folder)

    Move an entity (asset or folder) to a new folder
    This call is an alias for the move_sync (blocking) method.

    :param Entity entity: The entity to move either asset or folder
    :param Entity dest_folder: The new destination folder. This can be None to move a folder to the root of the repository
    :return: The updated entity
    :rtype: Entity


   .. py:method::  children(folder, maximum=50, next_page=None)

    Return the child entities of a folder one page at a time. The caller is responsible for
    requesting the next page of results.

    :param str folder: The parent folder reference, None for the children of root folders
    :param int maximum: The maximum size of the result set in each page
    :param str next_page: A URL for the next page of results
    :return: A set of entity objects
    :rtype: set(Entity)

   .. py:method::  descendants(folder)

    Return the immediate child entities of a folder using a lazy iterator. The paging is done internally using a default page
    size of 50 elements. Callers can iterate over the result to get all children with a single call.

    :param str folder: The parent folder reference, None for the children of root folders
    :return: A set of entity objects (Folders and Assets)
    :rtype: set(Entity)

   .. py:method::   all_descendants(folder)

    Return all child entities recursively of a folder or repository down to the assets using a lazy iterator.
    The paging is done internally using a default page
    size of 25 elements. Callers can iterate over the result to get all children with a single call.

    :param str folder: The parent folder reference, None for the children of root folders
    :return: A set of entity objects (Folders and Assets)
    :rtype: set(Entity)

   .. py:method::  delete_asset(asset, operator_comment, supervisor_comment)

    Initiate and approve the deletion of an asset.

    :param Asset asset: The asset to delete
    :param str operator_comment: The comments from the operator which are added to the logs
    :param str supervisor_comment: The comments from the supervisor which are added to the logs
    :return: The asset reference
    :rtype: str

   .. py:method::  delete_folder(asset, operator_comment, supervisor_comment)

    Initiate and approve the deletion of a folder.

    :param Folder asset: The folder to delete
    :param str operator_comment: The comments from the operator which are added to the logs
    :param str supervisor_comment: The comments from the supervisor which are added to the logs
    :return: The folder reference
    :rtype: str


   .. py:method::  thumbnail(entity, filename, size=Thumbnail.LARGE)

    Get the thumbnail image for an asset or folder

    :param Entity entity: The entity
    :param str filename: The file the image is written to
    :param Thumbnail size: The size of the thumbnail image
    :return: The filename
    :rtype: str

   .. py:method::  download(entity, filename)

    Download the first generation of the access representation of an asset

    :param Entity entity: The entity
    :param str filename: The file the image is written to
    :param Thumbnail size: The size of the thumbnail image
    :return: The filename
    :rtype: str

   .. py:method::  updated_entities(previous_days: int = 1)

    Fetch a list of entities which have changed (been updated) over the previous n days.

    This method uses a generator function to make repeated calls to the server for every page of results.

    :param int previous_days: The number of days to check for changes.
    :return: A list of entities
    :rtype: list


   .. py:method::  all_events()

    Returns a list of events for the user's tenancy

    This method uses a generator function to make repeated calls to the server for every page of results.

    :return: A list of events
    :rtype: list

   .. py:method::  entity_events(entity: Entity)

    Returns a list of event actions performed against this entity

    This method uses a generator function to make repeated calls to the server for every page of results.

    :param Entity entity: The entity
    :return: A list of events
    :rtype: list


   .. py:method::  add_thumbnail(entity: Entity, image_file: str)

    Set the thumbnail for the entity to the uploaded image

    Supported image formats are png, jpeg, tiff, gif and bmp. The image must be 10MB or less in size.

    :param Entity entity: The entity
    :param str image_file: The path to the image


   .. py:method::  remove_thumbnail(entity: Entity)

    Remove the thumbnail for the entity to the uploaded image

    :param str image_file: The path to the image


   .. py:method::  replace_generation_sync(content_object: ContentObject, file_name: str, fixity_algorithm, fixity_value)

    Replace the last active generation of a content object with a new digital file.

    Starts the workflow and blocks until the workflow completes.

    :param ContentObject content_object: The content object to replace
    :param str file_name: The path to the new content object
    :param str fixity_algorithm: Optional fixity algorithm
    :param str fixity_value: Optional fixity value
    :return: Completed workflow status
    :rtype: str

   .. py:method::  replace_generation_async(content_object: ContentObject, file_name: str, fixity_algorithm, fixity_value)

    Replace the last active generation of a content object with a new digital file.

    Starts the workflow and returns a process ID

    :param ContentObject content_object: The content object to replace
    :param str file_name: The path to the new content object
    :param str fixity_algorithm: Optional fixity algorithm
    :param str fixity_value: Optional fixity value
    :return:  Process ID
    :rtype: str


   .. py:method::  get_async_progress(pid: str)

    Return the status of a running process


    :param pid str: The progress ID
    :return:  Workflow status
    :rtype: str

   .. py:method::   export_opex(entity: Entity, **kwargs)

    Initiates export of the entity and downloads the opex package

    :param Entity entity: The entity to export Asset or Folder
    :param str IncludeContent: "Content", "NoContent"
    :param str IncludeMetadata: "Metadata", "NoMetadata", "MetadataWithEvents"
    :param str IncludedGenerations: "LatestActive", "AllActive", "All"
    :param str IncludeParentHierarchy: "true", "false"
    :return: The path to the opex ZIP file
    :rtype: str


.. py:class:: Generation

    Generations represent changes to content objects over time, as formats become obsolete new
    generations may need to be created to make the information accessible.

    .. py:attribute:: original

    original  generation  (True or False)

    .. py:attribute:: active

    active  generation  (True or False)

    .. py:attribute:: format_group

    format for this generation

    .. py:attribute:: effective_date

    effective date generation

    .. py:attribute:: bitstreams

    list of Bitstream objects

    .. py:attribute:: properties

    list of technical properties
    each property is dict object containing PUID, PropertyName and Value

    .. py:attribute:: formats

    list of technical formats
    each format is dict object containing PUID, FormatName and FormatVersion



.. py:class:: Bitstream

    Bitstreams represent the actual computer files as ingested into Preservica, i.e.
    the TIFF photograph or the PDF document

    .. py:attribute:: filename

    The filename of the original bitstream

    .. py:attribute:: length

    The file size in bytes of the original Bitstream

    .. py:attribute:: fixity

    Dictionary object of fixity values for this bitstream,
    the key is the algorithm name and the value is the fixity value

.. py:class:: Representation

    Representations are used to define how the information object are composed in terms of technology and structure.

    .. py:attribute:: rep_type

    The type of representation

    .. py:attribute:: name

    The name of representation

    .. py:attribute:: asset

    The asset the representation belongs to

.. py:class:: Entity

    Entity is the base class for assets, folders and content objects
    They all have the following attributes

    .. py:attribute:: reference

    The unique internal reference for the entity

    .. py:attribute:: title

    The title of the entity

    .. py:attribute:: description

    The description of the entity

    .. py:attribute:: security_tag

    The security tag of the entity

    .. py:attribute:: parent

    The unique internal reference for this entity's parent object

    The parent of an Asset is always a Folder

    The parent of a Folder is always a Folder or None for a folder at the root of the repository

    The parent of a Content Object is always an Asset

    .. py:attribute:: metadata

    A map of descriptive metadata attached to the entity.

    The key of the map is the metadata identifier used to retrieve the metadata document
    and the value is the schema URI

    .. py:attribute:: entity_type

    Assets have entity type EntityType.ASSET

    Folders have entity type EntityType.FOLDER

    Content Objects have entity type EntityType.CONTENT_OBJECT

.. py:class:: Asset

    Asset represents the information object or intellectual unit of information within the repository.

    .. py:attribute:: reference

    The unique internal reference for the asset

    .. py:attribute:: title

    The title of the asset

    .. py:attribute:: description

    The description of the asset

    .. py:attribute:: security_tag

    The security tag of the asset

    .. py:attribute:: parent

    The unique internal reference for this asset's parent folder

    .. py:attribute:: metadata

    A dict of descriptive metadata attached to the asset.

    The key of the dict is the metadata identifier used to retrieve the metadata document
    and the value is the schema URI

    .. py:attribute:: entity_type

    Assets have entity type EntityType.ASSET


.. py:class:: Folder

    Folder represents the structure of the repository and contains both Assets and Folder objects.

    .. py:attribute:: reference

    The unique internal reference for the folder

    .. py:attribute:: title

    The title of the folder

    .. py:attribute:: description

    The description of the folder

    .. py:attribute:: security_tag

    The security tag of the folder

    .. py:attribute:: parent

    The unique internal reference for this folder's parent folder

    .. py:attribute:: metadata

    A map of descriptive metadata attached to the folder.

    The key of the map is the metadata identifier used to retrieve the metadata document
    and the value is the schema URI

    .. py:attribute:: entity_type

    Assets have entity type EntityType.FOLDER


.. py:class:: ContentObject

    ContentObject represents the internal structure of an asset.

    .. py:attribute:: reference

    The unique internal reference for the content object

    .. py:attribute:: title

    The title of the content object

    .. py:attribute:: description

    The description of the content object

    .. py:attribute:: security_tag

    The security tag of the content object

    .. py:attribute:: parent

    The unique internal reference for this content object parent asset

    .. py:attribute:: metadata

    A map of descriptive metadata attached to the content object.

    The key of the map is the metadata identifier used to retrieve the metadata document
    and the value is the schema URI

    .. py:attribute:: entity_type

    Content objects have entity type EntityType.CONTENT_OBJECT

.. autoclass:: pyPreservica.EntityType

.. autoclass:: pyPreservica.RelationshipDirection


.. autoclass:: pyPreservica.IntegrityCheck



Content API
^^^^^^^^^^^^^^


This part of the documentation covers all the interfaces of pyPreservica :class:`ContentAPI <ContentAPI>` object.

.. py:currentmodule:: pyPreservica
.. autoclass:: ContentAPI
    :members:
.. autoclass:: SearchResult
    :members:



Upload API
^^^^^^^^^^^^

This part of the documentation covers all the interfaces of pyPreservica :class:`UploadAPI <UploadAPI>` object.

.. py:currentmodule:: pyPreservica
.. autofunction:: simple_asset_package
.. autofunction:: complex_asset_package
.. autofunction:: cvs_to_xml
.. autoclass:: UploadAPI
    :members:



Retention Management API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

https://eu.preservica.com/api/entity/documentation.html#/%2Fretention-policies

.. py:currentmodule:: pyPreservica
.. autoclass:: RetentionPolicy
.. autoclass:: RetentionAssignment
.. autoclass:: RetentionAPI
     :members:




Workflow API
^^^^^^^^^^^^^^

.. note::
    The Workflow API is available for Enterprise Preservica users

https://eu.preservica.com/api/admin/documentation.html

.. py:currentmodule:: pyPreservica
.. autoclass:: WorkflowContext
    :members:
    :undoc-members:
.. autoclass:: WorkflowInstance
    :members:
    :undoc-members:
.. autoclass:: WorkflowAPI
     :members:


Administration and Management  API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
    The Administration and Management API needs to be enabled by the help desk.

https://eu.preservica.com/sdb/rest/workflow/documentation.html

.. py:currentmodule:: pyPreservica
.. autoclass:: AdminAPI
     :members:


Process Monitor  API
^^^^^^^^^^^^^^^^^^^^^^^

https://us.preservica.com/api/processmonitor/documentation.html

.. py:currentmodule:: pyPreservica
.. autoclass:: MonitorStatus
    :members:
    :undoc-members:
.. autoclass:: MonitorCategory
    :members:
    :undoc-members:
.. autoclass:: MonitorAPI
     :members:



WebHook  API
^^^^^^^^^^^^^^^^^^^

https://us.preservica.com/api/webhook/documentation.html

.. py:currentmodule:: pyPreservica
.. autoclass:: TriggerType
    :members:
    :undoc-members:

.. autoclass:: WebHooksAPI
     :members:


Authority Records API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

https://eu.preservica.com/api/reference-metadata/documentation.html

This API is used for managing the Authority records within Preservica.

.. py:currentmodule:: pyPreservica
.. autoclass:: Table
    :members:
    :undoc-members:

.. autoclass:: AuthorityAPI
     :members:


Metadata Groups API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

https://us.preservica.com/api/metadata/documentation.html#/%2Fgroups

The Metadata Groups API is designed allows the creation of custom metadata within NGI (New Generation Interface).

.. py:currentmodule:: pyPreservica
.. autoclass:: Group
    :members:
    :undoc-members:

.. autoclass:: GroupField
    :members:
    :undoc-members:

.. autoclass:: GroupFieldType
    :members:
    :undoc-members:

.. autoclass:: MetadataGroupsAPI
     :members:



Settings API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

https://eu.preservica.com/api/settings/documentation.html

API for retrieving information about configuration settings.

.. py:currentmodule:: pyPreservica


.. autoclass:: SettingsAPI
     :members: