import pytest
from pyPreservica import *


def test_get_tags():
    client = EntityAPI()
    for tag in client.user_security_tags():
        print(tag)
