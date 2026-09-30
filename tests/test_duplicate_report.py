import csv
import json

import pytest
from pyPreservica import *

P = RepresentationType.Preservation
A = RepresentationType.Access


class FakeClient:
    """ Offline stand-in for EntityAPI with bitstreams which have fixity values """

    server = "example.preservica.com"
    protocol = "https"
    tenant = "EXAMPLE"

    # parent reference -> list of (reference, title, type)
    TREE = {
        None: [("f1", "Photos", "F"), ("f2", "Documents", "F"), ("a9", "loose.txt", "A")],
        "f1": [("a1", "beach", "A"), ("f3", "2024", "F")],
        "f3": [("a2", "beach copy", "A"), ("a3", "album", "A")],
        "f2": [("a4", "report", "A"), ("a5", "report copy", "A"), ("a6", "empty 1", "A"), ("a7", "empty 2", "A"),
               ("a8", "broken", "A")],
    }

    # asset reference -> list of (representation type, filename, size, fixity)
    BITSTREAMS = {
        # same content in two different folders
        "a1": [(P, "beach.tif", 1000, {"SHA1": "AAA"}), (A, "beach.jpg", 100, {"SHA1": "JPG"})],
        "a2": [(P, "beach-copy.tif", 1000, {"SHA-1": "aaa"}), (A, "beach.jpg", 100, {"SHA1": "JPG"})],
        # the same file twice inside one asset, plus a file with the same fixity but a different size
        "a3": [(P, "p1.tif", 500, {"SHA256": "BBB"}), (P, "p1-again.tif", 500, {"SHA256": "BBB"}),
               (P, "odd.tif", 999, {"SHA1": "AAA"})],
        # matched through the algorithm they have in common
        "a4": [(P, "report.pdf", 50, {"SHA256": "CCC", "SHA1": "DDD"})],
        "a5": [(P, "report.pdf", 50, {"SHA1": "DDD"}), (P, "notes.txt", 10, {})],
        # empty files
        "a6": [(P, "empty.txt", 0, {"SHA1": "EMPTY"})],
        "a7": [(P, "empty.txt", 0, {"SHA1": "EMPTY"})],
        "a9": [(P, "loose.txt", 7, {"MD5": "LOOSE"})],
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
        if asset.reference == "a8":
            raise HTTPException(asset.reference, 500, "", "representations", "server error")
        rep_types = {b[0] for b in self.BITSTREAMS.get(asset.reference, [])}
        return {Representation(asset, t, t.value, f"{asset.reference}/{t.value}") for t in rep_types}

    def content_objects(self, representation):
        co = ContentObject(representation.url, "co")
        co.items = [b for b in self.BITSTREAMS[representation.asset.reference] if b[0] == representation.rep_type]
        return [co]

    def generations(self, content_object):
        bitstreams = [Bitstream(name, size, fixity, f"{content_object.reference}/{i}")
                      for i, (_, name, size, fixity) in enumerate(content_object.items)]
        return [Generation(True, True, "", "", bitstreams)]


def groups_by_first_filename(groups):
    return {sorted(f.filename for f in g.files)[0]: g for g in groups}


def test_find_duplicates_in_repository():
    report = DuplicateContentReport(FakeClient(), show_progress=False)
    groups = report.scan()
    found = groups_by_first_filename(groups)
    assert set(found) == {"beach-copy.tif", "p1-again.tif", "report.pdf"}

    beach = found["beach-copy.tif"]
    assert beach.copies == 2
    assert beach.asset_count == 2
    assert beach.reclaimable == 1000
    assert beach.algorithm == "SHA1" and beach.fixity == "aaa"
    assert {f.folder_path for f in beach.files} == {"Photos", "Photos / 2024"}

    album = found["p1-again.tif"]
    assert album.asset_count == 1

    # a4 has SHA256 and SHA1, a5 only SHA1, so they match on SHA1
    report_pdf = found["report.pdf"]
    assert report_pdf.algorithm == "SHA1" and report_pdf.fixity == "ddd"

    # largest reclaimable space first
    assert groups[0] is beach


def test_totals():
    report = DuplicateContentReport(FakeClient(), show_progress=False)
    report.scan()
    assert report.assets_scanned == 9
    assert report.assets_failed == 1
    assert report.files_scanned == 11
    assert report.files_without_fixity == 1
    assert report.duplicate_files == 3
    assert report.reclaimable == 1000 + 500 + 50
    assert report.largest(1)[0].reclaimable == 1000


def test_empty_files_included_when_min_size_zero():
    report = DuplicateContentReport(FakeClient(), min_size=0, show_progress=False)
    found = groups_by_first_filename(report.scan())
    assert found["empty.txt"].copies == 2
    assert found["empty.txt"].reclaimable == 0


def test_access_representations():
    report = DuplicateContentReport(FakeClient(), representation_types=[P, A], show_progress=False)
    found = groups_by_first_filename(report.scan())
    assert found["beach.jpg"].copies == 2


def test_scan_folder():
    report = DuplicateContentReport(FakeClient(), max_workers=1, show_progress=False)
    groups = report.scan("f3")
    assert report.scope == "2024"
    assert [g.files[0].filename for g in groups] == ["p1.tif"]
    assert groups[0].files[0].path == []


def test_csv_json_and_html(tmp_path):
    report = DuplicateContentReport(FakeClient(), show_progress=False)
    report.scan()

    with open(report.save_csv(str(tmp_path / "dups.csv")), encoding="utf-8", newline="") as fd:
        rows = list(csv.DictReader(fd))
    assert len(rows) == 6
    assert {r["group"] for r in rows} == {"1", "2", "3"}
    assert rows[0]["reclaimable"] == "1000"

    reloaded = DuplicateContentReport(None, show_progress=False)
    reloaded.load_json(report.save_json(str(tmp_path / "dups.json")))
    assert reloaded.reclaimable == report.reclaimable
    assert reloaded.files_scanned == report.files_scanned
    assert reloaded.tenant == "EXAMPLE"
    assert reloaded.scope == "Repository"
    assert [g.fixity for g in reloaded.groups] == [g.fixity for g in report.groups]

    page = open(reloaded.render_html(str(tmp_path / "dups.html")), encoding="utf-8").read()
    start = page.index("const DATA = ") + len("const DATA = ")
    data = json.loads(page[start:page.index(";\n", start)])
    assert data["summary"]["reclaimable"] == 1550
    assert data["server"] == "example.preservica.com"
    assert len(data["groups"]) == 3


def test_no_scan_raises():
    with pytest.raises(RuntimeError):
        DuplicateContentReport(FakeClient(), show_progress=False).render_html("x.html")


def test_reporting_api_duplicate_content_report(monkeypatch, tmp_path):
    import pyPreservica.reportingAPI as reporting

    def fake_auth_init(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False,
                       two_fa_secret_key=None, protocol="https", request_hook=None, credentials_path=None):
        self.username, self.password, self.tenant, self.server = username, password, tenant, server
        self.shared_secret, self.two_fa_secret_key, self.protocol = use_shared_secret, two_fa_secret_key, protocol

    monkeypatch.setattr(AuthenticatedAPI, "__init__", fake_auth_init)
    monkeypatch.setattr(reporting, "EntityAPI", lambda **kwargs: FakeClient())

    api = ReportingAPI(username="user", password="pass", tenant="EXAMPLE", server="example.preservica.com")
    html_file = tmp_path / "dups.html"
    report = api.duplicate_content_report(filename=str(html_file), show_progress=False)
    assert report.reclaimable == 1550
    assert html_file.exists()
