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
SOURCE_PREFIXES = ("criterium_", "cyclist_", "bravelog_", "cycling_", "irunner_",
                   "focusline_", "taiwanbike_")


def discover_sources():
    """Every full source dataset: <source>_*.json minus .public.json / _summary.json."""
    out = []
    for p in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        b = os.path.basename(p)
        if b.startswith(SOURCE_PREFIXES) and not b.endswith((".public.json", "_summary.json")):
            out.append(p)
    return out


# Races superseded by a better source — their rows are skipped at merge.
# bravelog's combined 2025 TBA cert (北高360+雙塔520+四極602 in one race_key) is
# replaced by taiwanbike.org's authoritative per-distance results.
SUPERSEDED = {("bravelog.tw", "TBA北高360雙塔520四極602自行車認證")}

iter_records = common.iter_records  # streaming JSON-array reader (RAM-frugal)


def should_drop_zero_time(r):
    """Drop genuine zero/negative-time noise, but KEEP explicit DNF/DNS rows —
    criterium.tw reports non-finishers, which legitimately have no finish time."""
    if r.get("status") in ("DNF", "DNS"):
        return False
    fs = r.get("finish_seconds")
    return fs is not None and fs <= 0


def main():
    print("merging sources (streaming):")
    import gc
    mf = open(os.path.join(OUT, "master.json"), "w", encoding="utf-8")
    pf = open(os.path.join(OUT, "master.public.json"), "w", encoding="utf-8")
    mf.write("[\n")
    pf.write("[\n")

    # Stream one source at a time: filter → cross-source dedup → enrich → re-mask →
    # write each record straight to disk, then free the source. Peak memory stays at
    # ~one source instead of the whole corpus (RAM-tight machines OOM'd otherwise).
    # Dedup keeps the first-loaded source (sources load in sorted-glob order, as before).
    seen = set()
    n_out = n_zero = n_dup = n_superseded = 0
    races = defaultdict(lambda: {"rows": 0, "years": set(), "series": None, "platform": None})
    by_platform, by_year, by_gender, by_class, by_series = (Counter() for _ in range(5))
    by_status = Counter()

    for p in discover_sources():
        src_n = 0
        for r in iter_records(p):
            src_n += 1
            fs = r.get("finish_seconds")
            if should_drop_zero_time(r):      # zero-time noise, but keep DNF/DNS
                n_zero += 1
                continue
            if r.get("name_raw") and fs:        # cross-source exact-dup dedup
                k = (r.get("year"), r.get("name_raw"), int(fs))
                if k in seen:
                    n_dup += 1
                    continue
                seen.add(k)
            normalize.enrich(r)
            if (r["source_platform"], r["race_key"]) in SUPERSEDED:
                n_superseded += 1
                continue
            if r.get("name_raw"):               # re-mask at merge time (policy applied here)
                r["name_masked"] = common.mask_name(r["name_raw"])
            rk = r["race_key"]
            races[rk]["rows"] += 1
            races[rk]["years"].add(r["year"])
            races[rk]["series"] = r.get("series")
            races[rk]["platform"] = r["source_platform"]
            by_platform[r["source_platform"]] += 1
            by_year[r["year"]] += 1
            by_gender[r["gender"]] += 1
            by_class[r["race_class"]] += 1
            by_series[r["series"]] += 1
            by_status[r.get("status")] += 1
            sep = ",\n" if n_out else ""
            mf.write(sep)
            json.dump(r, mf, ensure_ascii=False)
            r.pop("name_raw", None)             # public: de-identified
            pf.write(sep)
            json.dump(r, pf, ensure_ascii=False)
            n_out += 1
        print(f"  loaded {src_n:>6}  {os.path.basename(p)}")
        gc.collect()

    mf.write("\n]\n"); mf.close()
    pf.write("\n]\n"); pf.close()
    if n_zero:
        print(f"  dropped {n_zero} zero-time (DNF/未計時) rows")
    if n_dup:
        print(f"  dropped {n_dup} cross-source exact-duplicate rows")
    if n_superseded:
        print(f"  dropped {n_superseded} superseded rows (bravelog races replaced by a better source)")

    summary = {
        "total_records": n_out,
        "by_platform": dict(by_platform),
        "by_year": dict(sorted(by_year.items(), key=lambda x: str(x[0]))),
        "by_gender": dict(by_gender),
        "by_race_class": dict(by_class),
        "by_series": dict(by_series.most_common()),
        "by_status": dict(by_status),
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
