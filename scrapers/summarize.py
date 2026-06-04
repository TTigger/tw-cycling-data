# -*- coding: utf-8 -*-
"""Build a compact summary of a processed dataset (for QC + the viz layer)."""
import json
import os
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def summarize(path):
    d = json.load(open(path, encoding="utf-8"))
    races = defaultdict(lambda: {"rows": 0, "categories": set()})
    for r in d:
        k = f"{r['year']} {r['race_name_canonical']}"
        races[k]["rows"] += 1
        if r["category_raw"]:
            races[k]["categories"].add(r["category_raw"])
    summary = {
        "source": os.path.basename(path),
        "total_records": len(d),
        "years": sorted({r["year"] for r in d if r["year"]}),
        "distinct_races": len(races),
        "gender_dist": dict(Counter(r["gender"] for r in d)),
        "top_age_groups": dict(Counter(r["age_group"] for r in d if r["age_group"]).most_common(15)),
        "races": [
            {"race": k, "rows": v["rows"], "n_categories": len(v["categories"])}
            for k, v in sorted(races.items())
        ],
    }
    out = os.path.join(OUT, "cyclist_summary.json")
    json.dump(summary, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"records={summary['total_records']}  races={summary['distinct_races']}  "
          f"years={summary['years']}")
    print(f"gender={summary['gender_dist']}")
    print(f"\n{'race':<46}{'rows':>6}{'cats':>6}")
    for r in summary["races"]:
        print(f"  {r['race'][:44]:<44}{r['rows']:>6}{r['n_categories']:>6}")
    print(f"\n-> {os.path.relpath(out)}")


if __name__ == "__main__":
    summarize(sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "cyclist_2024_2026.json"))
