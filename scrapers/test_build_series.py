# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_series as bs


def _rec(series, rk, year, rank, name=None, tsu=None, nm=None):
    return {"series": series, "race_key": rk, "year": year, "rank_overall": rank,
            "race_name_canonical": name or rk, "tsu_rider_id": tsu,
            "uci_id": None, "name_raw": nm, "name_masked": nm}


def test_series_standings_sums_percentile_over_stations():
    fs = {("r1", 2024): 100, ("r2", 2024): 100}
    recs = [
        _rec("S", "r1", 2024, 10, tsu="A", nm="甲"),   # pct 90
        _rec("S", "r2", 2024, 20, tsu="A", nm="甲"),   # pct 80  -> A pts 170, n2
        _rec("S", "r1", 2024, 50, tsu="B", nm="乙"),   # pct 50
        _rec("S", "r2", 2024, 60, tsu="B", nm="乙"),   # pct 40  -> B pts 90, n2
        _rec("S", "r1", 2024, 5, tsu="C", nm="丙"),    # only 1 station -> excluded
    ]
    keys = bs.build_group_keys(recs)
    out = bs.series_standings(recs, keys, field_sizes=fs, min_stations=2)
    season = out["S"]["seasons"]["2024"]
    assert [s["pts"] for s in season["standings"]] == [170, 90]   # A then B
    assert season["standings"][0]["n"] == 2
    assert {s["id"] for s in season["standings"]} == {bs.athlete_id("t:A"), bs.athlete_id("t:B")}
    assert bs.athlete_id("t:C") not in {s["id"] for s in season["standings"]}  # 1 station out
    assert len(season["stations"]) == 2
    assert season["standings"][0]["link"] is True  # A raced 2 -> trackable


def test_series_standings_drops_single_station_seasons():
    fs = {("r1", 2024): 50, ("r2", 2024): 50, ("solo", 2024): 50}
    recs = [
        _rec("Multi", "r1", 2024, 5, tsu="A", nm="甲"),
        _rec("Multi", "r2", 2024, 5, tsu="A", nm="甲"),
        _rec("Multi", "r1", 2024, 9, tsu="B", nm="乙"),
        _rec("Multi", "r2", 2024, 9, tsu="B", nm="乙"),
        _rec("Single", "solo", 2024, 1, tsu="A", nm="甲"),  # series with 1 station
        _rec("Single", "solo", 2024, 2, tsu="B", nm="乙"),
    ]
    keys = bs.build_group_keys(recs)
    out = bs.series_standings(recs, keys, field_sizes=fs, min_stations=2)
    assert "Multi" in out and "Single" not in out  # single-station series dropped


def test_series_standings_dedups_best_per_station():
    # rider with two category rows in the same station keeps the better pct, counts 1 station
    fs = {("r1", 2024): 100, ("r2", 2024): 100}
    recs = [
        _rec("S", "r1", 2024, 80, tsu="A", nm="甲"),   # pct 20
        _rec("S", "r1", 2024, 10, tsu="A", nm="甲"),   # pct 90 (same station, better)
        _rec("S", "r2", 2024, 30, tsu="A", nm="甲"),   # pct 70
    ]
    keys = bs.build_group_keys(recs)
    out = bs.series_standings(recs, keys, field_sizes=fs, min_stations=2)
    s = out["S"]["seasons"]["2024"]["standings"][0]
    assert s["n"] == 2 and s["pts"] == 160 and s["best"] == 90  # 90 (best in r1) + 70
