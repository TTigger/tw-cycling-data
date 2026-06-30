import json
import os
import build_manifest


def _write(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def test_compute_manifest_derives_stats_from_products(tmp_path):
    d = str(tmp_path)
    _write(os.path.join(d, "overview.json"),
           {"kpi": {"records": 146475, "races": 161, "series": 23,
                    "minYear": 2009, "maxYear": 2026, "sources": 8}})
    _write(os.path.join(d, "races.json"), [{"rk": "a"}, {"rk": "b"}])
    _write(os.path.join(d, "athletes.json"), [{"id": "x"}, {"id": "y"}, {"id": "z"}])
    _write(os.path.join(d, "teams.json"), [{"id": "t"}])

    m = build_manifest.compute_manifest(d)

    assert m["api_version"] == "v1"
    assert m["license"] == "CC-BY-4.0"
    # 指標由產物推導,不可寫死
    assert m["stats"]["records"] == 146475
    assert m["stats"]["sources"] == 8
    assert m["stats"]["year_min"] == 2009 and m["stats"]["year_max"] == 2026
    assert m["stats"]["races"] == 161        # distinct races (from overview kpi)
    assert m["stats"]["race_editions"] == 2  # per-year editions (len races.json)
    assert m["stats"]["athletes"] == 3       # len(athletes.json)
    assert m["stats"]["teams"] == 1          # len(teams.json)
    # 端點目錄涵蓋明細樣板路徑
    paths = {e["path"] for e in m["endpoints"]}
    assert "athlete/{athlete_id}.json" in paths
    assert "race/{race_key}.json" in paths
    assert "manifest.json" in paths
    assert "benchmarks.json" in paths
