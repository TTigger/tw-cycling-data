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
from build_athletes import build_group_keys, athlete_id, MIN_RESULTS, confidence  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.json")
OUT = common.PUBLIC_DATA_DIR

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


import re  # noqa: E402

# race-name → county (first match wins; ordered roughly north→south). Landmarks
# map to the county they sit in; explicit county names take priority via ordering.
REGION_KW = [
    (r"臺北|台北|天母|陽明山|大屯山|北海岸|擎天崗", "臺北"),
    (r"新北|淡海|平溪|雙溪", "新北"),
    (r"桃園|中壢|龍潭", "桃園"),
    (r"新竹|竹站", "新竹"),
    (r"苗栗|仙山", "苗栗"),
    (r"臺中|台中|大雪山", "臺中"),
    (r"彰化|八卦山", "彰化"),
    (r"南投|武嶺|日月潭|中寮|埔里|魚池", "南投"),
    (r"雲林|石壁|古坑", "雲林"),
    (r"嘉義|阿里山|塔塔加", "嘉義"),
    (r"臺南|台南", "臺南"),
    (r"高雄", "高雄"),
    (r"屏東|四重溪", "屏東"),
    (r"宜蘭|太平山|牛鬥", "宜蘭"),
    (r"花蓮|太平洋|登山王|太魯閣|花東", "花蓮"),
    (r"臺東|台東", "臺東"),
    (r"澎湖", "澎湖"),
    (r"金門|金沙", "金門"),
]
_REGION_RE = [(re.compile(p), c) for p, c in REGION_KW]


def race_region(name, region_field=None):
    """Derive a county from the race name (preferred, uniform) else the region
    field. None if neither resolves."""
    n = name or ""
    county = None
    for rx, c in _REGION_RE:
        if rx.search(n):
            county = c
            break
    county = county or region_field
    if not county:
        return None
    return re.sub(r"[縣市]$", "", county.strip()) or None   # 臺東縣/臺中市 -> 臺東/臺中


def build_geo(records):
    """Per-county race count + 人次 (finisher-entries), a geographic hotspot view."""
    agg = defaultdict(lambda: {"races": set(), "rows": 0})
    for r in records:
        county = race_region(r.get("race_name_canonical"), r.get("region"))
        if not county:
            continue
        d = agg[county]
        d["races"].add(r.get("race_key"))
        d["rows"] += 1
    out = [{"region": c, "races": len(d["races"]), "rows": d["rows"]} for c, d in agg.items()]
    out.sort(key=lambda x: -x["rows"])
    return out


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


def _streak(years):
    """Longest run of consecutive racing years (e.g. {2019,2020,2021,2024} -> 3)."""
    ys = sorted({y for y in years if y})
    if not ys:
        return 0
    best = run = 1
    for a, b in zip(ys, ys[1:]):
        run = run + 1 if b == a + 1 else 1
        best = max(best, run)
    return best


def build_records(records, top=8):
    """A 'records wall' of well-defined cold facts (the /insights page). Race-level
    facts need no identity; athlete-level facts use the TCU/UCI/name grouping and
    EXCLUDE low-confidence (high-homonym-risk) identities so a name collision can't
    falsely top a leaderboard. De-identified output (masked names + salted ids)."""
    fields = field_sizes(records)
    names = {}
    for r in records:
        rk = r.get("race_key")
        if rk and rk not in names:
            names[rk] = r.get("race_name_canonical") or rk

    big = sorted(((n, rk, y) for (rk, y), n in fields.items() if y), key=lambda t: -t[0])[:top]
    biggest_field = [{"rk": rk, "name": names.get(rk, rk), "y": y, "n": n} for n, rk, y in big]

    keys = build_group_keys(records)
    groups = defaultdict(list)
    for k, r in zip(keys, records):
        if k not in ("n:", "u:", "t:"):
            groups[k].append(r)

    ath = []
    for gk, recs in groups.items():
        if len(recs) < MIN_RESULTS:
            continue
        teams = {r.get("team") for r in recs if r.get("team")}
        genders = {r.get("gender") for r in recs if r.get("gender") in ("M", "F")}
        name_len = len([c for c in (recs[0].get("name_raw") or "") if not c.isspace()])
        if confidence(gk[0] in ("t", "u"), len(teams), name_len, mixed_gender=len(genders) > 1) == "low":
            continue
        per_race_years = defaultdict(set)
        for r in recs:
            if r.get("race_key") and r.get("year"):
                per_race_years[r["race_key"]].add(r["year"])
        lrk, lys = max(per_race_years.items(), key=lambda kv: len(kv[1])) if per_race_years else (None, set())
        ath.append({
            "id": athlete_id(gk), "nm": _masked(recs), "g": _mode_gender(recs),
            "n": len(recs), "wins": sum(1 for r in recs if r.get("rank_overall") == 1),
            "nr": len({r.get("race_key") for r in recs}),
            "streak": _streak([r.get("year") for r in recs]),
            "lrk": lrk, "lname": names.get(lrk, lrk), "lyears": len(lys),
        })

    def board(key, label_key="v"):
        return [{"id": a["id"], "nm": a["nm"], "g": a["g"], label_key: a[key]}
                for a in sorted(ath, key=lambda a: -a[key])[:top] if a[key] > 0]

    return {
        "biggest_field": biggest_field,
        "most_starts": board("n"),
        "most_wins": board("wins"),
        "most_races": board("nr"),
        "longest_streak": board("streak"),
        "most_loyal": [{"id": a["id"], "nm": a["nm"], "rk": a["lrk"], "name": a["lname"], "v": a["lyears"]}
                       for a in sorted(ath, key=lambda a: -a["lyears"])[:top] if a["lyears"] > 1],
    }


def main():
    records = list(common.iter_records(IN))  # RAM-frugal streaming parse
    insights = {
        "age_curve": build_age_curve(records),
        "breakout": build_breakout(records),
        "ratings": build_ratings(records),
        "geo": build_geo(records),
        "records": build_records(records),
    }
    with open(os.path.join(OUT, "insights.json"), "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, separators=(",", ":"))
    print("insights sections:", {k: len(v) for k, v in insights.items()})


if __name__ == "__main__":
    main()
