import pytest
from pyPreservica import *


def test_cam_get_all_groups_as_objects():
    client = MetadataGroupsAPI()
    assert len(list(client.groups())) > 0
    for g in client.groups():
        assert isinstance(g, Group)
        assert g.group_id is not None
        assert g.name is not None
        assert g.schemaUri is not None


def test_cam_get_all_groups_as_JSON():
    client = MetadataGroupsAPI()
    for g in client.groups_json():
        if g['name'] == "digiteek":
            assert g['schemaUri'] == 'http://www.preservica.com/metadata/group/digiteek'
        if g['name'] == 'McD Metadata':
            assert g['schemaUri'] == 'http://www.preservica.com/metadata/group/mcd_metadata'


def test_can_get_group():
    client = MetadataGroupsAPI()
    for g in client.groups():
        if g.name == "digiteek":
            full_group: Group = client.group(g.group_id)
            assert full_group.name == "digiteek"
            assert full_group.description == "digiteek"
            assert len(full_group.fields) == 19
            break


def test_can_add_group_by_object():
    client = MetadataGroupsAPI()
    group1: Group = Group("my_group_name1", "my_group_description1")
    group1.fields.append(GroupField(field_id="attribute_1", name="Attribute 1x", field_type=GroupFieldType.STRING))
    group1.fields.append(GroupField(field_id="attribute_2", name="Attribute 2x", field_type=GroupFieldType.NUMBER))
    group1.fields.append(GroupField(field_id="attribute_3", name="Attribute 3x", field_type=GroupFieldType.DATE))

    g1: dict = client.add_group(group1.name, group1.description, group1.fields)

    assert g1['name'] == group1.name
    assert g1['description'] == group1.description

    assert len(g1['fields']) == 3

    group1: Group = client.group(g1['id'])

    client.delete_group(group1.group_id)


def test_can_add_new_fields_to_group():
    client = MetadataGroupsAPI()

    group2: Group = Group("test_group_1", "test_group_1_description")

    assert len(group2.fields) == 0

    group2.fields.append(GroupField(field_id="attribute_11", name="Attribute 11", field_type=GroupFieldType.STRING))
    group2.fields.append(GroupField(field_id="attribute_22", name="Attribute 22", field_type=GroupFieldType.NUMBER))
    group2.fields.append(GroupField(field_id="attribute_33", name="Attribute 33", field_type=GroupFieldType.DATE))

    assert len(group2.fields) == 3

    g2: dict = client.add_group(group2.name, group2.description, group2.fields)

    assert g2['name'] == group2.name
    assert g2['description'] == group2.description

    assert len(g2['fields']) == 3

    group_id = g2['id']

    group3: Group = client.group(group_id)

    assert g2['name'] == group3.name
    assert g2['description'] == group3.description

    new_fields = []

    new_fields.append(GroupField(field_id="attribute_4", name="Attribute 4", field_type=GroupFieldType.LONG_STRING))
    new_fields.append(GroupField(field_id="attribute_5", name="Attribute 5", field_type=GroupFieldType.NUMBER))

    client.add_fields(group_id, new_fields)

    group4: Group = client.group(group_id)

    assert len(group4.fields) == 5

    client.delete_group(group_id)


def test_can_get_group_by_URI():
    client = MetadataGroupsAPI()
    uri = "http://www.preservica.com/metadata/group/mcd_metadata"
