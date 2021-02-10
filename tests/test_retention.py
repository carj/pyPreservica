import pytest
from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"


def test_get_assignments():
    client = EntityAPI()
    retention = RetentionAPI()

    asset = client.asset(ASSET_ID)

    polices = retention.assignments(asset)
    for p in polices:
        print(p)


def test_get_policies():
    retention = RetentionAPI()
    for p in retention.policies():
        p = retention.policy(p.ref)
        print(p.name)
        print(p.ref)
        print(p.description)
        print(p.security_tag)
        print(p.start_date_field)
        print(p.period)
        print(p.period_unit)
        print(p.expiry_action)
        print(p.restriction)
        print(p.assignable)

