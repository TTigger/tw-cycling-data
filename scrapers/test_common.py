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
