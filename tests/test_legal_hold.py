import uuid
from time import sleep

import pytest
from pyPreservica import *
from pyPreservica.retentionAPI import LegalHold


ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"

def setup():
    pass

def tear_down():
    pass

@pytest.fixture
def setup_data(request):
    print(f"\nRunning test: {request.node.name}")

    setup()
    yield
    tear_down()


def test_uuid():
    reference: str = '60b05dea-40a0-483a-b78f-65442d16b9d7'
    with pytest.raises(ValueError):
        uuid.UUID(f'urn:uuid:name')

    uuid.UUID(f'urn:uuid:{reference}')

def test_holds(setup_data):
    client = LegalHoldAPI()
    for hold in client.legal_holds():
        assert isinstance(hold, LegalHold)


def test_find_hold_by_name(setup_data):
    client = LegalHoldAPI()
    for hold in client.legal_holds(name="FAA"):
        assert isinstance(hold, LegalHold)
        assert hold.name == "FAA Investigation"
        assert hold.description == "Legal Hold"
        assert hold.user == "carj_preview_sales_manager@preservica.com"
        assert str(hold.create_date.date()) == "2026-07-06"


def test_create_new_hold(setup_data):
    client = LegalHoldAPI()
    lh = client.create_hold(name = 'Criminal Case', description = 'do not delete')
    for hold in client.legal_holds(name="Criminal Case"):
        assert isinstance(hold, LegalHold)
        assert hold.name == "Criminal Case"
        assert hold.description == "do not delete"


def test_delete_legal_hold(setup_data):
    client = LegalHoldAPI()
    client.delete_legal_hold("Criminal Case")

def test_get_hold_by_ref(setup_data):
    client = LegalHoldAPI()
    hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7')
    assert isinstance(hold, LegalHold)
    assert hold.name == "FAA Investigation"
    assert hold.description == "Legal Hold"
    assert hold.user == "carj_preview_sales_manager@preservica.com"
    assert str(hold.create_date.date()) == "2026-07-06"


def test_assign_legal_hold(setup_data):
    client = LegalHoldAPI()
    entity = EntityAPI()

    asset: Asset = entity.asset(ASSET_ID)
    legal_hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7')

    client.assign_legal_hold(asset, legal_hold)

    # try and change the title
    asset.title = "Under Legal Hold"
    with pytest.raises(HTTPException):
        entity.save(asset)


def test_remove_legal_hold(setup_data):
    client = LegalHoldAPI()
    entity = EntityAPI()
    asset: Asset = entity.asset(ASSET_ID)
    legal_hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7')

    client.remove_legal_hold_assignment(asset, legal_hold)

    t = asset.title
    asset.title = "Not Under Legal Hold"
    entity.save(asset)

    asset.title = t
    entity.save(asset)

def test_get_holds_on_asset(setup_data):
    client = LegalHoldAPI()
    entity = EntityAPI()
    asset: Asset = entity.asset(ASSET_ID)

    for legal_hold in client.legal_holds():
        client.assign_legal_hold(asset, legal_hold)

    holds = client.asset_holds(asset)

    assert len(holds) == 2

    for legal_hold in client.legal_holds():
        client.remove_legal_hold_assignment(asset, legal_hold)


def test_find_assignments(setup_data):
    client = LegalHoldAPI()
    entity = EntityAPI()
    asset: Asset = entity.asset(ASSET_ID)
    legal_hold: LegalHold = client.legal_hold('60b05dea-40a0-483a-b78f-65442d16b9d7')

    client.assign_legal_hold(asset, legal_hold)

    sleep(5)

    assignments = list(client.find())

    assert len(assignments) == 1

    client.remove_legal_hold_assignment(asset, legal_hold)