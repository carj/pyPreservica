import json

import pytest
from pyPreservica import *


class FakeClient:
    """ Offline stand-in for EntityAPI with a small folder hierarchy """

    server = "example.preservica.com"
    protocol = "https"
    tenant = "EXAMPLE"

    # parent reference -> list of (reference, title, type)
    TREE = {
        None: [("f1", "Photos", "F"), ("f2", "Documents", "F")],
        "f1": [("a1", "beach.tif", "A"), ("f3", "2024", "F")],
        "f3": [("a2", "party.tif", "A"), ("a3", "cake.tif", "A")],
        "f2": [("a4", "report.pdf", "A")],
    }

    # asset reference -> {representation type: [bitstream sizes]}
    SIZES = {
        "a1": {RepresentationType.Preservation: [1000], RepresentationType.Access: [100]},
        "a2": {RepresentationType.Preservation: [2000, 500]},
        "a3": {RepresentationType.Preservation: [3000]},
        "a4": {RepresentationType.Preservation: [50]},
    }

    def folder(self, reference):
        for children in self.TREE.values():
            for ref, title, _ in children:
                if ref == reference:
                    return Folder(ref, title)
        raise ReferenceNotFoundException(reference, 404, "", "folder")

    def descendants(self, folder=None):
        ref = folder.reference if folder is not None else None
        for child_ref, title, entity_type in self.TREE.get(ref, []):
            yield Folder(child_ref, title, parent=ref) if entity_type == "F" else Asset(child_ref, title, parent=ref)

    def representations(self, asset):
        return {Representation(asset, rep_type, rep_type.value, f"{asset.reference}/{rep_type.value}")
                for rep_type in self.SIZES.get(asset.reference, {})}

    def content_objects(self, representation):
        co = ContentObject(representation.url, "co")
        co.sizes = self.SIZES[representation.asset.reference][representation.rep_type]
        return [co]

    def generations(self, content_object):
        bitstreams = [Bitstream(f"file{i}", size, {}, f"{content_object.reference}/{i}")
                      for i, size in enumerate(content_object.sizes)]
        return [Generation(True, True, "", "", bitstreams), Generation(False, False, "", "", bitstreams)]


def test_scan_repository():
    report = StorageUsageReport(FakeClient(), show_progress=False)
    root = report.scan()
    assert root.size == 1000 + 100 + 2000 + 500 + 3000 + 50
    assert root.asset_count == 4
    assert root.bitstream_count == 6
    # children are sorted largest first
    assert [c.title for c in root.children] == ["Photos", "Documents"]
    photos = root.children[0]
    assert photos.size == 6600
    assert photos.children[0].title == "2024"
    assert photos.children[0].size == 5500


def test_scan_folder_preservation_only():
    report = StorageUsageReport(FakeClient(), representation_types=[RepresentationType.Preservation],
                                max_workers=1, show_progress=False)
    root = report.scan("f1")
    assert root.title == "Photos"
    assert root.size == 6500


def test_largest():
    report = StorageUsageReport(FakeClient(), show_progress=False)
    report.scan()
    assert [n.title for n in report.largest(2)] == ["cake.tif", "party.tif"]
    assert report.largest(1, EntityType.FOLDER)[0].title == "Photos"


def test_json_round_trip_and_html(tmp_path):
    report = StorageUsageReport(FakeClient(), show_progress=False)
    report.scan()
    json_file = report.save_json(str(tmp_path / "usage.json"))

    reloaded = StorageUsageReport(None, show_progress=False)
    root = reloaded.load_json(json_file)
    assert root.size == report.root.size
    assert root.children[0].children[0].title == "2024"
    assert reloaded.tenant == "EXAMPLE"
    assert reloaded.server == "example.preservica.com"

    html_file = report.render_html(str(tmp_path / "usage.html"))
    with open(html_file, encoding="utf-8") as fd:
        page = fd.read()
    assert "<svg" in page
    start = page.index("const DATA = ") + len("const DATA = ")
    data = json.loads(page[start:page.index(";\n", start)])
    assert data["tree"]["size"] == root.size
    assert data["tenant"] == "EXAMPLE"
    assert data["server"] == "example.preservica.com"


def test_no_scan_raises():
    with pytest.raises(RuntimeError):
        StorageUsageReport(FakeClient(), show_progress=False).render_html("x.html")


def test_human_size():
    from pyPreservica.reportingAPI import human_size
    assert human_size(512) == "512 B"
    assert human_size(1536) == "1.5 KiB"
    assert human_size(97 * 1024 ** 3) == "97.0 GiB"


@pytest.fixture
def offline_reporting_api(monkeypatch):
    """ A ReportingAPI which does not log in, and whose EntityAPI client is a FakeClient """
    import pyPreservica.reportingAPI as reporting
    created = []

    def fake_auth_init(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False,
                       two_fa_secret_key=None, protocol="https", request_hook=None, credentials_path=None):
        self.username, self.password, self.tenant, self.server = username, password, tenant, server
        self.shared_secret, self.two_fa_secret_key, self.protocol = use_shared_secret, two_fa_secret_key, protocol

    def fake_entity_api(**kwargs):
        client = FakeClient()
        client.kwargs = kwargs
        created.append(client)
        return client

    monkeypatch.setattr(AuthenticatedAPI, "__init__", fake_auth_init)
    monkeypatch.setattr(reporting, "EntityAPI", fake_entity_api)
    api = ReportingAPI(username="user", password="pass", tenant="EXAMPLE", server="example.preservica.com")
    return api, created


def test_reporting_api_storage_usage_report(offline_reporting_api, tmp_path):
    api, created = offline_reporting_api
    html_file = tmp_path / "usage.html"
    report = api.storage_usage_report("f1", filename=str(html_file),
                                      representation_types=[RepresentationType.Preservation], show_progress=False)
    assert report.root.title == "Photos"
    assert report.root.size == 6500
    assert html_file.exists()
    assert "Photos" in html_file.read_text(encoding="utf-8")
    # the EntityAPI client is created with the same credentials
    assert created[0].kwargs["username"] == "user"
    assert created[0].kwargs["tenant"] == "EXAMPLE"
    assert created[0].kwargs["server"] == "example.preservica.com"


def test_reporting_api_reuses_entity_client(offline_reporting_api, tmp_path):
    api, created = offline_reporting_api
    api.storage_usage_report(filename=str(tmp_path / "a.html"), show_progress=False)
    api.storage_usage_report(filename=str(tmp_path / "b.html"), show_progress=False)
    assert len(created) == 1
