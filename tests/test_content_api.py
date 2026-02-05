import pytest

from pyPreservica import *

FOLDER_ID = "ebd977f6-bebd-4ecf-99be-e054989f9af4"
ASSET_ID = "683f9db7-ff81-4859-9c03-f68cfa5d9c3d"
CO_ID = "0f2997f7-728c-4e55-9f92-381ed1260d70"




def setup():
    pass


def tear_down():
    pass


@pytest.fixture
def setup_data():
    print("\nSetting up resources...")

    setup()

    yield

    print("\nTearing down resources...")

    tear_down()


def test_get_asset_details(setup_data):
    client = ContentAPI()
    json_dict = client.object_details(EntityType.ASSET, ASSET_ID)
    assert json_dict is not None
    assert json_dict['id'] == 'sdb:IO|683f9db7-ff81-4859-9c03-f68cfa5d9c3d'
    assert json_dict['name'] == 'LC-USZ62-20901'


def test_download_asset(setup_data):
    client = ContentAPI()
    filename = client.download(ASSET_ID, "filename.img")
    assert os.path.exists(filename)
    os.remove(filename)


def test_download_folder(setup_data):
    client = ContentAPI()
    with pytest.raises(RuntimeError):
        filename = client.download(FOLDER_ID, "filename.img")


def test_get_thumbnail_small(setup_data):
    client = ContentAPI()
    small = client.thumbnail("IO", "464444f7-8a6e-40f3-86c3-1dd2a51cfeeb", "filename.img", Thumbnail.SMALL)
    assert os.path.exists(small)
    os.remove(small)


def test_get_thumbnail_med(setup_data):
    client = ContentAPI()
    med = client.thumbnail("IO", "8d268bed-93d7-449b-91e4-2e7e86562a07", "filename.img", Thumbnail.MEDIUM)
    assert os.path.exists(med)
    os.remove(med)


def test_get_thumbnail_large(setup_data):
    client = ContentAPI()
    large = client.thumbnail("IO", "d5048e76-79c5-4ca7-99c9-a202c8f6dc8b", "filename.img", Thumbnail.LARGE)
    assert os.path.exists(large)
    os.remove(large)


def test_get_indexed_fields(setup_data):
    client = ContentAPI()
    fields = client.indexed_fields()
    assert fields is not None
    assert 'xip.title' in fields
    assert 'xip.description' in fields


def test_simple_search_list(setup_data):
    client = ContentAPI()
    results = list(client.simple_search_list(query="pyPreservica"))
    assert len(results) == 5
    assert results.pop()['xip.reference'] == '9fd239eb-19a3-4a46-9495-40fd9a5d8f93'


def test_simple_search_list2(setup_data):
    client = ContentAPI()

    columns = ["xip.reference", "xip.title", "xip.description", "xip.document_type"]

    results = list(client.simple_search_list("pyPreservica", 25, columns))
    assert len(results) == 5
    assert results.pop()['xip.reference'] == '9fd239eb-19a3-4a46-9495-40fd9a5d8f93'


def test_field_search(setup_data):
    search = ContentAPI()
    for result in search.search_index_filter_list(query="%", filter_values={"xip.security_descriptor": "open",
                                                                         "xip.document_type": "IO",
                                                                         "xip.parent_hierarchy": FOLDER_ID}):
        assert result is not None



def test_search_index_filter_hits(setup_data):
    search = ContentAPI()

    hits_closed: int = search.search_index_filter_hits(query="%", filter_values={"xip.security_descriptor": "closed"})
    hits_open:int = search.search_index_filter_hits(query="%", filter_values={"xip.security_descriptor": "open"})

    hits: int = search.search_index_filter_hits(query="%", filter_values={"xip.security_descriptor": ["open", "closed"]})

    assert hits > 0
    assert hits == hits_open + hits_closed


def test_search_index_filter_list(setup_data):
    search = ContentAPI()
    results_open = list(search.search_index_filter_list(query="%", filter_values={"xip.security_descriptor": "open",
                                                                          "xip.document_type": "IO",  "xip.parent_hierarchy":"ce3895dc-adec-4e20-9326-e1b36ffb60df"}))

    results_closed = list(search.search_index_filter_list(query="%", filter_values={"xip.security_descriptor": "closed",
                                                                                  "xip.document_type": "IO", "xip.parent_hierarchy":"ce3895dc-adec-4e20-9326-e1b36ffb60df"}))

    results_open_closed = list(search.search_index_filter_list(query="%", filter_values={"xip.security_descriptor": ["open", "closed"],
                                                                                    "xip.document_type": "IO", "xip.parent_hierarchy":"ce3895dc-adec-4e20-9326-e1b36ffb60df"}))
    assert len(results_open_closed) > 0
    assert len(results_open_closed) == len(results_open) + len(results_closed)


def test_search_fields(setup_data):
    search = ContentAPI()

    f1 = Field(name="xip.security_descriptor", value="open")
    f2 = Field(name="xip.document_type", value="IO")
    f3 = Field(name="xip.parent_hierarchy", value="ce3895dc-adec-4e20-9326-e1b36ffb60df")

    fields_open = list(search.search_fields(query="%",  fields=[f1,f2,f3]))

    results_open = list(search.search_index_filter_list(query="%", filter_values={"xip.security_descriptor": "open",
                                                                                  "xip.document_type": "IO",
                                                                                  "xip.parent_hierarchy": "ce3895dc-adec-4e20-9326-e1b36ffb60df"}))
    assert len(fields_open) > 0
    assert len(fields_open) == len(results_open)



def test_search_fields_with_list(setup_data):
    search = ContentAPI()

    f1 = Field(name="xip.security_descriptor", value=["open", "closed"])
    f2 = Field(name="xip.document_type", value="SO")
    f3 = Field(name="xip.parent_hierarchy", value="ce3895dc-adec-4e20-9326-e1b36ffb60df")

    fields_open = list(search.search_fields(query="%",  fields=[f1,f2,f3]))

    results_open = list(search.search_index_filter_list(query="%", filter_values={"xip.security_descriptor": ["open", "closed"],
                                                                                  "xip.document_type": "SO",
                                                                                  "xip.parent_hierarchy": "ce3895dc-adec-4e20-9326-e1b36ffb60df"}))
    assert len(fields_open) > 0
    assert len(fields_open) == len(results_open)


def test_search_fields_with_list2(setup_data):
    search = ContentAPI()

    f1 = Field(name="xip.security_descriptor", value=["open", "closed"])
    f2 = Field(name="xip.document_type", value="SO", operator=Operator.NOT)
    f3 = Field(name="xip.parent_hierarchy", value="ce3895dc-adec-4e20-9326-e1b36ffb60df")

    fields_open = list(search.search_fields(query="%",  fields=[f1,f2,f3]))

    results_open = list(search.search_index_filter_list(query="%", filter_values={"xip.security_descriptor": ["open", "closed"],
                                                                                  "xip.document_type": "IO",
                                                                                  "xip.parent_hierarchy": "ce3895dc-adec-4e20-9326-e1b36ffb60df"}))

    assert len(fields_open) > 0

    assert len(fields_open) == len(results_open)