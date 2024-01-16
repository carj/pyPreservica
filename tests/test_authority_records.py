import pytest
from pyPreservica import *


def test_get_tables():
    client = AuthorityAPI()
    results = client.tables()
    assert isinstance(results, set)
    for table in results:
        assert isinstance(table, Table)
        assert table.name in ["Countries",  'Physical Storage']


def test_get_records():
    client = AuthorityAPI()
    tables = client.tables()
    for tab in tables:
        records = client.records(tab)


