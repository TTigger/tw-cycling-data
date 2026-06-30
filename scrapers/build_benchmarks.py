# -*- coding: utf-8 -*-
"""Build /data/v1/benchmarks.json: per-race finish-time percentile breakpoints
by age/gender/category cohort. Reads master.public.json (only). Run before
build_manifest.py so the manifest's endpoint count/stats see it."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common      # noqa: E402
import benchmarks  # noqa: E402

IN = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "master.public.json")
OUT = os.path.join(common.PUBLIC_DATA_DIR, "benchmarks.json")


def main():
    idx = benchmarks.build_index(common.iter_records(IN))
    os.makedirs(common.PUBLIC_DATA_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, separators=(",", ":"))
    races = len(idx)
    cohorts = sum(len(r["cohorts"]) for r in idx.values())
    print(f"benchmarks: races={races} cohorts={cohorts} -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
