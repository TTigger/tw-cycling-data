# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import common


def test_make_record_defaults_status_and_laps_to_none():
    r = common.make_record(race_name_raw="苗栗繞圈賽（第七屆）", year=2026)
    assert r["status"] is None
    assert r["laps"] is None


def test_make_record_carries_status_and_laps():
    r = common.make_record(race_name_raw="苗栗繞圈賽（第七屆）", year=2026,
                           name_raw="洪稟詠", status="DNF", laps=25)
    assert r["status"] == "DNF"
    assert r["laps"] == 25
    assert r["finish_seconds"] is None  # DNF has no time


def test_public_data_dir_points_at_v1():
    # 必須指向 web/public/data/v1(版本化命名空間)
    parts = os.path.normpath(common.PUBLIC_DATA_DIR).split(os.sep)
    assert parts[-3:] == ["public", "data", "v1"], parts
    # 必須以 scrapers/ 為基準回推到 repo 的 web/ 底下
    assert "web" in parts


def test_mask_name_cjk_unchanged():
    assert common.mask_name("李大明") == "李○明"
    assert common.mask_name("王明") == "王○"
    assert common.mask_name("歐陽菲菲") == "歐○○菲"


def test_mask_name_romanized_hides_given_keeps_surname():
    assert common.mask_name("Alex Dupont") == "A○ Dupont"
    assert common.mask_name("Alex Marie Dupont") == "A○ M○ Dupont"
    assert common.mask_name("ABBY ROBERTS") == "A○ ROBERTS"
    assert common.mask_name("Alex") == "A○"


def test_mask_name_junk_becomes_empty():
    assert common.mask_name("<span c.") == ""
    assert common.mask_name("Gilles <.") == ""
    assert common.mask_name("Robert>") == ""   # '>' guard, symmetric with '<'
    assert common.mask_name("1.") == ""


def test_mask_name_empty_and_none_unchanged():
    assert common.mask_name("") == ""
    assert common.mask_name(None) is None
