import pytest
from pyPreservica import *

def setup():
    pass

def tear_down():
    pass

@pytest.fixture
def setup_data(request):
    print(f"\nRunning test: {request.node.name}")

    setup()
    yield
    tear_down()

def test_edition(setup_data):
    client = EntityAPI()
    assert client.edition() == "enterprise"

def test_check_user_has_manager_roles(setup_data):
    client = EntityAPI()
    client.roles = ['ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER']
    with pytest.raises(RuntimeError):
        client._check_if_user_has_manager_role()

    client.roles = ['ROLE_SDB_MANAGER_USER', 'ROLE_SDB_ACCESS_USER']
    client._check_if_user_has_manager_role()

    client.roles = ['ROLE_SDB_ADMIN_USER', 'ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER']
    client._check_if_user_has_manager_role()

    client.roles = ['ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER', 'ROLE_SDB_CONFIG_MANAGER_USER']
    with pytest.raises(RuntimeError):
        client._check_if_user_has_manager_role()


def test_check_user_has_config_manager_roles(setup_data):
    client = EntityAPI()
    client.roles = ['ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER']
    with pytest.raises(RuntimeError):
        client._check_if_user_has_config_manager_role()

    client.roles = ['ROLE_SDB_MANAGER_USER', 'ROLE_SDB_ACCESS_USER']
    client._check_if_user_has_config_manager_role()

    client.roles = ['ROLE_SDB_ADMIN_USER', 'ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER']
    client._check_if_user_has_config_manager_role()

    client.roles = ['ROLE_SDB_CONFIG_MANAGER_USER', 'ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER']
    client._check_if_user_has_config_manager_role()



def test_check_user_has_user_manager_roles(setup_data):
    client = EntityAPI()
    client.roles = ['ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER']
    with pytest.raises(RuntimeError):
        client._check_if_user_has_user_manager_role()

    client.roles = ['ROLE_SDB_MANAGER_USER', 'ROLE_SDB_ACCESS_USER']
    client._check_if_user_has_user_manager_role()

    client.roles = ['ROLE_SDB_ADMIN_USER', 'ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER']
    client._check_if_user_has_user_manager_role()

    client.roles = ['ROLE_SDB_USER_MANAGER_USER', 'ROLE_SDB_ACCESS_USER', 'ROLE_SDB_DATA_MANAGEMENT_USER']
    client._check_if_user_has_user_manager_role()
