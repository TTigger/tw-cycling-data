# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import criterium_crawl as cc

META = {"name": "苗栗繞圈賽（第七屆）", "date": "2026-06-28",
        "year": 2026, "region": "苗栗", "event_ids": [4]}
ROWS = [
    {"rank": 1, "bib": "2", "name": "馮俊凱", "category": "M / M30",
     "team": "宇都宮車隊", "finish_time": "00:47:38", "laps": 35, "status": "FIN"},
    {"rank": None, "bib": "21", "name": "洪稟詠", "category": "M / U23",
     "team": "TEAM CYTO TRIGON", "finish_time": None, "laps": 25, "status": "DNF"},
    {"rank": None, "bib": "99", "name": "王小明", "category": "M / M35",
     "team": "Solo", "finish_time": None, "laps": 0, "status": "DNS"},
]


def test_build_records_fin():
    recs = cc.build_records(ROWS, META, "男子A組",
                            "https://events.criterium.tw/races/19554/events/4",
                            "2026-06-29T00:00:00")
    fin = recs[0]
    assert fin["source_platform"] == "criterium.tw"
    assert fin["race_name_raw"] == "苗栗繞圈賽（第七屆）"
    assert fin["year"] == 2026 and fin["date"] == "2026-06-28"
    assert fin["region"] == "苗栗"
    assert fin["result_label"] == "男子A組"
    assert fin["category_raw"] == "M / M30"
    assert fin["gender"] == "M" and fin["age_group"] == "30"
    assert fin["rank_overall"] == 1 and fin["bib"] == "2"
    assert fin["status"] == "FIN" and fin["laps"] == 35
    assert fin["finish_seconds"] == 47 * 60 + 38
    assert fin["name_masked"] == "馮○凱" and "name_raw" in fin


def test_build_records_dnf_has_no_time():
    recs = cc.build_records(ROWS, META, "男子A組", "u", "t")
    dnf = recs[1]
    assert dnf["status"] == "DNF"
    assert dnf["finish_time"] is None and dnf["finish_seconds"] is None
    assert dnf["laps"] == 25


def test_build_records_dns():
    recs = cc.build_records(ROWS, META, "男子A組", "u", "t")
    dns = recs[2]
    assert dns["status"] == "DNS"
    assert dns["finish_time"] is None and dns["finish_seconds"] is None
    assert dns["rank_overall"] is None
    assert dns["bib"] == "99"
    assert dns["laps"] == 0
