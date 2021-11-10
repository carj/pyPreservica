Retention API
~~~~~~~~~~~~~~~~~~

https://eu.preservica.com/api/entity/documentation.html#/%2Fretention-policies

Retention Policies
^^^^^^^^^^^^^^^^^^^^^

Fetch a list of all retention policies

.. code-block:: python

    retention = RetentionAPI()

    for policy in retention.policies():
        print(policy)


Fetch a retention policy by its name


.. code-block:: python

    retention = RetentionAPI()

    policy = retention.policy_by_name("Standard Policy")


Create a new retention policy

.. code-block:: python

    retention = RetentionAPI()

    args = dict()
    args['Name'] = "API Created Policy"
    args['Description'] = "Policy Description"
    args['SecurityTag'] = "open"
    args['StartDateField'] = "xip.created"
    args['Period'] = "6"
    args['PeriodUnit'] = "YEAR"
    args['ExpiryAction'] = "REVIEW"
    args['ExpiryActionParameters'] = "{\"EmailAddress\":[\"test@emailaddress1.com\",\"test@emailaddress2.com\"]}"
    args['Restriction'] = "DELETE"
    args['Assignable'] = bool(True)

    policy = retention.create_policy(**args)


Delete a Policy

.. code-block:: python

    retention = RetentionAPI()

    retention.delete_policy(policy.reference)



Retention Assignments
^^^^^^^^^^^^^^^^^^^^^

Assign a policy onto an asset

.. code-block:: python

    client = EntityAPI()
    retention = RetentionAPI()

    asset = client.asset("c365634e-9fcc-4ea1-b47f-077f55df9d64")

    policy = retention.policy_by_name("Standard Policy")

    retention_assignment = retention.add_assignments(asset, policy)


List the retention assignments on a asset

.. code-block:: python

    client = EntityAPI()
    retention = RetentionAPI()

    asset = client.asset("c365634e-9fcc-4ea1-b47f-077f55df9d64")

    assignments = retention.assignments(asset)


Remove a policy assignment from an asset

.. code-block:: python

    client = EntityAPI()
    retention = RetentionAPI()

    retention_assignment = retention.remove_assignments(assignment)

