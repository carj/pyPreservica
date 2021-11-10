import pytest
from pyPreservica import *


def test_get_tags():
    client = EntityAPI()
    tags = client.user_security_tags()
    assert type(tags) is dict
    assert "open" in tags


def test_all_tags():
    client = AdminAPI()
    tags = client.security_tags()
    assert type(tags) is list
    assert "open" in tags


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

