# -*- coding: utf-8 -*-
"""Compare a rebuilt web/public/data/v1 against a git baseline (default: HEAD).

Run after `scrapers/rebuild_all.sh build` to decide whether a from-scratch
rebuild is safe to publish. Checks, per race-year: row counts, and the multiset
of (masked name, finish seconds) rows; plus athlete-id overlap (ids are salted
hashes of the identity key, so a faithful rebuild reproduces them).

Usage: python scrapers/compare_rebuild.py [--ref <git-ref>] [--json out.json]
"""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter

ROOT = os.path.join(os.path.dirname(__file__), "..")
V1 = "web/public/data/v1"
sys.stdout.reconfigure(encoding="utf-8")


def git_json(ref, path):
    try:
        out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT,
                             capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None
    return json.loads(out.decode("utf-8"))


def disk_json(path):
    p = os.path.join(ROOT, path)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def row_keys(rows):
    return Counter((r.get("name"), int(r["t"]) if r.get("t") is not None else None)
                   for r in rows or [])


def compare(ref):
    old_races = {(r["rk"], r["y"]): r for r in git_json(ref, f"{V1}/races.json")}
    new_races = {(r["rk"], r["y"]): r for r in disk_json(f"{V1}/races.json")}
    report = {"missing": [], "added": [], "changed": [], "same": 0}
    for key, o in sorted(old_races.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        n = new_races.get(key)
        if n is None:
            report["missing"].append({"race": key[0], "year": key[1], "rows": o["rows"]})
            continue
        if o["rows"] == n["rows"]:
            orows = git_json(ref, f"{V1}/race/{o['file']}.json")
            nrows = disk_json(f"{V1}/race/{n['file']}.json")
            if row_keys(orows) == row_keys(nrows):
                report["same"] += 1
                continue
            ok, nk = row_keys(orows), row_keys(nrows)
            diff = sum((ok - nk).values())
        else:
            diff = None
        report["changed"].append({"race": key[0], "year": key[1], "old": o["rows"],
                                  "new": n["rows"], "rows_not_reproduced": diff})
    for key, n in new_races.items():
        if key not in old_races:
            report["added"].append({"race": key[0], "year": key[1], "rows": n["rows"]})

    def ids(a):
        return {x["id"] for x in (a or [])} if isinstance(a, list) else set((a or {}).keys())
    oa, na = ids(git_json(ref, f"{V1}/athletes.json")), ids(disk_json(f"{V1}/athletes.json"))
    report["athletes"] = {"old": len(oa), "new": len(na), "kept": len(oa & na),
                          "lost": len(oa - na), "new_ids": len(na - oa)}
    report["rows"] = {"old": sum(r["rows"] for r in old_races.values()),
                      "new": sum(r["rows"] for r in new_races.values())}
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--json")
    a = ap.parse_args()
    r = compare(a.ref)
    print(f"rows: {r['rows']['old']} → {r['rows']['new']}")
    print(f"race-years identical: {r['same']}  changed: {len(r['changed'])}  "
          f"missing: {len(r['missing'])}  added: {len(r['added'])}")
    print(f"athletes: {r['athletes']}")
    for k in ("missing", "changed", "added"):
        for x in r[k]:
            print(f"  {k:<8} {x}")
    if a.json:
        json.dump(r, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
