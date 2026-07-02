# -*- coding: utf-8 -*-
"""Build cross-year race difficulty coefficients (Feature ②).

Reads  data/processed/master.public.json   (de-identified — only times needed)
Writes web/public/data/v1/race_difficulty.json

For each race (race_key), the difficulty of a given year is that year's median
finish time relative to the race's typical year:

    coeff(race, year) = median_time(race, year) / baseline(race)
    baseline(race)    = median over the per-year medians

A slow ("hard") year has coeff > 1; an easy year coeff < 1. The frontend
calibrates a rider's time as raw / coeff, so an easy year no longer flatters and
a hard year no longer penalizes — isolating absolute fitness from conditions.

Tradeoffs (owner-approved): a race_key can mix distance/category groups (e.g.
50K vs 130K under one event), and the group mix can shift from year to year —
so coefficients are computed WITHIN each (race_key, result_label) group, each
with its own baseline, mirroring the shape used by benchmarks.json. Groups
fall back to 全部 when result_label is missing; only groups with >=2 years
that each have enough timed finishers qualify, and a race is kept iff it has
at least one qualifying group.
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
OUT = common.PUBLIC_DATA_DIR

MIN_FINISHERS = 20  # a year needs this many timed finishers for a stable median


def race_difficulty(records, min_finishers=MIN_FINISHERS):
    """{race_key: {name, groups: {group_label: {baseline, years}}}} — coefficients
    are computed WITHIN each (race_key, result_label) group so year-to-year
    group-mix shifts (e.g. more 130K finishers one year) never read as
    difficulty changes. group_label falls back to 全部 for unlabeled rows.
    A group needs >=2 years each with >=min_finishers timed finishers."""
    by_rgy = defaultdict(list)   # (race_key, group, year) -> [finish_seconds]
    names = {}
    for r in records:
        sec = r.get("finish_seconds")
        rk, y = r.get("race_key"), r.get("year")
        if not rk or not y or not sec or sec <= 0:
            continue
        g = r.get("result_label") or "全部"
        by_rgy[(rk, g, y)].append(sec)
        names.setdefault(rk, r.get("race_name_canonical") or r.get("race_name_raw"))

    year_med = defaultdict(lambda: defaultdict(dict))  # rk -> g -> {y: (median, n)}
    for (rk, g, y), secs in by_rgy.items():
        if len(secs) >= min_finishers:
            year_med[rk][g][y] = (statistics.median(secs), len(secs))

    out = {}
    for rk, groups in year_med.items():
        gout = {}
        for g, ym in groups.items():
            if len(ym) < 2:
                continue
            baseline = statistics.median([m for m, _ in ym.values()])
            if baseline <= 0:
                continue
            gout[g] = {"baseline": round(baseline), "years": {
                str(y): {"median": round(m), "coeff": round(m / baseline, 4), "n": n}
                for y, (m, n) in sorted(ym.items())}}
        if gout:
            out[rk] = {"name": names.get(rk), "groups": gout}
    return out


def main():
    records = common.iter_records(IN)
    diff = race_difficulty(records)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "race_difficulty.json"), "w", encoding="utf-8") as f:
        json.dump(diff, f, ensure_ascii=False, separators=(",", ":"))
    total_years = sum(len(g["years"]) for d in diff.values() for g in d["groups"].values())
    print(f"race_difficulty={len(diff)} races ({total_years} race-years) "
          f"-> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
