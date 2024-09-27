import pytest
from pyPreservica import *


def test_cam_get_all_groups():
    client = MetadataGroupsAPI()
    for g in client.groups():
        assert isinstance(g, Group)
