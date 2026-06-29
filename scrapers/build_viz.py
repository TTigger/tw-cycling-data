# -*- coding: utf-8 -*-
"""Build browser-ready data files from the master public dataset.

Reads  data/processed/master.public.json
Writes web/public/data/{viz.json, races.json, race/<race_key>__<year>.json}
"""
import json
import os
import re
import sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.public.json")
OUT = os.path.join(HERE, "..", "web", "public", "data")

_DIST_RE = re.compile(r"(\d{2,3})\s*(?:公里|[KkＫ]\s*[Mm]?|公?里)")


def is_finisher(r):
    """A row that belongs in finisher-only views (leaderboards, histograms).
    Non-FIN status rows (criterium.tw) carry no finish time and are excluded there;
    they are still counted for completion in build_races_index."""
    return r.get("status") in (None, "FIN")

def extract_distance_km(category_raw, result_label, race_name):
    """Pull a race distance in km from any of the label fields. None if absent."""
    for field in (category_raw, result_label, race_name):
        if not field:
            continue
        m = _DIST_RE.search(str(field))
        if m:
            km = int(m.group(1))
            if 5 <= km <= 700:
                return km
    return None


def avg_speed_kmh(distance_km, finish_seconds):
    """km/h from distance + elapsed seconds. None if missing or implausible (>80km/h)."""
    if not distance_km or not finish_seconds or finish_seconds <= 0:
        return None
    spd = distance_km / (finish_seconds / 3600)
    if spd > 80:
        return None
    return round(spd, 1)


def month_of(date_str):
    """Extract the month (1-12) from a YYYY-MM... date string. None if absent/unparseable."""
    if not date_str:
        return None
    m = re.match(r"\d{4}-(\d{2})", str(date_str))
    return int(m.group(1)) if m else None


def slim_record(rec):
    """Project a master record to the compact browser shape (short keys)."""
    dist = extract_distance_km(rec.get("category_raw"), rec.get("result_label"),
                               rec.get("race_name_raw") or rec.get("race_name_canonical"))
    t = rec.get("finish_seconds")
    # Note: here `t` is cast to int for histogram bucketing in the viz layer;
    # detail_record intentionally keeps the float finish_seconds for precise
    # leaderboard time display.
    return {
        "rk": rec.get("race_key"),
        "y": rec.get("year"), "mon": month_of(rec.get("date")),
        "s": rec.get("series"), "rc": rec.get("race_class"),
        "cat": rec.get("category_raw"), "g": rec.get("gender"),
        # normalized decade band (U19/19-29/.../60+/MASTER) for clean filter +
        # boxplot grouping; raw age_group is kept in the per-race detail rows.
        "ag": rec.get("age_band"),
        "t": int(t) if t is not None else None, "rank": rec.get("rank_overall"),
        "dist": dist, "spd": avg_speed_kmh(dist, t),
        "plat": rec.get("source_platform"), "reg": rec.get("region"),
    }


def build_races_index(records):
    """One entry per (race_key, year): name, series, count, multi-year flag,
    has_team, and completion (fin/total/rate/counts) when status data exists."""
    agg = defaultdict(lambda: {"rows": 0, "team": False,
                               "fin": 0, "status_rows": 0, "counts": Counter()})
    years = defaultdict(set)
    meta = {}
    for r in records:
        key = (r.get("race_key"), r.get("year"))
        a = agg[key]
        if is_finisher(r):
            a["rows"] += 1
        a["team"] = a["team"] or bool(r.get("team"))
        st = r.get("status")
        if st:
            a["status_rows"] += 1
            a["counts"][st] += 1
            if st == "FIN":
                a["fin"] += 1
        years[r.get("race_key")].add(r.get("year"))
        meta[r.get("race_key")] = {"rn": r.get("race_name_canonical"), "s": r.get("series")}
    out = []
    for (rk, y), a in agg.items():
        entry = {"rk": rk, "y": y, "rn": meta[rk]["rn"], "s": meta[rk]["s"],
                 "rows": a["rows"], "multi_year": len([x for x in years[rk] if x]) > 1,
                 "has_team": a["team"], "file": race_file_name(rk, y)}
        if a["status_rows"]:
            total = a["status_rows"]
            entry["completion"] = {
                "fin": a["fin"],
                "total": total,
                "rate": round(a["fin"] / total, 3) if total else 0.0,
                "counts": dict(a["counts"]),
            }
        out.append(entry)
    return sorted(out, key=lambda x: (-(x["rows"]), str(x["rk"])))


def race_file_name(rk, year):
    """Stable per-race-year filename stem; shared by main() and the races index
    so the frontend never recomputes the sanitization."""
    safe = re.sub(r"[^0-9A-Za-z一-鿿]+", "-", str(rk)).strip("-")
    return f"{safe}__{year}"


def _quantile(sorted_vals, q):
    """Linear-interpolated quantile — matches web/src/lib/aggregate.ts quantile()."""
    n = len(sorted_vals)
    if n == 0:
        return float("nan")
    if n == 1:
        return sorted_vals[0]
    pos = (n - 1) * q
    base = int(pos)
    rest = pos - base
    nxt = sorted_vals[base + 1] if base + 1 < n else None
    return sorted_vals[base] + rest * (nxt - sorted_vals[base]) if nxt is not None else sorted_vals[base]


def build_overview(viz, top_n=8, women_min=50):
    """Precompute the homepage aggregates so the landing page no longer downloads
    the full 24MB viz.json. Mirrors web/src/lib/overview.ts (kpiStats /
    monthYearHeat / trendByYearSeries / womenShareBySeries / compositionByClass)."""
    races, series = set(), set()
    mn, mx = None, None
    for r in viz:
        if r["rk"]:
            races.add(r["rk"])
        if r["s"]:
            series.add(r["s"])
        if r["y"] is not None:
            mn = r["y"] if mn is None else min(mn, r["y"])
            mx = r["y"] if mx is None else max(mx, r["y"])
    kpi = {"records": len(viz), "races": len(races), "series": len(series),
           "minYear": mn, "maxYear": mx}

    years = sorted({r["y"] for r in viz if r["y"] is not None})
    yi = {y: i for i, y in enumerate(years)}

    # heat: month x year people-count
    grid = defaultdict(int)
    for r in viz:
        if r["mon"] is None or r["y"] is None:
            continue
        grid[(r["mon"], r["y"])] += 1
    cells = [[m - 1, yi[y], c] for (m, y), c in grid.items()]
    heat = {"years": years, "cells": cells, "max": max((c for *_, c in cells), default=0)}

    # trend: stacked participation by year, top-N series (+ 其他)
    totals = defaultdict(int)
    for r in viz:
        totals[r["s"] or "其他"] += 1
    top = [s for s, _ in sorted(totals.items(), key=lambda e: -e[1])[:top_n]]
    top_set = set(top)
    counts = {s: [0] * len(years) for s in [*top, "其他"]}
    for r in viz:
        if r["y"] is None:
            continue
        s = r["s"] or "其他"
        counts[s if s in top_set else "其他"][yi[r["y"]]] += 1
    if all(c == 0 for c in counts["其他"]):
        del counts["其他"]
    trend = {"years": years, "series": list(counts.keys()), "counts": counts}

    # women share by series (sample >= women_min)
    wg = defaultdict(lambda: {"f": 0, "t": 0})
    for r in viz:
        if r["g"] not in ("M", "F"):
            continue
        e = wg[r["s"] or "其他"]
        if r["g"] == "F":
            e["f"] += 1
        e["t"] += 1
    women = sorted(
        ({"series": s, "f": e["f"], "total": e["t"], "pct": round(100 * e["f"] / e["t"])}
         for s, e in wg.items() if e["t"] >= women_min),
        key=lambda w: -w["total"])

    # composition by race_class x gender
    cg = defaultdict(lambda: {"m": 0, "f": 0, "u": 0})
    for r in viz:
        e = cg[r["rc"] or "未分類"]
        e["m" if r["g"] == "M" else "f" if r["g"] == "F" else "u"] += 1
    classes = sorted(cg.keys(), key=lambda c: -(cg[c]["m"] + cg[c]["f"] + cg[c]["u"]))
    composition = {"classes": classes,
                   "male": [cg[c]["m"] for c in classes],
                   "female": [cg[c]["f"] for c in classes],
                   "unknown": [cg[c]["u"] for c in classes]}

    return {"kpi": kpi, "heat": heat, "trend": trend, "women": women,
            "composition": composition}


def build_crossyear(viz):
    """Per-race cross-year winner/median finish time, so the race page no longer
    loads the full viz.json just to chart one race. Mirrors racedetail.crossYear."""
    by = defaultdict(lambda: defaultdict(list))   # rk -> y -> [t]
    for r in viz:
        if r["rk"] and r["y"] is not None and r["t"] is not None:
            by[r["rk"]][r["y"]].append(r["t"])
    out = {}
    for rk, years in by.items():
        if len(years) < 2:                        # cross-year card needs >=2 years
            continue
        rows = []
        for y in sorted(years):
            ts = sorted(years[y])
            rows.append({"y": y, "winner": ts[0], "median": round(_quantile(ts, 0.5))})
        out[rk] = rows
    return out


def detail_record(rec):
    """Per-race leaderboard row (de-identified)."""
    return {"rank": rec.get("rank_overall"), "bib": rec.get("bib"),
            "name": rec.get("name_masked"), "cat": rec.get("category_raw"),
            "g": rec.get("gender"), "ag": rec.get("age_group"),
            "team": rec.get("team"), "t": rec.get("finish_seconds"),
            "label": rec.get("result_label")}


def main():
    records = list(common.iter_records(IN))  # RAM-frugal streaming parse
    finishers = [r for r in records if is_finisher(r)]
    os.makedirs(os.path.join(OUT, "race"), exist_ok=True)
    viz = [slim_record(r) for r in finishers]
    with open(os.path.join(OUT, "viz.json"), "w", encoding="utf-8") as f:
        json.dump(viz, f, ensure_ascii=False, separators=(",", ":"))
    idx = build_races_index(records)
    with open(os.path.join(OUT, "races.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(OUT, "overview.json"), "w", encoding="utf-8") as f:
        json.dump(build_overview(viz), f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(OUT, "race_crossyear.json"), "w", encoding="utf-8") as f:
        json.dump(build_crossyear(viz), f, ensure_ascii=False, separators=(",", ":"))
    groups = defaultdict(list)
    for r in finishers:
        groups[race_file_name(r.get("race_key"), r.get("year"))].append(r)
    for fname, rows in groups.items():
        rows = sorted([detail_record(x) for x in rows],
                      key=lambda x: (x["rank"] is None, x["rank"] or 0))
        with open(os.path.join(OUT, "race", f"{fname}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(f"viz={len(viz)} races={len(idx)} detailFiles={len(groups)} -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
