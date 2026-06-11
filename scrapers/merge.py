# -*- coding: utf-8 -*-
"""
Merge all source datasets into one master dataset, applying cross-source
normalization (race_class + series). Auto-discovers every source file matching
cyclist_*.json / bravelog_*.json / cycling_*.json (excluding .public + _summary),
so adding a new year range or source needs no edit here.

Outputs:
  data/processed/master.json         (full, internal — has name_raw)
  data/processed/master.public.json  (de-identified — for frontend/Vercel)
  data/processed/master_summary.json (stats for QC + viz)
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402
import normalize  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
SOURCE_PREFIXES = ("cyclist_", "bravelog_", "cycling_")


def discover_sources():
    """Every full source dataset: <source>_*.json minus .public.json / _summary.json."""
    out = []
    for p in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        b = os.path.basename(p)
        if b.startswith(SOURCE_PREFIXES) and not b.endswith((".public.json", "_summary.json")):
            out.append(p)
    return out


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    print(f"  loaded {len(d):>6}  {os.path.basename(p)}")
    return d


def main():
    print("merging sources:")
    records = []
    for p in discover_sources():
        records.extend(load(p))
    # drop zero-time DNF/未計時 noise (00:00:00) — not real finishes
    before = len(records)
    records = [r for r in records if r.get("finish_seconds") is None or r["finish_seconds"] > 0]
    if before - len(records):
        print(f"  dropped {before - len(records)} zero-time (DNF/未計時) rows")

    # cross-source exact-duplicate dedup: the same rider+year+finish-second
    # showing up in two platforms (e.g. a 96 race on both Bravelog and tsu).
    # Keeps the first-loaded source; tolerant to ms vs whole-second precision.
    before = len(records)
    seen, deduped = set(), []
    for r in records:
        fs = r.get("finish_seconds")
        k = (r.get("year"), r.get("name_raw"), int(fs) if fs else None)
        if r.get("name_raw") and fs and k in seen:
            continue
        if r.get("name_raw") and fs:
            seen.add(k)
        deduped.append(r)
    records = deduped
    if before - len(records):
        print(f"  dropped {before - len(records)} cross-source exact-duplicate rows")
    for r in records:
        normalize.enrich(r)
        # Re-mask at merge time so the de-identification policy is applied here,
        # not frozen at crawl time (lets us change mask_name without re-crawling).
        if r.get("name_raw"):
            r["name_masked"] = common.mask_name(r["name_raw"])

    full = os.path.join(OUT, "master.json")
    json.dump(records, open(full, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    pub = [{k: v for k, v in r.items() if k != "name_raw"} for r in records]
    json.dump(pub, open(os.path.join(OUT, "master.public.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # summary
    races = defaultdict(lambda: {"rows": 0, "years": set(), "series": None, "platform": None})
    for r in records:
        k = r["race_key"]
        races[k]["rows"] += 1
        races[k]["years"].add(r["year"])
        races[k]["series"] = r.get("series")
        races[k]["platform"] = r["source_platform"]
    summary = {
        "total_records": len(records),
        "by_platform": dict(Counter(r["source_platform"] for r in records)),
        "by_year": dict(sorted(Counter(r["year"] for r in records).items(), key=lambda x: str(x[0]))),
        "by_gender": dict(Counter(r["gender"] for r in records)),
        "by_race_class": dict(Counter(r["race_class"] for r in records)),
        "by_series": dict(Counter(r["series"] for r in records).most_common()),
        "distinct_races": len(races),
        "races": [
            {"race_key": k, "series": v["series"], "platform": v["platform"],
             "years": sorted(y for y in v["years"] if y), "rows": v["rows"]}
            for k, v in sorted(races.items(), key=lambda x: -x[1]["rows"])
        ],
    }
    json.dump(summary, open(os.path.join(OUT, "master_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print(f"\n=== MASTER === records={summary['total_records']}  races={summary['distinct_races']}")
    print(f"  platform: {summary['by_platform']}")
    print(f"  year:     {summary['by_year']}")
    print(f"  gender:   {summary['by_gender']}")
    print(f"  class:    {summary['by_race_class']}")
    print(f"  series ({len(summary['by_series'])}):")
    for k, v in list(summary["by_series"].items())[:20]:
        print(f"     {v:>6}  {k}")
    print(f"\n  -> master.json (+ .public.json, master_summary.json)")


if __name__ == "__main__":
    main()
