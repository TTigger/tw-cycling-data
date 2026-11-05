# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import focusline_crawl as fc

META = {"category": "雙塔", "year": 2025, "date": "2025-11-14",
        "url": "https://score.focusline.com.tw/api/Member/focusline?code=51114JR&categoryName=100102"}
ROWS = [
    {"name": "林玉清", "number": "H75532", "gender": "", "category": "雙塔",
     "group": "M50", "gunTime": "17:39:10", "totalSort": "1"},
    {"name": "陳美玲", "number": "W1234", "gender": "女", "category": "雙塔",
     "group": "W40", "gunTime": "20:05:00", "totalSort": "5"},
    {"name": "張弘瑜", "number": "D42012", "gender": "", "category": "雙塔",
     "group": "M30", "gunTime": "00:00:07", "totalSort": "291"},  # placeholder -> dropped
]


def test_gender_of_falls_back_to_group():
    assert fc.gender_of({"gender": "", "group": "M50"}) == "M"
    assert fc.gender_of({"gender": "女", "group": "W40"}) == "F"
    assert fc.gender_of({"gender": "", "group": "W40"}) == "F"
    assert fc.gender_of({"gender": "", "group": "?"}) is None


def test_build_records_maps_and_filters_placeholder():
    recs = fc.build_records(ROWS, META, "2026-06-29T00:00:00Z")
    assert len(recs) == 2  # placeholder (00:00:07) dropped
    r = recs[0]
    assert r["source_platform"] == "twbike.org"
    assert r["race_name_raw"] == "雙塔 2025"
    assert r["year"] == 2025 and r["date"] == "2025-11-14"
    assert r["result_label"] == "雙塔"
    assert r["category_raw"] == "M50"
    assert r["gender"] == "M"
    assert r["bib"] == "H75532"
    assert r["finish_time"] == "17:39:10"
    assert r["finish_seconds"] == 17 * 3600 + 39 * 60 + 10
    assert r["rank_overall"] is None and r["team"] is None
    assert r["name_masked"] == "林○清" and "name_raw" in r
    assert recs[1]["gender"] == "F"  # 陳美玲 from gender field


def test_challenge_keeps_rank_and_race_name():
    meta = {"category": "72KM挑戰組", "year": 2026, "date": "2026-02-01", "url": "u",
            "race": "梅山36彎自行車挑戰賽", "region": "嘉義縣"}
    rows = [{"name": "王小明", "number": "1801", "gender": "", "group": "男子組",
             "gunTime": "02:21:08", "totalSort": "1"}]
    r = fc.build_records(rows, meta, "d")[0]
    assert r["source_platform"] == "focusline.com.tw"
    assert r["race_key"] == "梅山36彎自行車挑戰賽" and r["year"] == 2026
    assert r["rank_overall"] == 1 and r["region"] == "嘉義縣"
    assert r["result_label"] == "72KM挑戰組"


def test_skip_leisure_and_relay():
    assert fc.SKIP_CATEGORY.search("50K 休閒組")
    assert fc.SKIP_CATEGORY.search("團體接力組-東三塔550")
    assert not fc.SKIP_CATEGORY.search("103K 挑戰組")
