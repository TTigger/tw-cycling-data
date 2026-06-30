# -*- coding: utf-8 -*-
"""Build per-race "DNA" fingerprints (Feature ③).

Reads  data/processed/master.json   (INTERNAL — needs identity grouping for the
                                      regulars / repeat-rate axes)
Writes web/public/data/race_dna.json (aggregate-only — de-identified)

Six axes, each percentile-normalized 0–100 across all qualifying race-years so a
radar compares any two races on the same scale:

  sel    選擇性   coefficient of variation of finish times (spread = separating)
  size   規模     number of finishers
  climb  爬坡度   inverse median speed (slower race = climbier); needs distances
  prest  含金量   share of finishers who are "regulars" (raced >=3 race-years)
  repeat 回頭率   share of this edition's riders who also rode another edition
  women  女子比例 share of F among gendered finishers

Output carries only the race name + aggregate axis values — no rider data.
"""
import json
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402
from build_athletes import build_group_keys  # noqa: E402
from build_viz import extract_distance_km, avg_speed_kmh  # noqa: E402

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.json")
OUT = common.PUBLIC_DATA_DIR

MIN_FINISHERS = 20            # a race-year needs this many finishers to qualify
REGULAR_MIN_RACE_YEARS = 3    # raced in this many distinct race-years = a regular
AXES = ["sel", "size", "climb", "prest", "repeat", "women"]

_UNRESOLVED = ("n:", "u:", "t:")


def _cov(vals):
    """Coefficient of variation (spread / mean). None if <2 values or mean<=0."""
    if len(vals) < 2:
        return None
    m = statistics.mean(vals)
    if m <= 0:
        return None
    return statistics.pstdev(vals) / m


def _pct_rank(pairs):
    """{key: 0–100 ordinal percentile} for [(key, value), ...]. Single -> 50."""
    s = sorted(pairs, key=lambda kv: kv[1])
    n = len(s)
    if n == 1:
        return {s[0][0]: 50.0}
    return {k: i / (n - 1) * 100 for i, (k, _) in enumerate(s)}


def raw_axes(records, group_keys, min_finishers=MIN_FINISHERS):
    """Un-normalized axis values per (race_key, year) with >=min_finishers
    finishers. group_keys is parallel to records (build_group_keys)."""
    rider_ryears = defaultdict(set)                         # gk -> {(rk, year)}
    rider_rk_years = defaultdict(lambda: defaultdict(set))  # gk -> rk -> {year}
    for gk, r in zip(group_keys, records):
        if gk in _UNRESOLVED:
            continue
        rk, y = r.get("race_key"), r.get("year")
        if rk and y is not None:
            rider_ryears[gk].add((rk, y))
            rider_rk_years[gk][rk].add(y)
    regulars = {gk for gk, s in rider_ryears.items() if len(s) >= REGULAR_MIN_RACE_YEARS}

    by_ry = defaultdict(list)   # (rk, year) -> [(record, gk)]
    names = {}
    for gk, r in zip(group_keys, records):
        rk, y = r.get("race_key"), r.get("year")
        if not rk or y is None:
            continue
        by_ry[(rk, y)].append((r, gk))
        names.setdefault(rk, r.get("race_name_canonical") or r.get("race_name_raw"))

    out = {}
    for (rk, y), items in by_ry.items():
        n = len(items)
        if n < min_finishers:
            continue
        secs = [r["finish_seconds"] for r, _ in items
                if r.get("finish_seconds") and r["finish_seconds"] > 0]
        speeds = []
        for r, _ in items:
            d = extract_distance_km(r.get("category_raw"), r.get("result_label"),
                                    r.get("race_name_canonical") or r.get("race_name_raw"))
            sp = avg_speed_kmh(d, r.get("finish_seconds"))
            if sp:
                speeds.append(sp)
        genders = [r.get("gender") for r, _ in items if r.get("gender") in ("M", "F")]
        distinct = {gk for _, gk in items if gk not in _UNRESOLVED}
        repeaters = sum(1 for gk in distinct if rider_rk_years[gk][rk] - {y})
        reg_here = sum(1 for gk in distinct if gk in regulars)
        # climbiness only when a fifth (and >=5) of the field has a parseable
        # distance — too few labels and the median speed isn't representative.
        climb = -statistics.median(speeds) if len(speeds) >= max(5, n * 0.2) else None
        out[(rk, y)] = {
            "name": names.get(rk), "n": n,
            "sel": _cov(secs),
            "size": float(n),
            "climb": climb,
            "prest": reg_here / len(distinct) * 100 if distinct else None,
            "repeat": repeaters / len(distinct) * 100 if distinct else None,
            "women": sum(1 for g in genders if g == "F") / len(genders) * 100 if genders else None,
        }
    return out


def build_race_dna(records, group_keys, min_finishers=MIN_FINISHERS):
    """{race_key: {name, years: {year: {n, sel, size, climb, prest, repeat, women}}}}
    with each axis percentile-normalized 0–100 over all qualifying race-years.
    A race-year missing a raw axis value gets the neutral midpoint (50)."""
    raw = raw_axes(records, group_keys, min_finishers)
    norm = {ax: _pct_rank([(k, v[ax]) for k, v in raw.items() if v[ax] is not None])
            for ax in AXES}
    out = {}
    for (rk, y), v in raw.items():
        axes = {ax: round(norm[ax].get((rk, y), 50.0)) for ax in AXES}
        d = out.setdefault(rk, {"name": v["name"], "years": {}})
        d["years"][str(y)] = {"n": v["n"], **axes}
    return out


def main():
    records = list(common.iter_records(IN))
    group_keys = build_group_keys(records)
    dna = build_race_dna(records, group_keys)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "race_dna.json"), "w", encoding="utf-8") as f:
        json.dump(dna, f, ensure_ascii=False, separators=(",", ":"))
    ry = sum(len(d["years"]) for d in dna.values())
    print(f"race_dna={len(dna)} races ({ry} race-years) -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
