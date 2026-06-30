# -*- coding: utf-8 -*-
"""Build the public open dataset release assets from master.public.json:
tw-cycling-results.csv.gz, .json.gz, datapackage.json, CHECKSUMS.txt -> data/dist/.
Whitelist projection via dataset.project_row. Does NOT publish a release."""
import csv
import gzip
import hashlib
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
import common   # noqa: E402
import dataset  # noqa: E402

IN = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "master.public.json")
DIST = os.path.join(os.path.dirname(__file__), "..", "data", "dist")
CSV_NAME = "tw-cycling-results.csv.gz"
JSON_NAME = "tw-cycling-results.json.gz"
REPO = "https://github.com/TTigger/tw-cycling-data"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(records, out_dir, version):
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, CSV_NAME)
    json_path = os.path.join(out_dir, JSON_NAME)

    count = 0
    with gzip.open(csv_path, "wt", encoding="utf-8", newline="") as cf, \
            gzip.open(json_path, "wt", encoding="utf-8") as jf:
        w = csv.writer(cf)
        w.writerow(dataset.PUBLISH_COLUMNS)
        jf.write("[")
        for row in records:
            p = dataset.project_row(row)
            w.writerow([dataset.csv_value(p[c]) for c in dataset.PUBLISH_COLUMNS])
            jf.write(("," if count else "") + json.dumps(p, ensure_ascii=False))
            count += 1
        jf.write("]")

    files = {}
    for name in (CSV_NAME, JSON_NAME):
        path = os.path.join(out_dir, name)
        files[name] = {"bytes": os.path.getsize(path), "sha256": _sha256(path)}

    datapackage = {
        "name": "tw-cycling-results",
        "title": "Taiwan road-cycling race results (de-identified)",
        "version": version,
        "homepage": REPO,
        "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/"}],
        "attribution": f"tw-cycling-data ({REPO})",
        "contact": f"{REPO}/issues",
        "count": count,
        "resources": [
            {"path": CSV_NAME, "format": "csv", "compression": "gz",
             "bytes": files[CSV_NAME]["bytes"], "hash": files[CSV_NAME]["sha256"],
             "schema": {"fields": [{"name": n, "type": t, "description": d}
                                   for n, t, d in dataset.FIELDS]}},
            {"path": JSON_NAME, "format": "json", "compression": "gz",
             "bytes": files[JSON_NAME]["bytes"], "hash": files[JSON_NAME]["sha256"]},
        ],
    }
    with open(os.path.join(out_dir, "datapackage.json"), "w", encoding="utf-8") as f:
        json.dump(datapackage, f, ensure_ascii=False, indent=1)

    with open(os.path.join(out_dir, "CHECKSUMS.txt"), "w", encoding="utf-8") as f:
        for name in (CSV_NAME, JSON_NAME):
            f.write(f"{files[name]['sha256']}  {name}\n")

    return {"count": count, "files": files}


def main():
    version = datetime.now().strftime("%Y.%m.%d")
    summary = build(common.iter_records(IN), DIST, version)
    print(f"dataset v{version}: rows={summary['count']} -> {os.path.relpath(DIST)}")
    for name, info in summary["files"].items():
        print(f"  {name}: {info['bytes'] // 1024} KB  sha256={info['sha256'][:12]}…")


if __name__ == "__main__":
    main()
