import json

import pytest
from pyPreservica import *


def setup():
    pass

def tear_down():
    pass


@pytest.fixture
def setup_data():
    print("\nSetting up resources...")

    setup()

    yield

    print("\nTearing down resources...")

    tear_down()


def test_get_tables(setup_data):
    client = AuthorityAPI()
    results = client.tables()
    assert isinstance(results, set)
    for table in results:
        assert isinstance(table, Table)


def test_get_records(setup_data):
    client = AuthorityAPI()
    tables = client.tables()
    for tab in tables:
        records = client.records(tab)


def test_add_table(setup_data):
    client = AuthorityAPI()
    name: str = f"Test Table {datetime.now().date()}"
    table = Table(name=name, security_tag="open")
    table.description ="An API test table"
    table.fields = [{"name" : "creator", "type" : "ShortText", "displayName" : "The Creator", "includeInSummary" : True}]
    new_table = client.add_table(table)
    print(new_table)
    assert new_table.name == name


def test_add_record(setup_data):
    client = AuthorityAPI()
    the_table = None
    record_id = None
    for table in client.tables():
        if table.name == f"Test Table {datetime.now().date()}":
            i: int = len(client.records(table)) + 1
            record: dict = {"ID": i, "creator": "The Creator"}
            the_table = table
            record_id = client.add_record(table, record)
            break


    assert record_id is not None

    assert len(client.records(the_table)) > 0

    ref = json.loads(record_id)['ref']

    client.delete_record(ref)