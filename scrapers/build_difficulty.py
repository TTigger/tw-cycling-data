# -*- coding: utf-8 -*-
"""Build cross-year race difficulty coefficients (Feature ②).

Reads  data/processed/master.public.json   (de-identified — only times needed)
Writes web/public/data/race_difficulty.json

For each race (race_key), the difficulty of a given year is that year's median
finish time relative to the race's typical year:

    coeff(race, year) = median_time(race, year) / baseline(race)
    baseline(race)    = median over the per-year medians

A slow ("hard") year has coeff > 1; an easy year coeff < 1. The frontend
calibrates a rider's time as raw / coeff, so an easy year no longer flatters and
a hard year no longer penalizes — isolating absolute fitness from conditions.

Tradeoffs (owner-approved): the median is over ALL timed finishers (coeff is a
relative ratio, so category-mix differences mostly cancel year to year); only
races with >=2 years that each have enough timed finishers qualify.
"""
import json
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.public.json")
OUT = os.path.join(HERE, "..", "web", "public", "data")

MIN_FINISHERS = 20  # a year needs this many timed finishers for a stable median


def race_difficulty(records, min_finishers=MIN_FINISHERS):
    """{race_key: {name, baseline, years: {year: {median, coeff, n}}}} for every
    race with >=2 years that each have >=min_finishers timed finishers."""
    by_ry = defaultdict(list)   # (race_key, year) -> [finish_seconds]
    names = {}
    for r in records:
        sec = r.get("finish_seconds")
        rk, y = r.get("race_key"), r.get("year")
        if not rk or not y or not sec or sec <= 0:
            continue
        by_ry[(rk, y)].append(sec)
        names.setdefault(rk, r.get("race_name_canonical") or r.get("race_name_raw"))

    year_med = defaultdict(dict)   # race_key -> {year: (median, n)}
    for (rk, y), secs in by_ry.items():
        if len(secs) >= min_finishers:
            year_med[rk][y] = (statistics.median(secs), len(secs))

    out = {}
    for rk, ym in year_med.items():
        if len(ym) < 2:
            continue
        baseline = statistics.median([m for m, _ in ym.values()])
        if baseline <= 0:
            continue
        years = {
            str(y): {"median": round(m), "coeff": round(m / baseline, 4), "n": n}
            for y, (m, n) in sorted(ym.items())
        }
        out[rk] = {"name": names.get(rk), "baseline": round(baseline), "years": years}
    return out


def main():
    records = common.iter_records(IN)
    diff = race_difficulty(records)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "race_difficulty.json"), "w", encoding="utf-8") as f:
        json.dump(diff, f, ensure_ascii=False, separators=(",", ":"))
    total_years = sum(len(d["years"]) for d in diff.values())
    print(f"race_difficulty={len(diff)} races ({total_years} race-years) "
          f"-> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
