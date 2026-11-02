# -*- coding: utf-8 -*-
import datetime as dt

import discover as d


def _li(s):
    return f"<li>{s}</li>"


def test_raceon_dated_decodes_entities_and_wraps_year():
    page = "".join([
        _li("10.3｜L&rsquo;&Eacute;tape環法自行車挑戰賽：103K／報名連結"),
        _li("12.20｜石門羅馬百K自行車挑戰賽：72K／報名連結"),
        _li("1.1-1.2｜2027瘋系列超級騎士挑戰賽：300K／報名連結"),
    ])
    got = d.parse_raceon_dated(page, 2026)
    assert got[0] == ("L’Étape環法自行車挑戰賽", dt.date(2026, 10, 3))
    assert got[1][1] == dt.date(2026, 12, 20)
    assert got[2][1] == dt.date(2027, 1, 1)  # month went backwards → next year


def test_years_known_uses_best_match_not_any_match():
    by_year = {d.core("96聯賽武嶺站"): {2025}, d.core("苗栗繞圈賽"): {2026}}
    # loose any-match would union {2025, 2026} and hide the missing 2026 stop
    assert d.years_known(d.core("96聯賽苗栗站 仙山自行車登山賽"), by_year) == {2025}


def test_not_ingested_only_for_held_races_with_earlier_editions():
    by_year = {d.core("花蓮太平洋盃公路賽"): {2024, 2025}}
    today = dt.date(2026, 11, 2)
    rec = d.not_ingested("花蓮太平洋盃公路賽", dt.date(2026, 10, 30), today, by_year)
    assert rec["status"] == "NOT_INGESTED" and rec["date"] == "2026-10-30"
    assert d.not_ingested("花蓮太平洋盃公路賽", dt.date(2026, 12, 4), today, by_year) is None  # future
    assert d.not_ingested("全新賽事", dt.date(2026, 10, 1), today, by_year) is None  # never seen
    by_year[d.core("花蓮太平洋盃公路賽")].add(2026)
    assert d.not_ingested("花蓮太平洋盃公路賽", dt.date(2026, 10, 30), today, by_year) is None


def test_carry_forward_keeps_failed_calendar_gaps_and_retriages():
    prev = [
        {"race": "輪霸西濱挑戰", "calendar": "ensage2026", "guess_source": "x"},
        {"race": "陽明山登山王", "calendar": "ensage2026", "guess_source": "x"},  # COLLECTED
        {"race": "別的賽事", "calendar": "raceon2026", "guess_source": "x"},
    ]
    kept = d.carry_forward(prev, "ensage2026")
    assert [g["race"] for g in kept] == ["輪霸西濱挑戰"]
    assert kept[0]["status"] == "BLOCKED" and kept[0]["stale"] is True


def test_irunner_fill_missing_years_inherits_previous_event():
    import irunner_crawl as ir
    evs = [{"track_id": 1327, "year": None}, {"track_id": 1325, "year": 2024},
           {"track_id": 1346, "year": 2024}, {"track_id": 1328, "year": None}]
    ir.fill_missing_years(evs)
    assert {e["track_id"]: e["year"] for e in evs} == {1325: 2024, 1327: 2024, 1328: 2024, 1346: 2024}
