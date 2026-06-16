# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_difficulty as bd


def _rec(rk, year, sec, rn=None):
    return {"race_key": rk, "year": year, "finish_seconds": sec,
            "race_name_canonical": rn or rk}


def test_difficulty_coeff_relative_to_baseline():
    # race A: year 2023 medians ~ 2000s (slow/hard), 2024 ~ 1000s (fast/easy)
    recs = []
    for s in range(2000, 2000 + 60):        # 60 finishers, median ~2029
        recs.append(_rec("A", 2023, s))
    for s in range(1000, 1000 + 60):        # 60 finishers, median ~1029
        recs.append(_rec("A", 2024, s))
    out = bd.race_difficulty(recs, min_finishers=20)
    assert "A" in out
    yrs = out["A"]["years"]
    assert set(yrs) == {"2023", "2024"}
    # baseline = median of the two year-medians; slow year coeff>1, fast year<1
    assert yrs["2023"]["coeff"] > 1 and yrs["2024"]["coeff"] < 1
    # coeffs are symmetric about the baseline (two years -> reciprocal-ish)
    assert yrs["2023"]["median"] > yrs["2024"]["median"]
    assert yrs["2023"]["n"] == 60


def test_difficulty_drops_thin_years_and_single_year_races():
    recs = []
    for s in range(1000, 1000 + 30):        # A 2023: 30 finishers (ok)
        recs.append(_rec("A", 2023, s))
    for s in range(1000, 1000 + 30):        # A 2024: 30 finishers (ok) -> A qualifies
        recs.append(_rec("A", 2024, s))
    recs.append(_rec("A", 2025, 1500))      # A 2025: 1 finisher -> dropped (thin)
    for s in range(1000, 1000 + 30):        # B 2023 only -> single year, dropped
        recs.append(_rec("B", 2023, s))
    out = bd.race_difficulty(recs, min_finishers=20)
    assert set(out) == {"A"}
    assert set(out["A"]["years"]) == {"2023", "2024"}   # thin 2025 excluded


def test_difficulty_ignores_missing_times():
    recs = [_rec("A", 2023, None), _rec("A", 2023, 0), _rec("A", 2023, -5)]
    recs += [_rec("A", 2024, 1000) for _ in range(30)]
    out = bd.race_difficulty(recs, min_finishers=20)
    assert out == {}     # 2023 has no valid times -> A has <2 qualifying years
