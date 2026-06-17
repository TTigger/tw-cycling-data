# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_teams as bt


def _rec(team, rk, year, rank, tsu, nm):
    return {"team": team, "race_key": rk, "year": year, "rank_overall": rank,
            "race_name_canonical": rk, "tsu_rider_id": tsu, "uci_id": None,
            "name_raw": nm, "name_masked": nm}


def test_build_teams_rosters_and_record():
    fs = {("r1", 2024): 100, ("r2", 2024): 100, ("r1", 2023): 100}
    recs = [
        _rec("Alpha", "r1", 2024, 1, "A", "甲"),    # win, pct 99
        _rec("Alpha", "r2", 2024, 3, "A", "甲"),    # podium
        _rec("Alpha", "r1", 2024, 10, "B", "乙"),
        _rec("Alpha", "r1", 2023, 50, "C", "丙"),
        _rec("Alpha", "r2", 2024, 20, "D", "丁"),
    ]
    keys = bt.build_group_keys(recs)
    index, details = bt.build_teams(recs, keys, field_sizes=fs, min_riders=4)
    tid = bt.team_id("Alpha")
    assert [t["id"] for t in index] == [tid]
    d = details[tid]
    assert d["riders"] == 4 and d["races"] == 2
    assert d["wins"] == 1 and d["podiums"] == 2 and d["best"] == 1
    assert d["y0"] == 2023 and d["y1"] == 2024
    assert d["roster"][0]["id"] == bt.athlete_id("t:A")   # most rows first
    assert d["roster"][0]["n"] == 2 and d["roster"][0]["best"] == 1
    assert d["highlights"][0]["pct"] == 99                # best in-field result featured
    by = {x["y"]: x for x in d["byYear"]}
    assert by[2024]["riders"] == 3 and by[2024]["races"] == 2


def test_small_and_noise_teams_excluded():
    fs = {("r1", 2024): 100}
    recs = [
        _rec("Solo", "r1", 2024, 1, "A", "甲"),       # only 1 rider -> dropped
        _rec("Solo", "r1", 2024, 2, "B", "乙"),
        _rec("Solo", "r1", 2024, 3, "C", "丙"),
        _rec("個人", "r1", 2024, 4, "D", "丁"),         # noise team name -> dropped
        _rec("個人", "r1", 2024, 5, "E", "戊"),
        _rec("個人", "r1", 2024, 6, "F", "己"),
        _rec("個人", "r1", 2024, 7, "G", "庚"),
    ]
    keys = bt.build_group_keys(recs)
    index, details = bt.build_teams(recs, keys, field_sizes=fs, min_riders=4)
    assert index == [] and details == {}


def test_single_race_pseudo_team_excluded():
    # 4 riders but all in ONE race (event-assigned color squad) -> not a real team
    fs = {("r1", 2024): 1000}
    recs = [_rec("桃紅隊", "r1", 2024, i, f"A{i}", f"甲{i}") for i in range(1, 6)]
    keys = bt.build_group_keys(recs)
    index, details = bt.build_teams(recs, keys, field_sizes=fs, min_riders=4, min_races=2)
    assert index == [] and details == {}


def test_unresolved_identity_rows_skipped():
    # a row with no rider id and a name that ties to no anchor stays n:<name>;
    # such rows must not inflate a roster.
    fs = {("r1", 2024): 100}
    recs = [
        _rec("Beta", "r1", 2024, 1, "A", "甲"),
        _rec("Beta", "r1", 2024, 2, "B", "乙"),
        _rec("Beta", "r1", 2024, 3, "C", "丙"),
        {"team": "Beta", "race_key": "r1", "year": 2024, "rank_overall": 4,
         "race_name_canonical": "r1", "tsu_rider_id": None, "uci_id": None,
         "name_raw": None, "name_masked": None},   # nameless -> n:
    ]
    keys = bt.build_group_keys(recs)
    index, _ = bt.build_teams(recs, keys, field_sizes=fs, min_riders=4)
    assert index == []   # only 3 resolvable riders, nameless row skipped
