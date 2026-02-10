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
        print(table)
        assert isinstance(table, Table)


def test_get_records(setup_data):
    client = AuthorityAPI()
    tables = client.tables()
    for tab in tables:
        print(tab)
        records = client.records(tab)
        print(records)


def test_add_table(setup_data):
    client = AuthorityAPI()
    name: str = f"Test Table {datetime.now().isoformat()}"
    table = Table(name=name, security_tag="open")
    table.description ="An API test table"
    table.fields = [{"name" : "creator", "type" : "ShortText", "displayName" : "The Creator", "includeInSummary" : True}]
    new_table = client.add_table(table)
    print(new_table)
    assert new_table.name == name
