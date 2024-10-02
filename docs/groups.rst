Metadata Groups API
~~~~~~~~~~~~~~~~~~~~~

The Metadata Groups API is designed allows the creation of custom metadata within NGI (New Generation Interface).

You can find Swagger UI for this API at https://us.preservica.com/api/metadata/documentation.html#/%2Fgroups

Listing Existing Groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can query the system for all metadata groups using the following


.. code-block:: python

    client = MetadataGroupsAPI()

    for group in client.groups():
        print(g.name)
        print(g.description)


This returns a Generator of `Group` objects. The Groups returned do not include the individual metadata fields, just the
Group ID, name, description and schema URI.

If you need the underlying JSON document rather than a Python Object, you can use:

.. code-block:: python

    client = MetadataGroupsAPI()

    for g in client.groups_json()
        print(g['name'])


this returns a list of dict object containing all groups.

Fetching a Metadata Group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need the full set of metadata fields belonging to the group then you need to fetch a full `Group` object using the
group id:

.. code-block:: python

    client = MetadataGroupsAPI()

    for group in client.groups():
        group: Group = client.group(group.group_id)
        print(group.name)
        for field in group.fields:
            print(field)

The `Group` object contains a list of metadata fields.




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

There are two options for creating a new group, either pass a well-formed JSON document describing the group or
pass a list of `GroupField` objects.

If you have an existing JSON document you can create the new Group by passing the document as a string argument or as a
dictionary JSON object:

.. code-block:: python

    client = MetadataGroupsAPI()

    json_doc: str = """{
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

or


.. code-block:: python

    client = MetadataGroupsAPI()


    json_dict: dict = {
        "name": "My Test Group",
        "description": "A group setup to show an example of groups.",
        "fields": [ {
            "id": "issuing_country",
            "name": "Issuing Country",
            "type": "STRING",
            "defaultValue": "American Samoa",
            "minOccurs": 1,
            "maxOccurs": 1,
            "values": ["Afghanistan", "Aland Islands", "Albania", "Algeria", "American Samoa"],
            "indexed": True
            }
        ]
    }

    client.add_group_json(json_dict)


If you dont have a JSON document, you can create the group and the required metadata fields using Python Classes:

.. code-block:: python

    client = MetadataGroupsAPI()

    group_fields = []

    group_fields.append(GroupField(field_id="issuing_country", name="Issuing Country", field_type=GroupFieldType.STRING))
    group_fields.append(GroupField(field_id="issue_date", name="Issue Date", field_type=GroupFieldType.DATE))

    client.add_group(group_name="my group", description="my group description", fields=group_fields)


Adding new Fields
^^^^^^^^^^^^^^^^^^^^^

You can add new metadata fields to an existing Group using

.. code-block:: python

    client = MetadataGroupsAPI()

    new_fields = []

    new_fields.append(GroupField(field_id="issuing_country", name="Issuing Country", field_type=GroupFieldType.STRING))
    new_fields.append(GroupField(field_id="issue_date", name="Issue Date", field_type=GroupFieldType.DATE))

    client.add_fields(group_id="my group",  new_fields=new_fields)

The new fields are appended to the end of the group metadata.