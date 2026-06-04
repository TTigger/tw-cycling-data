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
    assert bv.avg_speed_kmh(100, 3600) == 100.0
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
        "age_group": "25", "finish_seconds": 7231.4, "rank_overall": 1,
        "result_label": "總排名", "source_platform": "cyclist.org.tw", "region": None,
    }
    s = bv.slim_record(rec)
    assert s["rk"] == "taipingshan"
    assert s["y"] == 2026 and s["mon"] == 5
    assert s["g"] == "M" and s["ag"] == "25"
    assert s["t"] == 7231 and s["rank"] == 1
    assert s["plat"] == "cyclist.org.tw"
    assert "name_raw" not in s and "splits" not in s
