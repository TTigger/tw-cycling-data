# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import merge


def test_keeps_dnf_dns_rows_without_time():
    assert merge.should_drop_zero_time({"status": "DNF", "finish_seconds": None}) is False
    assert merge.should_drop_zero_time({"status": "DNS", "finish_seconds": 0}) is False


def test_drops_zero_time_noise_without_status():
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": 0}) is True
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": -5}) is True


def test_keeps_normal_finisher():
    assert merge.should_drop_zero_time({"status": "FIN", "finish_seconds": 2858}) is False
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": 2858}) is False


def test_criterium_prefix_discovered():
    assert "criterium_" in merge.SOURCE_PREFIXES


def test_focusline_and_taiwanbike_prefixes_discovered():
    assert "focusline_" in merge.SOURCE_PREFIXES
    assert "taiwanbike_" in merge.SOURCE_PREFIXES


def test_superseded_set_contains_bravelog_tba_combined():
    assert ("bravelog.tw", "TBA北高360雙塔520四極602自行車認證") in merge.SUPERSEDED


def test_team_that_is_a_rider_real_name_is_masked():
    names = {"張允丞", "陳柏安"}
    assert merge.mask_person_team("張允丞", names) == "張○丞"
    assert merge.mask_person_team(" 陳柏安 ", names) == "陳○安"
    assert merge.mask_person_team("新竹市ZIV聯隊", names) == "新竹市ZIV聯隊"
    assert merge.mask_person_team(None, names) is None
    # a name inside a longer team string is masked in place
    assert merge.mask_person_team("張允丞&陳柏安親友團", names) == "張○丞&陳○安親友團"
    assert merge.mask_person_team("狂抽猛送張允丞", names) == "狂抽猛送張○丞"


def test_sporter96_prefix_discovered():
    assert "sporter96_" in merge.SOURCE_PREFIXES
