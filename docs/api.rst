.. py:currentmodule:: pyPreservica

Developer Interface
~~~~~~~~~~~~~~~~~~~~

Entity API
^^^^^^^^^^^^^^

This part of the documentation covers all the interfaces of pyPreservica :class:`EntityAPI <EntityAPI>` object.


.. autoclass:: EntityAPI
     :members:


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

