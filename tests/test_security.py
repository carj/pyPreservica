import pytest
from pyPreservica import *


def test_get_tags():
    client = EntityAPI()
    tags = client.user_security_tags()
    assert type(tags) is dict
    assert "open" in tags


def test_get_roles():
    client = AdminAPI()
    roles = client.system_roles()
    assert type(roles) is list
    assert "ROLE_SDB_ACCESS_USER" in roles
    assert "ROLE_SDB_MANAGER_USER" in roles


def test_all_tags():
    client = AdminAPI()
    tags = client.security_tags()
    assert type(tags) is list
    assert "open" in tags


def test_add_remove_system_role():
    client = AdminAPI()
    roles = client.system_roles()
    assert type(roles) is list
    assert "ROLE_SDB_ACCESS_USER" in roles
    assert "ROLE_SDB_MANAGER_USER" in roles
    assert "ROLE_SDB_CUSTOM_EDIT_USER" not in roles
    r = client.add_system_role("SDB_CUSTOM_EDIT_USER")
    assert "ROLE_SDB_CUSTOM_EDIT_USER" == r
    roles = client.system_roles()
    assert "ROLE_SDB_CUSTOM_EDIT_USER" in roles
    client.delete_system_role("ROLE_SDB_CUSTOM_EDIT_USER")
    roles = client.system_roles()
    assert "SDB_CUSTOM_EDIT_USER" not in roles


def test_add_remove_security_tag():
    client = AdminAPI()
    tags = client.security_tags()
    assert type(tags) is list
    assert "top_secret_tag" not in tags
    assert "open" in tags
    client.add_security_tag("top_secret_tag")
    tags = client.security_tags()
    assert "top_secret_tag" in tags
    client.delete_security_tag("top_secret_tag")
    tags = client.security_tags()
    assert "top_secret_tag" not in tags


def test_add_remove_security_tag_old_version():
    client = AdminAPI()
    client.major_version = 6
    client.minor_version = 3
    client.patch_version = 6
    tags = client.security_tags()
    assert type(tags) is list
    assert "top_secret_tag" not in tags
    assert "open" in tags
    with pytest.raises(RuntimeError):
        client.add_security_tag("top_secret_tag")
