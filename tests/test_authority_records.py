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
        assert table.name in ["Countries", 'Physical Storage']


def test_get_records(setup_data):
    client = AuthorityAPI()
    tables = client.tables()
    for tab in tables:
        records = client.records(tab)
