import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_get_policy_by_name():
    retention = RetentionAPI()
    policy = retention.policy_by_name("Standard Policy")
    assert policy.name == "Standard Policy"


def test_get_policies():
    retention = RetentionAPI()
    for p in retention.policies():
        print(p.name)
        print(p.reference)
        print(p.description)
        print(p.security_tag)
        print(p.start_date_field)
        print(p.period)
        print(p.period_unit)
        print(p.expiry_action)
        print(p.restriction)
        print(p.assignable)


def test_create_policy():
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

    retention.create_policy(**args)

    policy = retention.policy_by_name("API Created Policy")

    assert policy.name == "API Created Policy"

    retention.delete_policy(policy.reference)


def test_update_existing_policy():
    retention = RetentionAPI()

    args = dict()
    args['Name'] = "API Created Policy1"
    args['Description'] = "Policy Description"
    args['SecurityTag'] = "open"
    args['StartDateField'] = "xip.created"
    args['Period'] = "6"
    args['PeriodUnit'] = "YEAR"
    args['ExpiryAction'] = "REVIEW"
    args['ExpiryActionParameters'] = "{\"EmailAddress\":[\"test@emailaddress1.com\",\"test@emailaddress2.com\"]}"
    args['Restriction'] = "DELETE"
    args['Assignable'] = bool(False)

    retention.create_policy(**args)

    policy = retention.policy_by_name("API Created Policy1")

    args['Period'] = "8"

    retention.update_policy(policy.reference, **args)

    retention.delete_policy(policy.reference)


def test_get_assignments():
    client = EntityAPI()
    retention = RetentionAPI()

    asset = client.asset("b14848b5-4c4d-4d8a-b394-3b764069ee93")

    retention_assignments = retention.assignments(asset)

    assert len(retention_assignments) == 1

    retention_assignment = retention_assignments.pop()

    assert retention_assignment.entity_reference == "b14848b5-4c4d-4d8a-b394-3b764069ee93"

    policy = retention.policy(retention_assignment.policy_reference)

    assert policy.name == "HR Records"


def test_add_assignments():
    client = EntityAPI()
    retention = RetentionAPI()

    asset = client.asset("799b467f-050d-415f-b8ec-7c74b343f628")

    retention_assignments = retention.assignments(asset)

    assert len(retention_assignments) == 0

    policy = retention.policies().pop()

    if not policy.assignable:
        retention.assignable_policy(policy.reference, True)

    retention_assignment = retention.add_assignments(asset, policy)

    assert retention_assignment is not None

    retention_assignments = retention.assignments(asset)

    assert len(retention_assignments) == 1

    retention.remove_assignments(retention_assignment)

    retention.assignable_policy(policy.reference, False)


def test_zdelete_policy():
    retention = RetentionAPI()
    for policy in retention.policies():
        if policy.name == "API Created Policy1":
            retention.delete_policy(policy.reference)


