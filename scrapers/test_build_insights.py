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
