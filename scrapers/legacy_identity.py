# -*- coding: utf-8 -*-
"""Carry athlete identities across a source that started masking names.

Since 2026-H2 bravelog.tw shows only masked names ("黃*翔") everywhere, so a
re-crawl can no longer group its rows by real name. But every row we published
before that is already linked to an athlete id in web/public/data/v1/athlete/.
This module maps a result row -> its previously published athlete id via
(race_key, year, rounded finish seconds, masked name), which is unique in
practice. Rows that don't match (new races, or ambiguous keys) stay unlinked
rather than being guessed from a masked name.

  python scrapers/legacy_identity.py build [--ref HEAD]
      -> data/identity/legacy_athlete_map.json  (commit it; de-identified)

build_athletes.build_group_keys() applies the map to source-masked rows.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
MAP_PATH = os.path.join(ROOT, "data", "identity", "legacy_athlete_map.json")
MASTER = os.path.join(ROOT, "data", "processed", "master.json")
ATHLETE_DIR = "web/public/data/v1/athlete"


def is_source_masked(name):
    """The source itself hid the name (bravelog '黃*翔'), so it can't be grouped by name."""
    return bool(name) and ("*" in name or "＊" in name)


def entry_key(race_key, year, seconds, masked):
    if race_key is None or year is None or seconds is None or not masked:
        return None
    return f"{race_key}|{year}|{round(seconds)}|{masked}"


def row_key(r):
    return entry_key(r.get("race_key"), r.get("year"), r.get("finish_seconds"),
                     r.get("name_masked") or common.mask_name(r.get("name_raw")))


def _git_athlete_files(ref):
    """Yield parsed athlete/<id>.json files at a git ref (one cat-file process)."""
    ls = subprocess.run(["git", "ls-tree", "--name-only", f"{ref}:{ATHLETE_DIR}"],
                        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    p = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for name in ls:
        p.stdin.write(f"{ref}:{ATHLETE_DIR}/{name}\n".encode())
        p.stdin.flush()
        header = p.stdout.readline().split()
        size = int(header[2])
        body = p.stdout.read(size)
        p.stdout.read(1)  # trailing newline
        yield json.loads(body.decode("utf-8"))
    p.stdin.close()
    p.wait()


def build_map(ref, wanted_race_years=None):
    """{entry_key: athlete_id} from the athlete files at `ref`. Keys that point at
    two different athletes are dropped (ambiguous). Optionally restricted to
    (race_key, year) pairs we actually need."""
    out, ambiguous = {}, set()
    for a in _git_athlete_files(ref):
        for h in a.get("history", []):
            if wanted_race_years is not None and (h.get("rk"), h.get("y")) not in wanted_race_years:
                continue
            k = entry_key(h.get("rk"), h.get("y"), h.get("t"), a.get("nm"))
            if not k:
                continue
            if k in out and out[k] != a["id"]:
                ambiguous.add(k)
            out[k] = a["id"]
    for k in ambiguous:
        out.pop(k, None)
    return out, len(ambiguous)


_MAP = None


def load_map():
    global _MAP
    if _MAP is None:
        _MAP = json.load(open(MAP_PATH, encoding="utf-8")) if os.path.exists(MAP_PATH) else {}
    return _MAP


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--ref", default="HEAD", help="git ref holding the published athlete files")
    a = ap.parse_args()
    wanted = {(r.get("race_key"), r.get("year")) for r in common.iter_records(MASTER)
              if is_source_masked(r.get("name_raw"))}
    m, amb = build_map(a.ref, wanted)
    os.makedirs(os.path.dirname(MAP_PATH), exist_ok=True)
    json.dump(dict(sorted(m.items())), open(MAP_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    print(f"legacy athlete map: {len(m)} entries over {len(wanted)} race-years "
          f"({amb} ambiguous keys dropped) -> {os.path.relpath(MAP_PATH)}")


if __name__ == "__main__":
    main()
