import csv
import gzip
import json
import os
import build_dataset as B
import dataset as D


def _rows():
    base = {c: None for c in D.PUBLISH_COLUMNS}
    r1 = dict(base, year=2024, name_masked="李○明", finish_seconds=3600, splits=[{"k": 1}])
    r2 = dict(base, year=2025, name_masked="陳○明", finish_seconds=4000)
    # include sensitive keys to prove they are dropped
    r1["uci_id"] = "10012345678"; r1["name_raw"] = "李大明"; r1["source_url"] = "http://x"
    return [r1, r2]


def test_build_writes_assets_and_drops_sensitive(tmp_path):
    out = str(tmp_path)
    summary = B.build(_rows(), out, "2026.06.30")

    assert summary["count"] == 2
    # csv.gz header == PUBLISH_COLUMNS, no sensitive columns
    with gzip.open(os.path.join(out, "tw-cycling-results.csv.gz"), "rt", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == D.PUBLISH_COLUMNS
    for c in D.DROP_COLUMNS:
        assert c not in header

    # datapackage: count + per-file sha256/bytes present, license CC-BY-4.0
    dp = json.load(open(os.path.join(out, "datapackage.json"), encoding="utf-8"))
    assert dp["count"] == 2
    assert dp["licenses"][0]["name"] == "CC-BY-4.0"
    assert dp["version"] == "2026.06.30"
    names = {r["path"] for r in dp["resources"]}
    assert "tw-cycling-results.csv.gz" in names and "tw-cycling-results.json.gz" in names
    for r in dp["resources"]:
        assert len(r["hash"]) == 64 and r["bytes"] > 0      # sha256 hex
    # schema fields cover every published column
    fields = {fld["name"] for fld in dp["resources"][0]["schema"]["fields"]}
    assert fields == set(D.PUBLISH_COLUMNS)

    # CHECKSUMS.txt lists both gz files
    chk = open(os.path.join(out, "CHECKSUMS.txt"), encoding="utf-8").read()
    assert "tw-cycling-results.csv.gz" in chk and "tw-cycling-results.json.gz" in chk

    # json.gz round-trips and contains no sensitive keys
    with gzip.open(os.path.join(out, "tw-cycling-results.json.gz"), "rt", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2 and "uci_id" not in data[0] and "name_raw" not in data[0]
