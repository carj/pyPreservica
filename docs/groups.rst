Metadata Groups API
~~~~~~~~~~~~~~~~~~~~~

The Metadata Groups API is designed allows the creation of custom metadata within NGI (New Generation Interface).

You can find Swagger UI for this API at https://us.preservica.com/api/metadata/documentation.html#/%2Fgroups

Listing Existing Groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can query the system for all metadata groups using the following

.. code-block:: python

    client = MetadataGroupsAPI()

    for group in client.groups():
        print(group)


This returns a list of `Group` objects.  Groups returned do not include metadata fields.

If you need the raw json document as a string, use:

.. code-block:: python

    client = MetadataGroupsAPI()

    json_document: str = client.groups_json():


If you need the full set of metadata fields belonging to the group then you need to fetch a full `Group` object using the
group id:

.. code-block:: python

    client = MetadataGroupsAPI()

    for group in client.groups():
        group = client.group(group.group_id)
        print(group.name)
        for field in group.fields:
            print(field)


Just like the `groups` method, if you need the raw json document you can call

.. code-block:: python

    client = MetadataGroupsAPI()

    json_document: str = client.group_json(group_id):

Deleting Groups
^^^^^^^^^^^^^^^^^^

You can delete a group using its Group ID


.. code-block:: python

    client = MetadataGroupsAPI()

    client.delete_group(group_id)

or via the namespace URI attached to the Group.

.. code-block:: python

    client = MetadataGroupsAPI()

    client.delete_group_namespace(namespace)



Create a New Group
^^^^^^^^^^^^^^^^^^^^^

There are two options for creating a new group, either pass a well-formed json document describing the group or
pass a list of `GroupField` objects.

If you have a json document you can create the new Group using:

.. code-block:: python

    client = MetadataGroupsAPI()


    json_doc = """{
      "name" : "My Test Group",
      "description" : "A group setup to show an example of groups.",
      "fields" : [ {
        "id" : "issuing_country",
        "name" : "Issuing Country",
        "type" : "STRING",
        "defaultValue" : "American Samoa",
        "minOccurs" : 1,
        "maxOccurs" : 1,
        "values" : [ "Afghanistan", "Aland Islands", "Albania", "Algeria", "American Samoa" ],
        "indexed" : true
        }
      ]
    }"""

    client.add_group_json(json_doc)


If you dont have a json document, you can create the group and the required fields using Python Classes:

.. code-block:: python

    client = MetadataGroupsAPI()

    group_fields = []

    group_fields.append(GroupField(field_id="issuing_country", name="Issuing Country", field_type=GroupFieldType.STRING))
    group_fields.append(GroupField(field_id="issue_date", name="Issue Date", field_type=GroupFieldType.DATE))

    client.add_group(group_name="my group", description="my group description", fields=group_fields)


