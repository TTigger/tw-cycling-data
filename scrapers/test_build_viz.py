# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_viz as bv

def test_extract_distance_km():
    assert bv.extract_distance_km("104公里挑戰組", None, None) == 104
    assert bv.extract_distance_km("29公里經典組", None, None) == 29
    assert bv.extract_distance_km(None, "145K_總排名", None) == 145
    assert bv.extract_distance_km("80KM", None, None) == 80
    assert bv.extract_distance_km("男子菁英組", None, "2026 太平山王 45K") == 45
    assert bv.extract_distance_km("男子菁英組", "總排名", "太平山王") is None
    assert bv.extract_distance_km(None, None, None) is None

def test_avg_speed_kmh():
    assert bv.avg_speed_kmh(50, 3600) == 50.0
    assert round(bv.avg_speed_kmh(45, 7200), 1) == 22.5
    assert bv.avg_speed_kmh(None, 3600) is None
    assert bv.avg_speed_kmh(100, None) is None
    assert bv.avg_speed_kmh(100, 0) is None
    assert bv.avg_speed_kmh(100, 60) is None

def test_month_of():
    assert bv.month_of("2025-09-07 06:40:00") == 9
    assert bv.month_of("2024-11-14") == 11
    assert bv.month_of(None) is None
    assert bv.month_of("bad") is None

def test_slim_record():
    rec = {
        "race_key": "taipingshan", "race_name_canonical": "太平山王 公路賽",
        "year": 2026, "date": "2026-05-09", "series": "臺灣自行車聯賽(TCL)",
        "race_class": "競賽", "category_raw": "M25", "gender": "M",
        "age_group": "25", "age_band": "19-29", "finish_seconds": 7231.4, "rank_overall": 1,
        "result_label": "總排名", "source_platform": "cyclist.org.tw", "region": None,
    }
    s = bv.slim_record(rec)
    assert s["rk"] == "taipingshan"
    assert s["y"] == 2026 and s["mon"] == 5
    assert s["g"] == "M" and s["ag"] == "19-29"  # emits normalized band, not raw
    assert s["t"] == 7231 and s["rank"] == 1
    assert s["plat"] == "cyclist.org.tw"
    assert "name_raw" not in s and "splits" not in s

def test_build_races_index():
    records = [
        # "alpha" spans 2024 + 2025 -> multi_year True; one row carries a team.
        {"race_key": "alpha", "year": 2024, "race_name_canonical": "Alpha Race",
         "series": "TCL", "team": "Team A"},
        {"race_key": "alpha", "year": 2024, "race_name_canonical": "Alpha Race",
         "series": "TCL", "team": None},
        {"race_key": "alpha", "year": 2025, "race_name_canonical": "Alpha Race",
         "series": "TCL", "team": None},
        # "beta" single-year (2025), no team anywhere -> multi_year False, has_team False.
        {"race_key": "beta", "year": 2025, "race_name_canonical": "Beta Race",
         "series": "CTCA", "team": None},
    ]
    out = bv.build_races_index(records)

    # One entry per (race_key, year): alpha/2024, alpha/2025, beta/2025.
    keys = {(e["rk"], e["y"]) for e in out}
    assert keys == {("alpha", 2024), ("alpha", 2025), ("beta", 2025)}
    assert len(out) == 3

    by_key = {(e["rk"], e["y"]): e for e in out}

    # multi_year flag: alpha entries True (spans 2 years), beta False.
    assert by_key[("alpha", 2024)]["multi_year"] is True
    assert by_key[("alpha", 2025)]["multi_year"] is True
    assert by_key[("beta", 2025)]["multi_year"] is False

    # has_team propagates per (race_key, year): only alpha/2024 had a team row.
    assert by_key[("alpha", 2024)]["has_team"] is True
    assert by_key[("alpha", 2025)]["has_team"] is False
    assert by_key[("beta", 2025)]["has_team"] is False

    # Sorted by rows descending (alpha/2024 has 2 rows, others 1).
    assert [e["rows"] for e in out] == sorted([e["rows"] for e in out], reverse=True)
    assert out[0]["rows"] == 2 and (out[0]["rk"], out[0]["y"]) == ("alpha", 2024)

    # Entries carry rk / y / rn / s.
    for e in out:
        assert set(("rk", "y", "rn", "s")).issubset(e.keys())
    assert by_key[("alpha", 2024)]["rn"] == "Alpha Race"
    assert by_key[("beta", 2025)]["s"] == "CTCA"

    assert all("file" in e for e in out)
    assert out[0]["file"] == bv.race_file_name(out[0]["rk"], out[0]["y"])


def test_race_file_name():
    assert bv.race_file_name("taipingshan", 2026) == "taipingshan__2026"
    assert bv.race_file_name("【96】台北", 2025) == "96-台北__2025"
    assert bv.race_file_name("a/b c", 2024) == "a-b-c__2024"


def test_completion_present_for_status_races():
    import build_viz
    recs = [
        {"race_key": "苗栗繞圈賽第七屆", "year": 2026, "race_name_canonical": "苗栗繞圈賽（第七屆）",
         "series": None, "team": None, "status": "FIN", "finish_seconds": 2858},
        {"race_key": "苗栗繞圈賽第七屆", "year": 2026, "race_name_canonical": "苗栗繞圈賽（第七屆）",
         "series": None, "team": None, "status": "DNF", "finish_seconds": None},
        {"race_key": "苗栗繞圈賽第七屆", "year": 2026, "race_name_canonical": "苗栗繞圈賽（第七屆）",
         "series": None, "team": None, "status": "DNS", "finish_seconds": None},
    ]
    idx = build_viz.build_races_index(recs)
    entry = next(e for e in idx if e["rk"] == "苗栗繞圈賽第七屆")
    assert entry["completion"] == {"fin": 1, "total": 3, "rate": round(1 / 3, 3),
                                   "counts": {"FIN": 1, "DNF": 1, "DNS": 1}}


def test_completion_dq_srt_nys_count_but_not_fin():
    import build_viz
    recs = [
        {"race_key": "test_race", "year": 2026, "race_name_canonical": "Test Race",
         "series": None, "team": None, "status": "FIN", "finish_seconds": 2858},
        {"race_key": "test_race", "year": 2026, "race_name_canonical": "Test Race",
         "series": None, "team": None, "status": "DQ", "finish_seconds": None},
        {"race_key": "test_race", "year": 2026, "race_name_canonical": "Test Race",
         "series": None, "team": None, "status": "SRT", "finish_seconds": None},
        {"race_key": "test_race", "year": 2026, "race_name_canonical": "Test Race",
         "series": None, "team": None, "status": "NYS", "finish_seconds": None},
    ]
    idx = build_viz.build_races_index(recs)
    entry = next(e for e in idx if e["rk"] == "test_race")
    c = entry["completion"]
    assert c["total"] == 4          # all 4 rows count in total
    assert c["fin"] == 1            # only FIN counts as finisher
    assert c["counts"]["DQ"] == 1
    assert c["counts"]["SRT"] == 1
    assert c["counts"]["NYS"] == 1
    assert c["rate"] == round(1 / 4, 3)


def test_completion_absent_without_status():
    import build_viz
    recs = [{"race_key": "彰化經典百K", "year": 2024, "race_name_canonical": "彰化經典百K",
             "series": None, "team": None, "status": None, "finish_seconds": 3600}]
    idx = build_viz.build_races_index(recs)
    entry = next(e for e in idx if e["rk"] == "彰化經典百K")
    assert "completion" not in entry


def test_is_finisher():
    import build_viz
    assert build_viz.is_finisher({"status": "FIN"}) is True
    assert build_viz.is_finisher({"status": None}) is True
    assert build_viz.is_finisher({"status": "DNF"}) is False
    assert build_viz.is_finisher({"status": "DNS"}) is False
    assert build_viz.is_finisher({"status": "DQ"}) is False
    assert build_viz.is_finisher({"status": "SRT"}) is False
    assert build_viz.is_finisher({"status": "NYS"}) is False


def test_rows_equals_finisher_count_not_status_total():
    """rows must equal the finisher count (FIN + no-status), NOT the all-status total.
    This invariant keeps races.json consistent with the leaderboard file row count
    and prevents ResultConverter from dividing percentile by an inflated denominator."""
    import build_viz
    recs = [
        {"race_key": "criterium_test", "year": 2026, "race_name_canonical": "Criterium Test",
         "series": None, "team": None, "status": "FIN", "finish_seconds": 2000},
        {"race_key": "criterium_test", "year": 2026, "race_name_canonical": "Criterium Test",
         "series": None, "team": None, "status": "DNF", "finish_seconds": None},
        {"race_key": "criterium_test", "year": 2026, "race_name_canonical": "Criterium Test",
         "series": None, "team": None, "status": "DNS", "finish_seconds": None},
    ]
    idx = build_viz.build_races_index(recs)
    entry = next(e for e in idx if e["rk"] == "criterium_test")
    # rows counts only the FIN finisher, not DNF/DNS
    assert entry["rows"] == 1
    # completion.total still captures all 3 status rows
    assert entry["completion"]["total"] == 3
    assert entry["completion"]["fin"] == 1
