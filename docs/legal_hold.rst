=================
Legal Hold API
=================

https://demo.preservica.com/api/entity/documentation.html#/%2Flegal-holds


----------------------
List Legal Holds
----------------------

Fetch a list of all system legal holds, this returns a Generator object which returns LegalHold objects.

.. code-block:: python

    client = LegalHoldAPI()

    for hold in client.legal_holds():
        print(hold)


If you know the name of the legal hold, you can pass it as an argument. This filters the result set to those who
have a match on the name

.. code-block:: python

    client = LegalHoldAPI()

    for hold in client.legal_holds('My Legal Hold'):
        print(hold)

If you have the unique reference of the legal hold object use:

.. code-block:: python

    client = LegalHoldAPI()

    hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7'):


------------------------
Create New Legal Holds
------------------------

You can create a new Legal Hold object via the following method:

.. code-block:: python

    client = LegalHoldAPI()

    hold = client.create_hold(name = "My Hold",  description = "The Hold Description")
    print(hold)

This function will automatically add a date and time stamp and assign the current user as the hold owner.
The description is optional.


------------------------
Delete Legal Holds
------------------------

You can delete a Legal Hold object either by its unique reference or its name

.. code-block:: python

    client = LegalHoldAPI()

    client.delete_hold('60b05dea-40a0-483a-b78f-65442d16b9d7')

or

.. code-block:: python

    client = LegalHoldAPI()

    client.delete_hold('My Hold')



------------------------
Update Legal Holds
------------------------

You can change the name or description of an existing Legal Hold using:

.. code-block:: python

    client = LegalHoldAPI()

    hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7'):

    hold.name = "New Name"

    client.update_legal_hold(hold)



----------------------------------
Putting an Asset under Legal Hold
----------------------------------

This call requires the user's role to have UPDATE_LEGAL_HOLD permission on the Assets security tag.

To put an asset under a hold, the asset must be assigned to the hold.

Once under a legal hold, the Asset cannot be deleted or updated.

.. code-block:: python

    client = LegalHoldAPI()
    entity = EntityAPI()

    legal_hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7'):

    asset: Asset = entity.asset('123e4567-e89b-12d3-a456-426614174000')

    client.assign_legal_hold(asset, legal_hold)


for example, to place all assets within a folder under legal hold:

.. code-block:: python

    client = LegalHoldAPI()
    entity = EntityAPI()

    legal_hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7'):

    for asset in filter(only_assets, entity.descendants('123e4567-e89b-12d3-a456-426614174000')):
        client.assign_legal_hold(asset, legal_hold)


----------------------------------
Removing an Asset from Legal Hold
----------------------------------

This call requires the user's role to have UPDATE_LEGAL_HOLD permission on the Assets security tag.

.. code-block:: python

    client = LegalHoldAPI()
    entity = EntityAPI()

    legal_hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7'):

    asset: Asset = entity.asset('123e4567-e89b-12d3-a456-426614174000')

    client.remove_legal_hold_assignment(asset, legal_hold)


----------------------------------
Finding Assets under Legal Hold
----------------------------------

To find all Assets which have a legal hold applied use:

.. code-block:: python

    client = LegalHoldAPI()

    for assignment in client.find():
        print(assignment)