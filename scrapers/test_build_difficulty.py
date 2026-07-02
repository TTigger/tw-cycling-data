# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_difficulty as bd


def _rec(rk, year, sec, rn=None):
    return {"race_key": rk, "year": year, "finish_seconds": sec,
            "race_name_canonical": rn or rk}


def _row(rk, y, sec, label):
    return {"race_key": rk, "year": y, "finish_seconds": sec, "result_label": label,
            "race_name_canonical": rk}


def test_difficulty_coeff_relative_to_baseline():
    # race A: year 2023 medians ~ 2000s (slow/hard), 2024 ~ 1000s (fast/easy)
    recs = []
    for s in range(2000, 2000 + 60):        # 60 finishers, median ~2029
        recs.append(_rec("A", 2023, s))
    for s in range(1000, 1000 + 60):        # 60 finishers, median ~1029
        recs.append(_rec("A", 2024, s))
    out = bd.race_difficulty(recs, min_finishers=20)
    assert "A" in out
    yrs = out["A"]["groups"]["全部"]["years"]
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
    assert set(out["A"]["groups"]["全部"]["years"]) == {"2023", "2024"}   # thin 2025 excluded


def test_difficulty_ignores_missing_times():
    recs = [_rec("A", 2023, None), _rec("A", 2023, 0), _rec("A", 2023, -5)]
    recs += [_rec("A", 2024, 1000) for _ in range(30)]
    out = bd.race_difficulty(recs, min_finishers=20)
    assert out == {}     # 2023 has no valid times -> A has <2 qualifying years


def test_race_difficulty_groups_by_result_label():
    rows = []
    # group 50K: 2023 median 3600, 2024 median 3960 (coeff 1.1 vs baseline 3780)
    rows += [_row("R", 2023, 3600 + i, "50K") for i in range(-10, 10)]
    rows += [_row("R", 2024, 3960 + i, "50K") for i in range(-10, 10)]
    # group 130K: slower times, own baseline — must NOT blend with 50K
    rows += [_row("R", 2023, 18000 + i, "130K") for i in range(-10, 10)]
    rows += [_row("R", 2024, 18000 + i, "130K") for i in range(-10, 10)]
    d = bd.race_difficulty(rows, min_finishers=20)
    g50 = d["R"]["groups"]["50K"]
    assert g50["baseline"] == 3780
    assert g50["years"]["2023"]["coeff"] == round(3600 / 3780, 4)
    assert d["R"]["groups"]["130K"]["years"]["2023"]["coeff"] == 1.0
    assert d["R"]["name"] == "R"


def test_race_difficulty_drops_thin_group_year_and_single_year_group():
    rows = [_row("R", 2023, 3600 + i, "A") for i in range(-10, 10)]      # A: only 1 valid year
    rows += [_row("R", 2024, 3700, "A")] * 5                              # 2024 <20 -> dropped
    rows += [_row("R", 2023, 900 + i, None) for i in range(-10, 10)]     # 全部: 2 years ok
    rows += [_row("R", 2024, 950 + i, None) for i in range(-10, 10)]
    d = bd.race_difficulty(rows, min_finishers=20)
    assert set(d["R"]["groups"]) == {"全部"}


def test_race_difficulty_drops_race_with_no_qualifying_group():
    rows = [_row("S", 2023, 3600 + i, "A") for i in range(-10, 10)]
    assert "S" not in bd.race_difficulty(rows, min_finishers=20)
