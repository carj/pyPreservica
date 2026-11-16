import json
import uuid

import pytest
from pyPreservica import *

# A single, re-usable table for these tests. The reference metadata API has no way to
# delete a table, so the tests look for this table by name and only create it if missing.
TEST_TABLE_NAME = "pyPreservica API Test Table"
TEST_TABLE_DESCRIPTION = "Table used by the pyPreservica AuthorityAPI tests"

UNKNOWN_REFERENCE = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
def setup_data(request):
    print(f"\nRunning test: {request.node.name}")
    yield


@pytest.fixture(scope="module")
def client():
    return AuthorityAPI()


@pytest.fixture(scope="module")
def test_table(client):
    table = find_table(client, TEST_TABLE_NAME)
    if table is None:
        new_table = Table(name=TEST_TABLE_NAME, security_tag="open", displayField="creator")
        new_table.description = TEST_TABLE_DESCRIPTION
        new_table.fields = [
            {"name": "id", "type": "ShortText", "displayName": "ID", "includeInSummary": True},
            {"name": "creator", "type": "ShortText", "displayName": "The Creator", "includeInSummary": True},
        ]
        table = client.add_table(new_table)

    yield table

    # remove any records left behind by failed tests
    for record in client.records(table):
        client.delete_record(record['ref'])


def find_table(client, name):
    for table in client.tables():
        if table.name == name:
            return table
    return None


def record_refs(client, table):
    return {record['ref'] for record in client.records(table)}


def field_values(record: dict) -> dict:
    return {field['name']: field.get('value') for field in record.get('fieldValues', [])}


# ---------------------------------------------------------------- tables

def test_get_tables(setup_data, client):
    results = client.tables()
    assert isinstance(results, set)
    for table in results:
        assert isinstance(table, Table)
        assert table.reference is not None
        assert table.name is not None


def test_tables_contains_test_table(setup_data, client, test_table):
    refs = {table.reference for table in client.tables()}
    assert test_table.reference in refs


def test_table_by_reference(setup_data, client, test_table):
    table = client.table(test_table.reference)
    assert isinstance(table, Table)
    assert table.reference == test_table.reference
    assert table.name == TEST_TABLE_NAME
    assert table.security_tag == "open"
    assert table.description == TEST_TABLE_DESCRIPTION
    assert table.fields is not None
    assert {"id", "creator"} <= {field['name'] for field in table.fields}


def test_table_str(setup_data, client, test_table):
    text = str(client.table(test_table.reference))
    assert test_table.reference in text
    assert TEST_TABLE_NAME in text


def test_table_unknown_reference(setup_data, client):
    with pytest.raises(HTTPException):
        client.table(UNKNOWN_REFERENCE)


def test_add_table(setup_data, client):
    pytest.skip("Creates a new table on every run and tables cannot be deleted")
    name: str = f"Test Table {datetime.now().date()}"
    table = Table(name=name, security_tag="open")
    table.description = "An API test table"
    table.fields = [{"name": "creator", "type": "ShortText", "displayName": "The Creator", "includeInSummary": True}]
    new_table = client.add_table(table)
    assert new_table.name == name
    assert new_table.reference is not None


# ---------------------------------------------------------------- records

def test_get_records(setup_data, client):
    for table in client.tables():
        records = client.records(table)
        assert isinstance(records, list)


def test_add_record(setup_data, client, test_table):
    creator = f"Creator {uuid.uuid4()}"
    before = record_refs(client, test_table)

    response = client.add_record(test_table, {"ID": "1", "Creator": creator})
    ref = json.loads(response)['ref']
    try:
        assert ref not in before
        assert record_refs(client, test_table) == before | {ref}

        record = client.record(ref)
        assert isinstance(record, dict)
        assert record['ref'] == ref
        values = field_values(record)
        assert values['creator'] == creator
        assert values['id'] == "1"
    finally:
        client.delete_record(ref)

    assert record_refs(client, test_table) == before


def test_records_expanded_field_values(setup_data, client, test_table):
    creator = f"Creator {uuid.uuid4()}"
    ref = json.loads(client.add_record(test_table, {"id": "2", "creator": creator}))['ref']
    try:
        matching = [r for r in client.records(test_table) if r['ref'] == ref]
        assert len(matching) == 1
        assert field_values(matching[0])['creator'] == creator
    finally:
        client.delete_record(ref)


def test_add_records_from_csv(setup_data, client, test_table, tmp_path):
    creators = [f"CSV Creator {i} {uuid.uuid4()}" for i in range(3)]
    csv_file = tmp_path / "records.csv"
    csv_file.write_text("creator\n" + "\n".join(creators) + "\n", encoding="utf-8")

    before = record_refs(client, test_table)
    client.add_records(test_table, str(csv_file), encoding="utf-8")
    new_refs = record_refs(client, test_table) - before
    try:
        assert len(new_refs) == 3
        added = {field_values(client.record(ref))['creator']: field_values(client.record(ref))['id']
                 for ref in new_refs}
        assert set(added) == set(creators)
        # without an id column the CSV line number is used as the id
        assert added[creators[0]] == "2"
        assert added[creators[2]] == "4"
    finally:
        for ref in new_refs:
            client.delete_record(ref)


def test_add_records_from_csv_with_id_column(setup_data, client, test_table, tmp_path):
    creator = f"CSV Creator {uuid.uuid4()}"
    csv_file = tmp_path / "records.csv"
    csv_file.write_text(f"ID,creator\nABC-123,{creator}\n", encoding="utf-8")

    before = record_refs(client, test_table)
    client.add_records(test_table, str(csv_file), encoding="utf-8")
    new_refs = record_refs(client, test_table) - before
    try:
        assert len(new_refs) == 1
        values = field_values(client.record(next(iter(new_refs))))
        assert values['id'] == "ABC-123"
        assert values['creator'] == creator
    finally:
        for ref in new_refs:
            client.delete_record(ref)


def test_record_unknown_reference(setup_data, client):
    with pytest.raises(HTTPException):
        client.record(UNKNOWN_REFERENCE)


def test_delete_record_unknown_reference(setup_data, client):
    with pytest.raises(HTTPException):
        client.delete_record(UNKNOWN_REFERENCE)


def test_record_gone_after_delete(setup_data, client, test_table):
    ref = json.loads(client.add_record(test_table, {"id": "3", "creator": "To be deleted"}))['ref']
    client.delete_record(ref)
    with pytest.raises(HTTPException):
        client.record(ref)
