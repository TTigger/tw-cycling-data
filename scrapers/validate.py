# -*- coding: utf-8 -*-
"""
Data-quality validation for a processed dataset. Read-only; prints a report and
writes data/processed/_validation_<name>.json. Catches the failure modes recon
flagged: duplicates, bad time parsing, rank inversions, missing fields, year drift.

  python validate.py                                  # validates master.json
  python validate.py cyclist_2024_2026.json
"""
import json
import os
import re
import sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# plausible finish-time window: 8 min .. 60 h (upper bound allows multi-day
# round-the-island stage races like 瘋系列環台賽 with cumulative times >30h)
MIN_SEC, MAX_SEC = 8 * 60, 60 * 3600


def validate(name):
    path = os.path.join(OUT, name)
    d = json.load(open(path, encoding="utf-8"))
    issues = defaultdict(list)
    n = len(d)

    # 1) exact duplicate result rows
    seen = set()
    for r in d:
        k = (r.get("race_key"), r.get("year"), r.get("category_raw"), r.get("bib"), r.get("finish_time"))
        if k in seen:
            issues["duplicate_rows"].append(k)
        seen.add(k)

    # 2) missing critical fields
    for i, r in enumerate(d):
        if not r.get("finish_time"):
            issues["missing_finish_time"].append(i)
        if not r.get("name_masked") and not r.get("name_raw"):
            issues["missing_name"].append(i)
        if not r.get("race_name_canonical"):
            issues["missing_race"].append(i)

    # 3) finish-time parse / sanity
    for i, r in enumerate(d):
        s = r.get("finish_seconds")
        if r.get("finish_time") and s is None:
            issues["time_unparsed"].append(r.get("finish_time"))
        elif s is not None and not (MIN_SEC <= s <= MAX_SEC):
            issues["time_out_of_range"].append({"t": r.get("finish_time"), "s": s,
                                                "race": r.get("race_name_canonical")})

    # 4) rank inversions within (race_key, year, result_label): slower time at better rank
    groups = defaultdict(list)
    for r in d:
        if r.get("rank_overall") and r.get("finish_seconds") is not None:
            groups[(r["race_key"], r["year"], r.get("result_label"))].append(r)
    inversions = 0
    for g in groups.values():
        g.sort(key=lambda x: x["rank_overall"])
        prev = None
        for r in g:
            if prev is not None and r["finish_seconds"] + 1e-6 < prev:
                inversions += 1
            prev = max(prev, r["finish_seconds"]) if prev is not None else r["finish_seconds"]
    if inversions:
        issues["rank_time_inversions"] = [inversions]

    # 5) year drift: race name year vs year field (bound to 2009-2027 so product
    # names like "Wilier 2000" aren't misread as a year)
    for i, r in enumerate(d):
        ny = common.extract_year(r.get("race_name_raw") or "")
        if ny and not (2009 <= ny <= 2027):
            ny = None
        if ny and r.get("year") and ny != r["year"]:
            issues["year_mismatch"].append({"name_year": ny, "field_year": r["year"],
                                            "race": r.get("race_name_canonical")})

    # coverage stats
    by_src = Counter(r.get("source_platform") for r in d)
    gender_cov = {src: Counter(r.get("gender") for r in d if r.get("source_platform") == src)
                  for src in by_src}
    age_cov = {src: sum(1 for r in d if r.get("source_platform") == src and r.get("age_group"))
               for src in by_src}

    report = {
        "dataset": name, "records": n,
        "issue_counts": {k: len(v) for k, v in issues.items()},
        "samples": {k: v[:5] for k, v in issues.items()},
        "coverage": {
            "by_source": dict(by_src),
            "gender_by_source": {s: dict(c) for s, c in gender_cov.items()},
            "age_group_present_by_source": age_cov,
        },
    }
    out = os.path.join(OUT, f"_validation_{name}")
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"=== VALIDATE {name} ===  records={n}")
    if report["issue_counts"]:
        for k, v in sorted(report["issue_counts"].items(), key=lambda x: -x[1]):
            print(f"  ⚠ {k}: {v}")
    else:
        print("  ✓ no issues")
    print(f"  coverage by source: {dict(by_src)}")
    for s, c in gender_cov.items():
        tot = sum(c.values())
        known = tot - c.get(None, 0)
        print(f"    {s}: gender known {known}/{tot} ({100*known//tot if tot else 0}%), "
              f"age_group present {age_cov[s]}/{tot}")
    print(f"  -> {os.path.relpath(out)}")
    return report


if __name__ == "__main__":
    validate(sys.argv[1] if len(sys.argv) > 1 else "master.json")
