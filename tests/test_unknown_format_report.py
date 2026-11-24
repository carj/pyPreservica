import csv
import json

import pytest
from pyPreservica import *

P = RepresentationType.Preservation
A = RepresentationType.Access


def fmt(puid, method, name="Format", priority="1"):
    return {"Valid": "true", "PUID": puid, "Priority": priority, "IdentificationMethod": method,
            "FormatName": name, "FormatVersion": None}


TIFF = fmt("fmt/353", "Signature", "Tagged Image File Format")


class FakeClient:
    """ Offline stand-in for EntityAPI with generations which have format candidates """

    server = "example.preservica.com"
    protocol = "https"
    tenant = "EXAMPLE"

    # parent reference -> list of (reference, title, type)
    TREE = {
        None: [("f1", "Research", "F"), ("f3", "Text", "F"), ("a9", "access copy", "A"), ("a10", "broken", "A")],
        "f1": [("a2", "survey", "A"), ("a3", "readme", "A"), ("f2", "Raw", "F")],
        "f2": [("a1", "scan", "A"), ("a8", "migrated", "A")],
        "f3": [("a4", "notes", "A"), ("a5", "minutes", "A"), ("a6", "letter", "A"), ("a7", "shout", "A"),
               ("a11", "manual", "A")],
    }

    # asset reference -> list of (representation type, filename, size, formats, original, active)
    GENERATIONS = {
        "a1": [(P, "scan.tif", 5000, [TIFF], True, True)],
        "a2": [(P, "survey.DAT", 4000, [], True, True)],
        "a3": [(P, "README", 10, [fmt("", "Unknown", None)], True, True)],
        "a4": [(P, "notes.txt", 300, [fmt("x-fmt/111", "Extension", "Plain Text File")], True, True)],
        "a5": [(P, "minutes.wpd", 200, [fmt("x-fmt/394", "Extension", "WordPerfect", "1"),
                                        fmt("x-fmt/203", "Extension", "WordPerfect", "2")], True, True)],
        # one candidate from the extension and one from the content, so the format is known
        "a6": [(P, "letter.doc", 100, [fmt("fmt/40", "Extension"), fmt("fmt/40", "Signature")], True, True)],
        "a7": [(P, "shout.TXT", 50, [fmt("x-fmt/111", "EXTENSION", "Plain Text File")], True, True)],
        # the original generation is identified but no longer active, the migrated one is not identified
        "a8": [(P, "old.tif", 7000, [TIFF], True, False), (P, "new.xyz", 6000, [], False, True)],
        "a9": [(A, "access.bin", 900, [], True, True)],
        # a PUID with no identification method, e.g. set manually, counts as known
        "a11": [(P, "manual.abc", 70, [fmt("fmt/999", "None")], True, True)],
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
        if asset.reference == "a10":
            raise HTTPException(asset.reference, 500, "", "representations", "server error")
        rep_types = {g[0] for g in self.GENERATIONS.get(asset.reference, [])}
        return {Representation(asset, t, t.value, f"{asset.reference}/{t.value}") for t in rep_types}

    def content_objects(self, representation):
        co = ContentObject(f"co-{representation.asset.reference}", "co")
        co.items = [g for g in self.GENERATIONS[representation.asset.reference] if g[0] == representation.rep_type]
        return [co]

    def generations(self, content_object):
        result = []
        for i, (_, name, size, formats, original, active) in enumerate(content_object.items):
            generation = Generation(original, active, "", "", [Bitstream(name, size, {}, f"{content_object.reference}/{i}")])
            generation.formats = formats
            result.append(generation)
        return result


def by_name(files):
    return {f.filename: f for f in files}


def test_classify():
    assert UnknownFormatFile.classify(None) == UnknownFormatFile.NO_PUID
    assert UnknownFormatFile.classify([]) == UnknownFormatFile.NO_PUID
    assert UnknownFormatFile.classify([fmt(None, "Unknown")]) == UnknownFormatFile.NO_PUID
    assert UnknownFormatFile.classify([fmt("  ", "Extension")]) == UnknownFormatFile.NO_PUID
    assert UnknownFormatFile.classify([fmt("x-fmt/111", "Extension")]) == UnknownFormatFile.EXTENSION_ONLY
    assert UnknownFormatFile.classify([fmt("x-fmt/111", "extension")]) == UnknownFormatFile.EXTENSION_ONLY
    assert UnknownFormatFile.classify([fmt("fmt/40", "Extension"), fmt("fmt/40", "Signature")]) is None
    assert UnknownFormatFile.classify([fmt("fmt/189", "Container")]) is None
    assert UnknownFormatFile.classify([fmt("fmt/999", "None")]) is None
    # a candidate without a PUID does not make an extension match into a content match
    assert UnknownFormatFile.classify([fmt("x-fmt/111", "Extension"), fmt("", "Signature")]) == \
        UnknownFormatFile.EXTENSION_ONLY


def test_scan_repository():
    report = UnknownFormatReport(FakeClient(), show_progress=False)
    files = by_name(report.scan())
    assert set(files) == {"survey.DAT", "README", "notes.txt", "minutes.wpd", "shout.TXT", "new.xyz"}

    assert files["survey.DAT"].status == UnknownFormatFile.NO_PUID
    assert files["survey.DAT"].extension == ".dat"
    assert files["survey.DAT"].folder_path == "Research"
    assert files["README"].status == UnknownFormatFile.NO_PUID
    assert files["README"].extension == ""
    assert files["notes.txt"].status == UnknownFormatFile.EXTENSION_ONLY
    assert files["notes.txt"].formats[0]["puid"] == "x-fmt/111"
    assert files["minutes.wpd"].status == UnknownFormatFile.EXTENSION_ONLY
    assert files["shout.TXT"].status == UnknownFormatFile.EXTENSION_ONLY

    migrated = files["new.xyz"]
    assert migrated.original is False
    assert migrated.folder_path == "Research / Raw"
    assert migrated.representation == "Preservation"

    # no PUID files first, largest first
    assert [f.filename for f in report.files[:3]] == ["new.xyz", "survey.DAT", "README"]


def test_totals():
    report = UnknownFormatReport(FakeClient(), show_progress=False)
    report.scan()
    assert report.assets_scanned == 11
    assert report.assets_failed == 1
    # a1, a2, a3, a4, a5, a6, a7, the active a8 generation and a11; a9 is an access copy
    assert report.files_scanned == 9
    assert report.bytes_scanned == 5000 + 4000 + 10 + 300 + 200 + 100 + 50 + 6000 + 70
    summary = report.summary()
    assert summary["no_puid"] == 3 and summary["no_puid_bytes"] == 10010
    assert summary["extension_only"] == 3 and summary["extension_only_bytes"] == 550
    assert len(report.no_puid_files) == 3
    assert len(report.extension_only_files) == 3


def test_exclude_extension_only():
    report = UnknownFormatReport(FakeClient(), include_extension_only=False, max_workers=1, show_progress=False)
    files = report.scan()
    assert {f.filename for f in files} == {"survey.DAT", "README", "new.xyz"}
    assert report.extension_only_files == []
    # still counted, so the page can say how many were left out
    assert report.summary()["extension_only"] == 3


def test_access_representations():
    report = UnknownFormatReport(FakeClient(), representation_types=[P, A], show_progress=False)
    files = by_name(report.scan())
    assert files["access.bin"].representation == "Access"


def test_scan_folder():
    report = UnknownFormatReport(FakeClient(), show_progress=False)
    files = report.scan("f2")
    assert report.scope == "Raw"
    assert [f.filename for f in files] == ["new.xyz"]
    assert files[0].path == []


def test_groupings():
    report = UnknownFormatReport(FakeClient(), show_progress=False)
    report.scan()
    extensions = {g["extension"]: g for g in report.by_extension()}
    assert extensions[".txt"]["files"] == 2 and extensions[".txt"]["extension_only"] == 2
    assert extensions[".txt"]["no_puid"] == 0
    assert extensions[".dat"]["no_puid"] == 1
    assert extensions[""]["example"] == "README"
    assert report.by_extension()[0]["extension"] == ".txt"

    folders = {g["folder"]: g for g in report.by_folder()}
    assert folders["Text"]["files"] == 3 and folders["Text"]["size"] == 550
    assert folders["Research"]["no_puid"] == 2
    assert folders["Research / Raw"]["folders"] == 1


def test_csv_json_and_html(tmp_path):
    report = UnknownFormatReport(FakeClient(), show_progress=False)
    report.scan()

    with open(report.save_csv(str(tmp_path / "unknown.csv")), encoding="utf-8", newline="") as fd:
        rows = {r["filename"]: r for r in csv.DictReader(fd)}
    assert len(rows) == 6
    assert rows["new.xyz"]["status"] == "No PUID"
    assert rows["new.xyz"]["generation"] == "Migrated"
    assert rows["new.xyz"]["folder_path"] == "Research / Raw"
    assert rows["minutes.wpd"]["status"] == "Extension only"
    assert rows["minutes.wpd"]["formats"] == "x-fmt/394 WordPerfect (Extension); x-fmt/203 WordPerfect (Extension)"
    assert rows["survey.DAT"]["extension"] == ".dat"
    assert rows["survey.DAT"]["formats"] == ""

    reloaded = UnknownFormatReport(None, show_progress=False)
    reloaded.load_json(report.save_json(str(tmp_path / "unknown.json")))
    assert [f.filename for f in reloaded.files] == [f.filename for f in report.files]
    assert reloaded.summary() == report.summary()
    assert reloaded.tenant == "EXAMPLE"
    assert reloaded.scope == "Repository"

    page = open(reloaded.render_html(str(tmp_path / "unknown.html")), encoding="utf-8").read()
    start = page.index("const DATA = ") + len("const DATA = ")
    data = json.loads(page[start:page.index(";\n", start)])
    assert data["summary"]["no_puid"] == 3
    assert data["server"] == "example.preservica.com"
    assert len(data["files"]) == 6
    assert {f["ext"] for f in data["files"]} == {".dat", "", ".txt", ".wpd", ".xyz"}


def test_no_scan_raises():
    with pytest.raises(RuntimeError):
        UnknownFormatReport(FakeClient(), show_progress=False).render_html("x.html")


def test_reporting_api_unknown_format_report(monkeypatch, tmp_path):
    import pyPreservica.reportingAPI as reporting

    def fake_auth_init(self, username=None, password=None, tenant=None, server=None, use_shared_secret=False,
                       two_fa_secret_key=None, protocol="https", request_hook=None, credentials_path=None):
        self.username, self.password, self.tenant, self.server = username, password, tenant, server
        self.shared_secret, self.two_fa_secret_key, self.protocol = use_shared_secret, two_fa_secret_key, protocol

    monkeypatch.setattr(AuthenticatedAPI, "__init__", fake_auth_init)
    monkeypatch.setattr(reporting, "EntityAPI", lambda **kwargs: FakeClient())

    api = ReportingAPI(username="user", password="pass", tenant="EXAMPLE", server="example.preservica.com")
    html_file = tmp_path / "unknown.html"
    report = api.unknown_format_report(filename=str(html_file), include_extension_only=False, show_progress=False)
    assert len(report.files) == 3
    assert html_file.exists()
