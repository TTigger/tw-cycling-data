# -*- coding: utf-8 -*-
"""Last-resort restore of one source's rows from the published open dataset.

For when a source site is down during a from-scratch rebuild (criterium.tw
returned Cloudflare 525 in 2026-11). The open dataset is de-identified, so:
  * name_raw is the published masked name with ○ -> * — i.e. it is marked as
    source-masked, and build_athletes re-attaches it to the athlete id we already
    published (legacy_identity) instead of grouping by a masked name;
  * per-row DNF/DNS status was never published, so non-finishers (no time) get
    status "NF" (did not finish, type unknown) — we do not guess which was which.
Re-crawl the source as soon as it is back; this is a stopgap, labelled via
source_format="restored:<release tag>".

  python scrapers/restore_from_release.py <dataset.json.gz> --source criterium.tw \
      --tag dataset-v2026.06.30.1 --out criterium_restored.json
  # only the rows a re-crawl could not reproduce:
  python scrapers/restore_from_release.py <dataset.json.gz> --source irunner.biji.co \
      --tag dataset-v2026.06.30.1 --out irunner_restored.json \
      --missing-from data/processed/irunner_20*.json
"""
import argparse
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def restore(rows, source, tag):
    out = []
    for r in rows:
        if r.get("source_platform") != source:
            continue
        masked = r.get("name_masked")
        has_time = r.get("finish_seconds") is not None
        out.append(common.make_record(
            source_platform=source, source_format=f"restored:{tag}",
            race_name_raw=r.get("race_name_canonical"),
            race_name_canonical=r.get("race_name_canonical"), race_key=r.get("race_key"),
            year=r.get("year"), date=r.get("date"), region=r.get("region"),
            race_type=r.get("race_type"),
            result_label=r.get("result_label"), category_raw=r.get("category_raw"),
            gender=r.get("gender"), age_group=r.get("age_group"),
            rank_overall=r.get("rank_overall"), team=r.get("team"),
            name_raw=masked.replace("○", "*") if masked else None, name_masked=masked,
            finish_time=r.get("finish_time"), finish_seconds=r.get("finish_seconds"),
            splits=r.get("splits"),
            status=("FIN" if has_time else "NF") if source == "criterium.tw" else None))
    return out


def crawled_keys(paths):
    """(race_key, year, masked name, whole seconds) of rows a fresh crawl produced."""
    keys = set()
    for p in paths:
        for r in common.iter_records(p):
            fs = r.get("finish_seconds")
            if fs is None:
                continue
            keys.add((r.get("race_key"), r.get("year"),
                      r.get("name_masked") or common.mask_name(r.get("name_raw")), int(fs)))
    return keys


def missing_only(restored, crawled):
    """Keep only published rows the re-crawl could not reproduce (e.g. iRunner
    finishers its search no longer returns)."""
    return [r for r in restored if r.get("finish_seconds") is not None and
            (r["race_key"], r["year"], r["name_masked"], int(r["finish_seconds"])) not in crawled]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", help="tw-cycling-results.json.gz from a dataset release")
    ap.add_argument("--source", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--missing-from", nargs="+", metavar="PROCESSED_JSON",
                    help="only restore rows absent from these freshly crawled files")
    a = ap.parse_args()
    rows = json.load(gzip.open(a.dataset, "rt", encoding="utf-8"))
    out = restore(rows, a.source, a.tag)
    if a.missing_from:
        out = missing_only(out, crawled_keys(a.missing_from))
    path = os.path.join(OUT_DIR, a.out)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"restored {len(out)} {a.source} rows from {a.tag} -> {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
