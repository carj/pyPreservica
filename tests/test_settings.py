import pytest

from pyPreservica.settingsAPI import SettingsAPI


def setup():
    pass


def tear_down():
    pass


@pytest.fixture
def setup_data():
    setup()
    yield
    tear_down()



def test_get_enrichment_profiles(setup_data):
    client = SettingsAPI()
    profiles = client.metadata_enrichment_profiles()
    assert profiles is not None

def test_can_add_enrichment_profile(setup_data):
    client = SettingsAPI()