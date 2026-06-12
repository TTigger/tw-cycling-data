# -*- coding: utf-8 -*-
"""Build browser-ready data files from the master public dataset.

Reads  data/processed/master.public.json
Writes web/public/data/{viz.json, races.json, race/<race_key>__<year>.json}
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.public.json")
OUT = os.path.join(HERE, "..", "web", "public", "data")

_DIST_RE = re.compile(r"(\d{2,3})\s*(?:公里|[KkＫ]\s*[Mm]?|公?里)")

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
    """One entry per (race_key, year): name, series, count, multi-year flag, has_team."""
    agg = defaultdict(lambda: {"rows": 0, "team": False})
    years = defaultdict(set)
    meta = {}
    for r in records:
        key = (r.get("race_key"), r.get("year"))
        a = agg[key]
        a["rows"] += 1
        a["team"] = a["team"] or bool(r.get("team"))
        years[r.get("race_key")].add(r.get("year"))
        meta[r.get("race_key")] = {"rn": r.get("race_name_canonical"), "s": r.get("series")}
    out = []
    for (rk, y), a in agg.items():
        out.append({"rk": rk, "y": y, "rn": meta[rk]["rn"], "s": meta[rk]["s"],
                    "rows": a["rows"], "multi_year": len([x for x in years[rk] if x]) > 1,
                    "has_team": a["team"], "file": race_file_name(rk, y)})
    return sorted(out, key=lambda x: (-(x["rows"]), str(x["rk"])))


def race_file_name(rk, year):
    """Stable per-race-year filename stem; shared by main() and the races index
    so the frontend never recomputes the sanitization."""
    safe = re.sub(r"[^0-9A-Za-z一-鿿]+", "-", str(rk)).strip("-")
    return f"{safe}__{year}"


def detail_record(rec):
    """Per-race leaderboard row (de-identified)."""
    return {"rank": rec.get("rank_overall"), "bib": rec.get("bib"),
            "name": rec.get("name_masked"), "cat": rec.get("category_raw"),
            "g": rec.get("gender"), "ag": rec.get("age_group"),
            "team": rec.get("team"), "t": rec.get("finish_seconds"),
            "label": rec.get("result_label")}


def main():
    records = list(common.iter_records(IN))  # RAM-frugal streaming parse
    os.makedirs(os.path.join(OUT, "race"), exist_ok=True)
    viz = [slim_record(r) for r in records]
    with open(os.path.join(OUT, "viz.json"), "w", encoding="utf-8") as f:
        json.dump(viz, f, ensure_ascii=False, separators=(",", ":"))
    idx = build_races_index(records)
    with open(os.path.join(OUT, "races.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, separators=(",", ":"))
    groups = defaultdict(list)
    for r in records:
        groups[race_file_name(r.get("race_key"), r.get("year"))].append(r)
    for fname, rows in groups.items():
        rows = sorted([detail_record(x) for x in rows],
                      key=lambda x: (x["rank"] is None, x["rank"] or 0))
        with open(os.path.join(OUT, "race", f"{fname}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(f"viz={len(viz)} races={len(idx)} detailFiles={len(groups)} -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
