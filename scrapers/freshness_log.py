# -*- coding: utf-8 -*-
"""Append a dated line to the local freshness log after a discover.py run and flag
races that newly appeared since the last logged run.

Used by the Windows scheduled task (scrapers/freshness_local.ps1): the cloud
routine's IP is 403'd by all three calendars, so a true calendar diff only works
on the local (TW) IP. This is pure local bookkeeping — it never scrapes, merges,
or pushes. Review missing_races.json and commit coverage.json yourself when you
decide to act on a new gap.
"""
import json
import os
from datetime import datetime

D = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "_discover")
cur = json.load(open(os.path.join(D, "missing_races.json"), encoding="utf-8"))

snap_path = os.path.join(D, "missing_snapshot.json")
prev_names = set()
if os.path.exists(snap_path):
    try:
        prev_names = {p["race"] for p in json.load(open(snap_path, encoding="utf-8"))}
    except Exception:
        pass

new = [m for m in cur if m["race"] not in prev_names]
untriaged = [m for m in cur if not m.get("status")]  # no KNOWN_TRIAGE verdict yet
stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
line = f"[{stamp}] 缺漏 {len(cur)} 場(未分流 {len(untriaged)})・本次新增 {len(new)} 場"

log = os.path.join(D, "freshness.log")
with open(log, "a", encoding="utf-8") as f:
    f.write(line + "\n")
    for m in new:
        f.write(f"    NEW {m['race']} -> {m['guess_source']}\n")

json.dump(cur, open(snap_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(line)
if new:
    print(f"  {len(new)} new race(s) need triage -> {os.path.relpath(log)}")
