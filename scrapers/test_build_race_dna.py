# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_race_dna as rd


def _rec(rk, year, sec, g="M", cat=None, rn=None):
    return {"race_key": rk, "year": year, "finish_seconds": sec, "gender": g,
            "category_raw": cat, "result_label": None,
            "race_name_canonical": rn or rk}


def test_cov_and_pct_rank():
    assert abs(rd._cov([1000, 2000, 3000, 4000]) - 1118.033988749895 / 2500) < 1e-9
    assert rd._cov([5]) is None              # need >=2
    r = rd._pct_rank([("a", 1), ("b", 2), ("c", 3)])
    assert r["a"] == 0.0 and r["c"] == 100.0 and 0 < r["b"] < 100
    assert rd._pct_rank([("solo", 9)]) == {"solo": 50.0}   # single -> neutral


def _ra_dataset():
    # race A year 2024: 4 finishers; g1 is a multi-year regular & repeater of A
    recs = [
        _rec("A", 2024, 1000, g="F"),   # g1
        _rec("A", 2024, 2000, g="M"),   # g2
        _rec("A", 2024, 3000, g="M"),   # g3
        _rec("A", 2024, 4000, g="M"),   # g4
        _rec("A", 2023, 1500, g="F"),   # g1 again (other year of A) -> repeater
        _rec("A", 2022, 1500, g="F"),   # g1 again -> 3 distinct race-years = regular
    ]
    # parallel group keys (g1 shares a key across its 3 rows)
    keys = ["n:g1", "n:g2", "n:g3", "n:g4", "n:g1", "n:g1"]
    return recs, keys


def test_raw_axes_values():
    recs, keys = _ra_dataset()
    raw = rd.raw_axes(recs, keys, min_finishers=4)
    a = raw[("A", 2024)]
    assert a["n"] == 4 and a["size"] == 4.0
    assert a["women"] == 25.0                       # 1 of 4
    assert a["prest"] == 25.0                       # g1 is the only regular
    assert a["repeat"] == 25.0                      # g1 rode A in another year
    assert abs(a["sel"] - (1118.033988749895 / 2500)) < 1e-9
    assert a["climb"] is None                       # no distance labels -> no speed


def test_build_race_dna_normalizes_0_100():
    recs, keys = _ra_dataset()
    # race B year 2025: 4 finishers, 2 women (higher women ratio than A)
    recs += [_rec("B", 2025, 1000, g="F"), _rec("B", 2025, 2000, g="F"),
             _rec("B", 2025, 3000, g="M"), _rec("B", 2025, 4000, g="M")]
    keys += ["n:g5", "n:g6", "n:g7", "n:g8"]
    dna = rd.build_race_dna(recs, keys, min_finishers=4)
    assert set(dna) == {"A", "B"}
    av = dna["A"]["years"]["2024"]
    bv = dna["B"]["years"]["2025"]
    # all axes are ints in 0..100
    for v in (av, bv):
        for ax in rd.AXES:
            assert 0 <= v[ax] <= 100
    # B has the higher women ratio -> ranks higher on that axis
    assert bv["women"] > av["women"]
    # neither race has a derivable climb -> both neutral 50
    assert av["climb"] == 50 and bv["climb"] == 50
    assert av["n"] == 4
