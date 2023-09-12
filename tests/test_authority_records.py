import pytest
from pyPreservica import *


def test_get_tables():
    client = AuthorityAPI()
    results = client.tables()
    assert isinstance(results, set)
    t = results.pop()
    assert isinstance(t, Table)
    assert t.name == "Countries"


def test_get_records():
    client = AuthorityAPI()
    tables = client.tables()
    for tab in tables:
        records = client.records(tab)


