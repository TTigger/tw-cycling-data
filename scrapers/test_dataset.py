import os

import dataset as D

_ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_publish_columns_match_fields_and_count_20():
    assert D.PUBLISH_COLUMNS == [f[0] for f in D.FIELDS]
    assert len(D.PUBLISH_COLUMNS) == 20


def test_project_row_keeps_only_publish_columns():
    raw = {c: f"v_{c}" for c in D.PUBLISH_COLUMNS}
    # add every dropped/sensitive column with a sentinel value
    for c in D.DROP_COLUMNS:
        raw[c] = "SENSITIVE"
    raw["name_raw"] = "王大明"   # must never appear
    raw["future_unknown_col"] = "LEAK"  # unknown to BOTH lists: whitelist must block it
    out = D.project_row(raw)
    assert list(out.keys()) == D.PUBLISH_COLUMNS          # exact set + order
    for c in D.DROP_COLUMNS + ["name_raw", "future_unknown_col"]:
        assert c not in out                               # safety gate
    assert "SENSITIVE" not in out.values() and "LEAK" not in out.values()


def test_drop_columns_cover_the_reidentifiers():
    for c in ("uci_id", "tsu_rider_id", "source_url", "bib", "nationality",
              "name_raw", "scraped_at", "source_format", "race_name_raw"):
        assert c in D.DROP_COLUMNS


def test_project_row_fills_missing_with_none():
    out = D.project_row({"year": 2024})
    assert out["year"] == 2024 and out["name_masked"] is None


def test_csv_value_handles_list_and_none():
    assert D.csv_value(None) == ""
    assert D.csv_value(123) == "123"
    assert D.csv_value([{"k": 10}]) == '[{"k": 10}]'      # JSON, ensure_ascii off


def test_dataset_docs_list_every_column_and_license():
    for fn in ("DATASET.md", "DATASET.en.md"):
        text = open(os.path.join(_ROOT, fn), encoding="utf-8").read()
        for c in D.PUBLISH_COLUMNS:
            assert f"`{c}`" in text, f"{fn} missing backticked column `{c}`"
        assert "CC BY 4.0" in text or "CC-BY-4.0" in text
        assert "issues" in text


def test_citation_cff_has_license_and_type_dataset():
    cff = open(os.path.join(_ROOT, "CITATION.cff"), encoding="utf-8").read()
    assert "cff-version" in cff and "CC-BY-4.0" in cff and "dataset" in cff
