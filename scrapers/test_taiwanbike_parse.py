# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import taiwanbike_parse as tp

LISTING = (
    '<a href="https://docs.google.com/spreadsheets/d/1-OSl9p_AAA/edit?usp=sharing">'
    '2025雙塔520自行車認證</a>'
    '<a href="https://drive.google.com/file/d/9zzz/view">2019雙塔520</a>'  # not a sheet -> skip
    '<a href="https://docs.google.com/spreadsheets/d/1-BBB/edit">2026環大苗栗107K</a>'
    '<a href="https://docs.google.com/spreadsheets/d/1-CCC/edit">2018北高360</a>'  # <2022 -> skip
    '<a href="https://docs.google.com/spreadsheets/d/1-DDD/edit">2030環台</a>'
)

# 雙塔520 (duplicate 組別 header: event-name col + age-group col)
H1 = ["參加編號", "姓名", "隊名", "組別", "性別", "組別", "起點時間", "終點時間", "成績"]
R1 = ["6000", "蔡正一", "騎就對了", "2025TBA雙塔520自行車認證", "男", "M25",
      "2025-11-08 00:01:25", "2025-11-08 22:05:15", "22:03:49"]

# 環大苗栗 (has 名次 + chip time; different schema)
H2 = ["名次", "選手編號", "姓名", "組別", "分組排名", "性別排名", "大會成績", "晶片成績"]
R2 = ["1", "A12", "王大明", "M30", "1", "1", "03:10:00", "03:09:55"]

# row with no finish time -> skipped
H3 = ["參加編號", "姓名", "成績"]
R3 = ["7", "李四", ""]


def test_extract_sheet_links_filters_to_2022plus_sheets():
    links = tp.extract_sheet_links(LISTING)
    assert [(l["year"], l["sheet_id"]) for l in links] == [(2025, "1-OSl9p_AAA"), (2026, "1-BBB"), (2030, "1-DDD")]


def test_map_row_dual_group_picks_age_code_and_chip_time():
    m = tp.map_row(H1, R1)
    assert m["bib"] == "6000"
    assert m["name"] == "蔡正一"
    assert m["team"] == "騎就對了"
    assert m["category"] == "M25"        # the age-group code, not the event name
    assert m["gender"] == "M"
    assert m["finish_time"] == "22:03:49"


def test_map_row_prefers_chip_time_and_ignores_rank():
    m = tp.map_row(H2, R2)
    assert m["bib"] == "A12" and m["name"] == "王大明"
    assert m["category"] == "M30" and m["gender"] == "M"
    assert m["finish_time"] == "03:09:55"   # 晶片成績 preferred over 大會成績


def test_map_row_without_finish_time_is_none():
    assert tp.map_row(H3, R3) is None


import taiwanbike_crawl as tc

def test_records_from_sheet_maps_and_masks():
    tabs = {"雙塔520選手總表": [
        ["參加編號", "姓名", "隊名", "組別", "性別", "組別", "成績"],
        ["6000", "蔡正一", "騎就對了", "2025TBA雙塔520", "男", "M25", "22:03:49"],
        ["7", "李四", "", "x", "男", "M30", ""],          # no time -> dropped
        ["8", "陳一", "隊B", "y", "男", "M40", "00:00:30"],  # placeholder <1h -> dropped
    ]}
    recs = tc.records_from_sheet(tabs, "2025雙塔520自行車認證", 2025, "2026-06-29T00:00:00Z")
    assert len(recs) == 1
    r = recs[0]
    assert r["source_platform"] == "taiwanbike.org"
    assert r["race_name_raw"] == "雙塔520自行車認證 2025"  # year stripped from title
    assert r["team"] == "騎就對了" and r["category_raw"] == "M25"
    assert r["rank_overall"] is None
    assert r["finish_seconds"] == 22 * 3600 + 3 * 60 + 49
    assert r["name_masked"] == "蔡○一"
