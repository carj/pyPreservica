import pytest
import json
from pyPreservica import *


def test_format_families():
    par = PreservationActionRegistry()
    document = par.format_families()
    assert len(json.loads(document)['formatFamilies']) == 131


def test_format_family():
    par = PreservationActionRegistry()
    document = par.format_family('ae87efa4-cd5a-5d07-b1b7-251a4fe871c8')
    ogg = json.loads(document)
    assert ogg['id']['name'] == "ogg"


def test_preservation_action_types():
    par = PreservationActionRegistry()
    document = par.preservation_action_types()
    assert len(json.loads(document)['preservationActionTypes']) == 9


def test_preservation_action_type():
    par = PreservationActionRegistry()
    document = par.preservation_action_type('658b595a-a516-56fd-9a53-aaa561d18020')
    ffa = json.loads(document)
    assert ffa['id']['name'] == "ffa"


def test_properties():
    par = PreservationActionRegistry()
    document = par.properties()
    assert len(json.loads(document)['parProperties']) == 101


def test_property():
    par = PreservationActionRegistry()
    document = par.property('00bfe91a-eb9d-540c-8b00-0497701d773a')
    ffa = json.loads(document)
    assert ffa['id']['name'] == "prp/1"
