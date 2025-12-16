import pytest
from pyPreservica import *


def setup():
    client = AdminAPI()
    users = client.all_users()
    for u in users:
        if u  ==  "pypreservica@gmail.com":
            client.delete_user(u)



def tear_down():
    pass


@pytest.fixture
def setup_data():
    print("\nSetting up resources...")

    setup()

    yield

    print("\nTearing down resources...")

    tear_down()



def test_get_all_users(setup_data):
    client = AdminAPI()
    users = client.all_users()
    assert type(users) is list
    for username in users:
        assert type(username) is str
    assert client.username in users


def test_get_user(setup_data):
    client = AdminAPI()
    user = client.user_details(client.username)
    assert type(user) is dict
    assert user['UserName'] == client.username
    assert type(user['Roles']) is list
    assert 'SDB_MANAGER_USER' in user['Roles']


def test_add_user(setup_data):
    client = AdminAPI()
    user = client.add_user("pypreservica@gmail.com", "pypreservica", ['SDB_MANAGER_USER', 'SDB_INGEST_USER'])
    assert user['UserName'] == "pypreservica@gmail.com"
    user = client.user_details(user['UserName'])
    assert user['UserName'] == "pypreservica@gmail.com"
    assert "pypreservica@gmail.com" in client.all_users()
    client.delete_user("pypreservica@gmail.com")
    assert "pypreservica@gmail.com" not in client.all_users()


def test_change_display_name(setup_data):
    client = AdminAPI()
    user = client.add_user("pypreservica@gmail.com", "pypreservica", ['SDB_MANAGER_USER', 'SDB_INGEST_USER'])
    assert user['UserName'] == "pypreservica@gmail.com"
    assert user['FullName'] == "pypreservica"
    client.change_user_display_name(user['UserName'], "pypreservica full name")
    user = client.user_details(user['UserName'])
    assert user['FullName'] == "pypreservica full name"
    client.delete_user("pypreservica@gmail.com")


