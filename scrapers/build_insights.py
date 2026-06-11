# -*- coding: utf-8 -*-
"""Build aggregate analytics datasets (the /insights page) from the master
dataset. Emits web/public/data/insights.json with de-identified sections.

Reads master.json (internal) so identity-based sections can group an athlete's
career via build_athletes' TCU/UCI/name grouping; output carries only masked
names + salted athlete ids — never name_raw.
"""
import json
import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402,F401
from build_athletes import build_group_keys, athlete_id, MIN_RESULTS  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.json")
OUT = os.path.join(HERE, "..", "web", "public", "data")

AGE_ORDER = ["U19", "19-29", "30-39", "40-49", "50-59", "60+"]


def quantile(sorted_vals, q):
    """Linear-interpolated quantile of an already-sorted list."""
    if not sorted_vals:
        return None
    i = q * (len(sorted_vals) - 1)
    lo = int(i)
    frac = i - lo
    if lo + 1 < len(sorted_vals):
        return sorted_vals[lo] * (1 - frac) + sorted_vals[lo + 1] * frac
    return sorted_vals[lo]


def field_sizes(records):
    """Classified finishers per (race_key, year) — the denominator for in-field
    percentile. Counts every row with a rank (not just timed ones, since some
    finishers have a placing but no recorded finish_seconds)."""
    return Counter((r.get("race_key"), r.get("year")) for r in records
                   if r.get("rank_overall"))


def in_field_pct(rank, field):
    """% of the field beaten = (field - rank) / field * 100. None if invalid or
    inconsistent (rank beyond the counted field — a data gap, not a real result)."""
    if not rank or not field or field < 1 or rank < 1 or rank > field:
        return None
    return (field - rank) / field * 100


def build_age_curve(records):
    """Median in-field percentile by coarse age band (× gender). Shows which age
    bands tend to beat more of the field — a population 'peak age' view.
    NOTE: age_band is decade-level (coarse) and there is survivorship bias (only
    committed riders persist to older bands); presented as exploratory."""
    fields = field_sizes(records)
    buckets = defaultdict(list)
    for r in records:
        band = r.get("age_band")
        if band not in AGE_ORDER:
            continue
        pct = in_field_pct(r.get("rank_overall"),
                           fields.get((r.get("race_key"), r.get("year"))))
        if pct is None:
            continue
        buckets[(band, "all")].append(pct)
        g = r.get("gender")
        if g in ("M", "F"):
            buckets[(band, g)].append(pct)
    out = []
    for (band, g), vals in buckets.items():
        if len(vals) < 50:                      # need a meaningful sample
            continue
        vals.sort()
        out.append({"band": band, "g": g, "n": len(vals),
                    "p25": round(quantile(vals, 0.25), 1),
                    "p50": round(quantile(vals, 0.5), 1),
                    "p75": round(quantile(vals, 0.75), 1)})
    out.sort(key=lambda e: (AGE_ORDER.index(e["band"]), e["g"]))
    return out


def _median(vals):
    s = sorted(vals)
    return quantile(s, 0.5)


def _masked(recs):
    return Counter(r.get("name_masked") or common.mask_name(r.get("name_raw"))
                   for r in recs).most_common(1)[0][0]


def _mode_gender(recs):
    gs = Counter(r.get("gender") for r in recs if r.get("gender") in ("M", "F"))
    return gs.most_common(1)[0][0] if gs else None


def build_breakout(records, min_per_year=2, min_jump=15.0, top=40):
    """Biggest year-over-year improvement in median in-field percentile per
    athlete (a 'breakout' season). Each year needs >=min_per_year results so the
    yearly median is stable; only jumps >=min_jump percentile points are kept.
    Uses the same TCU/UCI/name identity grouping as the athlete pages."""
    fields = field_sizes(records)
    keys = build_group_keys(records)
    groups = defaultdict(list)
    for k, r in zip(keys, records):
        if k not in ("n:", "u:", "t:"):
            groups[k].append(r)
    out = []
    for gk, recs in groups.items():
        if len(recs) < MIN_RESULTS:
            continue
        by_year = defaultdict(list)
        for r in recs:
            pct = in_field_pct(r.get("rank_overall"),
                               fields.get((r.get("race_key"), r.get("year"))))
            if pct is not None and r.get("year"):
                by_year[r["year"]].append(pct)
        yr_med = {y: _median(v) for y, v in by_year.items() if len(v) >= min_per_year}
        years = sorted(yr_med)
        if len(years) < 2:
            continue
        best = None
        for a, b in zip(years, years[1:]):           # consecutive racing years
            jump = yr_med[b] - yr_med[a]
            if best is None or jump > best["jump"]:
                best = {"from_y": a, "to_y": b,
                        "from_pct": round(yr_med[a], 1), "to_pct": round(yr_med[b], 1),
                        "jump": round(jump, 1)}
        if best is None or best["jump"] < min_jump:
            continue
        out.append({"id": athlete_id(gk), "nm": _masked(recs),
                    "g": _mode_gender(recs), "anchored": gk[0] in ("t", "u"), **best})
    out.sort(key=lambda e: -e["jump"])
    return out[:top]


def build_ratings(records):
    """A transparent per-race competitiveness rating from three signals:
      - scale: median finishers per edition (log-scaled)
      - longevity: number of years the race has been held
      - field depth: % of finishers who are 'regulars' (race >=3 distinct races)
    Combined to a 0-100 score, then bucketed to 1-5 stars by rank across all
    rated races (>=20 median finishers)."""
    fields = field_sizes(records)
    name_races = defaultdict(set)
    for r in records:
        if r.get("name_raw"):
            name_races[r["name_raw"]].add(r.get("race_key"))
    regular = {nm for nm, rks in name_races.items() if len(rks) >= 3}

    agg = defaultdict(lambda: {"years": set(), "name": None, "finishers": 0, "regulars": 0})
    for r in records:
        rk = r.get("race_key")
        if not rk:
            continue
        d = agg[rk]
        d["years"].add(r.get("year"))
        d["name"] = r.get("race_name_canonical") or rk
        d["finishers"] += 1
        if r.get("name_raw") in regular:
            d["regulars"] += 1

    rows = []
    for rk, d in agg.items():
        eds = [fields[(rk, y)] for y in d["years"] if (rk, y) in fields]
        if not eds:
            continue
        med_field = int(quantile(sorted(eds), 0.5))
        if med_field < 20:                           # skip tiny races
            continue
        editions = len([y for y in d["years"] if y])
        reg_pct = round(d["regulars"] / d["finishers"] * 100, 1) if d["finishers"] else 0.0
        f_score = min(math.log10(med_field) / math.log10(2500), 1.0)
        e_score = min(editions / 8, 1.0)
        r_score = min(reg_pct / 40, 1.0)
        score = round((0.4 * f_score + 0.25 * e_score + 0.35 * r_score) * 100)
        rows.append({"race_key": rk, "name": d["name"], "score": score,
                     "med_field": med_field, "editions": editions, "regular_pct": reg_pct,
                     "years": sorted(y for y in d["years"] if y)})
    rows.sort(key=lambda x: -x["score"])
    n = len(rows) or 1
    for i, row in enumerate(rows):
        q = i / n
        row["stars"] = 5 if q < 0.1 else 4 if q < 0.3 else 3 if q < 0.6 else 2 if q < 0.85 else 1
    return rows[:60]


def main():
    with open(IN, encoding="utf-8") as f:
        records = json.load(f)
    insights = {
        "age_curve": build_age_curve(records),
        "breakout": build_breakout(records),
        "ratings": build_ratings(records),
    }
    with open(os.path.join(OUT, "insights.json"), "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, separators=(",", ":"))
    print("insights sections:", {k: len(v) for k, v in insights.items()})


if __name__ == "__main__":
    main()
