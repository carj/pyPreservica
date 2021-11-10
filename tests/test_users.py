from pyPreservica import *


def test_get_all_users():
    client = AdminAPI()
    users = client.all_users()
    assert type(users) is list
    for username in users:
        assert type(username) is str
    assert client.username in users


def test_get_user():
    client = AdminAPI()
    user = client.user_details(client.username)
    assert type(user) is dict
    assert user['UserName'] == client.username
    assert type(user['Roles']) is list
    assert 'SDB_MANAGER_USER' in user['Roles']


def test_add_user():
    client = AdminAPI()
    user = client.add_user("pypreservica@gmail.com", "pypreservica", ['SDB_MANAGER_USER', 'SDB_INGEST_USER'])
    assert user['UserName'] == "pypreservica@gmail.com"
    user = client.user_details(user['UserName'])
    assert user['UserName'] == "pypreservica@gmail.com"
    assert "pypreservica@gmail.com" in client.all_users()
    client.delete_user("pypreservica@gmail.com")
    assert "pypreservica@gmail.com" not in client.all_users()


def test_change_display_name():
    client = AdminAPI()
    user = client.add_user("pypreservica@gmail.com", "pypreservica", ['SDB_MANAGER_USER', 'SDB_INGEST_USER'])
    assert user['UserName'] == "pypreservica@gmail.com"
    assert user['FullName'] == "pypreservica"
    client.change_user_display_name(user['UserName'], "pypreservica full name")
    user = client.user_details(user['UserName'])
    assert user['FullName'] == "pypreservica full name"
    client.delete_user("pypreservica@gmail.com")


