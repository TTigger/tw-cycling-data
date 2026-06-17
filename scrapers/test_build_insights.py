# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_insights as bi


def test_quantile():
    v = [1, 2, 3, 4, 5]
    assert bi.quantile(v, 0.5) == 3
    assert bi.quantile(v, 0.0) == 1
    assert bi.quantile(v, 1.0) == 5
    assert bi.quantile([], 0.5) is None


def test_in_field_pct():
    assert bi.in_field_pct(1, 100) == 99.0
    assert bi.in_field_pct(50, 100) == 50.0
    assert bi.in_field_pct(None, 100) is None
    assert bi.in_field_pct(5, 0) is None


def _r(band, rank, rk, y=2024, g="M", t=3600.0):
    return {"age_band": band, "rank_overall": rank, "race_key": rk, "year": y,
            "gender": g, "finish_seconds": t}


def test_build_age_curve_groups_by_band_and_gender():
    # 60 finishers in one race; ranks 1..60, band 30-39, gender M
    recs = [_r("30-39", i, "r1", g="M", t=1000 + i) for i in range(1, 61)]
    out = bi.build_age_curve(recs)
    rows = {(e["band"], e["g"]): e for e in out}
    assert ("30-39", "M") in rows and ("30-39", "all") in rows
    e = rows[("30-39", "M")]
    assert e["n"] == 60
    # median rank 30/60 -> ~50% of field beaten
    assert 45 <= e["p50"] <= 55
    # MASTER / unknown bands excluded
    assert all(e["band"] in bi.AGE_ORDER for e in out)


def test_build_age_curve_drops_small_samples():
    recs = [_r("U19", i, "r1") for i in range(1, 10)]  # only 9 -> < 50 threshold
    assert bi.build_age_curve(recs) == []


def _rb(name, rk, y, rank, field_filler, tsu=None):
    # one rider + (field_filler-1) others so the race has `field_filler` finishers
    rows = [{"name_raw": name, "name_masked": None, "tsu_rider_id": tsu, "uci_id": None,
             "race_key": rk, "year": y, "rank_overall": rank, "gender": "M",
             "finish_seconds": 3600.0 + rank}]
    for j in range(2, field_filler + 1):
        rows.append({"name_raw": f"填充{j}{rk}{y}", "name_masked": None, "tsu_rider_id": None,
                     "uci_id": None, "race_key": rk, "year": y, "rank_overall": j,
                     "gender": "M", "finish_seconds": 3600.0 + j})
    return rows


def test_build_breakout_finds_year_jump():
    recs = []
    # athlete "王大明": 2023 ranks ~mid (pct ~50), 2024 ranks top (pct ~99) -> big jump
    recs += _rb("王大明", "rA", 2023, 50, 100, tsu="TCU-z")
    recs += _rb("王大明", "rB", 2023, 50, 100, tsu="TCU-z")
    recs += _rb("王大明", "rC", 2024, 1, 100, tsu="TCU-z")
    recs += _rb("王大明", "rD", 2024, 1, 100, tsu="TCU-z")
    out = bi.build_breakout(recs, min_per_year=2, min_jump=15.0)
    assert len(out) == 1
    e = out[0]
    assert e["from_y"] == 2023 and e["to_y"] == 2024
    assert e["jump"] > 40 and e["nm"] == "王○明" and e["anchored"] is True
    assert "name_raw" not in e


def test_build_ratings_scores_and_stars():
    recs = []
    # bigRace: 40 finishers across 3 years, many regulars -> high score
    for y in (2022, 2023, 2024):
        for i in range(1, 41):
            nm = f"常客{i}" if i <= 30 else f"路人{i}{y}"
            recs.append({"name_raw": nm, "name_masked": None, "race_key": "bigRace",
                         "race_name_canonical": "Big Race", "year": y, "rank_overall": i,
                         "gender": "M", "finish_seconds": 3600.0 + i})
    # the 30 常客 also race two other events -> become "regulars" (>=3 race_keys)
    for rk in ("other1", "other2"):
        for i in range(1, 31):
            recs.append({"name_raw": f"常客{i}", "name_masked": None, "race_key": rk,
                         "race_name_canonical": rk, "year": 2024, "rank_overall": i,
                         "gender": "M", "finish_seconds": 3600.0 + i})
    out = bi.build_ratings(recs)
    big = next(r for r in out if r["race_key"] == "bigRace")
    assert big["med_field"] == 40 and big["editions"] == 3
    assert big["regular_pct"] == 75.0   # 30 of 40
    assert 1 <= big["stars"] <= 5 and big["score"] > 0
    assert big["years"] == [2022, 2023, 2024]


def test_race_region_and_geo():
    assert bi.race_region("建大武嶺盃") == "南投"
    assert bi.race_region("臺灣KOM登山王之路-春季") == "花蓮"
    assert bi.race_region("扶輪盃陽明山自行車登山王") == "臺北"  # 陽明山 wins (listed first)
    assert bi.race_region("彰化經典百K") == "彰化"
    assert bi.race_region("某神秘賽", "高雄") == "高雄"  # falls back to region field
    assert bi.race_region("無線索賽") is None
    recs = [
        {"race_name_canonical": "建大武嶺盃", "race_key": "a", "region": None},
        {"race_name_canonical": "建大武嶺盃", "race_key": "a", "region": None},
        {"race_name_canonical": "彰化經典百K", "race_key": "b", "region": None},
    ]
    geo = bi.build_geo(recs)
    nantou = next(g for g in geo if g["region"] == "南投")
    assert nantou["rows"] == 2 and nantou["races"] == 1




def test_streak():
    assert bi._streak([2019, 2020, 2021, 2024]) == 3
    assert bi._streak([2020, 2022, 2024]) == 1
    assert bi._streak([]) == 0


def _rrec(name, rk, y, rank, g="M", tsu=None, team="A"):
    return {"name_raw": name, "name_masked": None, "race_key": rk, "race_name_canonical": rk,
            "year": y, "rank_overall": rank, "gender": g, "team": team,
            "tsu_rider_id": tsu, "uci_id": None}


def test_build_records_biggest_field_wins_loyal():
    recs = [_rrec(f"p{i}", "BIG", 2024, i + 1, tsu=f"T{i}") for i in range(5)]  # 5 finishers
    recs += [_rrec(f"q{i}", "small", 2024, i + 1, tsu=f"S{i}") for i in range(2)]
    recs.append(_rrec("p0", "BIG", 2023, 1, tsu="T0"))   # p0 wins BIG twice, rides it 2 yrs
    out = bi.build_records(recs, top=5)
    assert out["biggest_field"][0]["rk"] == "BIG" and out["biggest_field"][0]["n"] == 5
    aid = bi.athlete_id("t:T0")
    assert next(x for x in out["most_wins"] if x["id"] == aid)["v"] == 2
    loyal = next(x for x in out["most_loyal"] if x["id"] == aid)
    assert loyal["v"] == 2 and loyal["rk"] == "BIG"


def test_build_records_excludes_low_confidence_homonym():
    # one name across 6 teams + mixed gender -> low confidence -> excluded from boards
    recs = [_rrec("甲", f"r{i}", 2020 + i, 1, g=("M" if i % 2 else "F"), team=t)
            for i, t in enumerate("ABCDEQ")]
    aid = bi.athlete_id("n:甲")
    out = bi.build_records(recs)
    assert all(x["id"] != aid for x in out["most_wins"])   # 6 wins, but homonym-risky -> dropped
