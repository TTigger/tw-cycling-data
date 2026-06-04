# -*- coding: utf-8 -*-
"""
Phase-1b crawler for Bravelog (bravelog.tw) — citizen/challenge cycling results.

Worklist: data/raw/bravelog_cycling_contests.json (from bravelog_calendar.py).
Per contest:  parse raceId <select> (sub-races) -> for each raceId paginate
?raceId=X&page=1..total (server-rendered HTML) -> parse athlete rows.
Per-contest result cache (resumable). Rate-limited.

Usage:
  python bravelog_calendar.py 2024 2025 2026   # build worklist first
  python bravelog_crawl.py                      # crawl all cycling contests
  python bravelog_crawl.py --limit 2            # smoke test first 2 contests
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.bravelog.tw/contest/rank"
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CACHE = os.path.join(RAW, "bravelog_by_contest")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# Per-athlete parsing uses a BOUNDED window (anchored on each athlete link) to
# avoid catastrophic regex backtracking across the whole 68KB page when a row's
# markup differs (e.g. a chevron-only link with no name/time div).
ATHLETE = re.compile(r'href="https://www\.bravelog\.tw/athlete/(\d+)/([0-9A-Za-z]+)"')
_NAME = re.compile(r'<div class="name">(.*?)</div>', re.S)
_DETAIL = re.compile(r'<div class="detail-info">(.*?)</div>', re.S)
_TIME = re.compile(r'<div class="time">\s*<span>\s*([0-9:]+)', re.S)
RACEOPT = re.compile(r'<option value="(\d+)"[^>]*>(.*?)</option>')
TOTAL = re.compile(r'data-total="(\d+)"')


def get(session, url):
    r = common.polite_get(session, url, delay=0.4)
    r.encoding = "utf-8"
    return r.text


def race_options(html):
    """sub-race (raceId) options from the <select name='raceId'> block."""
    m = re.search(r'(?s)<select name="raceId".*?</select>', html)
    if not m:
        return []
    return [(rid, re.sub(r"\s+", "", lbl)) for rid, lbl in RACEOPT.findall(m.group(0))]


def parse_rows(html):
    rows, seen = [], set()
    anchors = list(ATHLETE.finditer(html))
    for i, a in enumerate(anchors):
        # bounded window: from this athlete link to the next (or +1200 chars)
        end = anchors[i + 1].start() if i + 1 < len(anchors) else a.start() + 1200
        win = html[a.start():end]
        nm = _NAME.search(win)
        tm = _TIME.search(win)
        if not nm or not tm:                 # e.g. chevron-only link — skip
            continue
        key = (a.group(1), a.group(2))
        if key in seen:
            continue
        seen.add(key)
        dm = _DETAIL.search(win)
        spans = ([re.sub(r"\s+", "", s) for s in re.findall(r"<span[^>]*>(.*?)</span>", dm.group(1), re.S)]
                 if dm else [])
        rows.append({
            "race_id": a.group(1), "bib": spans[0] if spans else a.group(2),
            "name": re.sub(r"\s+", " ", nm.group(1)).strip(),
            "category": spans[1] if len(spans) > 1 else None,
            "gender_group": spans[2] if len(spans) > 2 else None,
            "finish": tm.group(1),
        })
    return rows


def crawl_contest(session, uid):
    """Return list of raw rows for a contest, across all sub-races + pages."""
    base = f"{BASE}/{uid}"
    html = get(session, base)
    opts = race_options(html)
    if not opts:                       # single-race contest: paginate base
        opts = [(None, None)]
    all_rows = []
    for rid, label in opts:
        first = get(session, f"{base}?raceId={rid}&page=1") if rid else get(session, f"{base}?page=1")
        tm = TOTAL.search(first)
        total = int(tm.group(1)) if tm else 1
        pages_html = [first] + [
            get(session, f"{base}?raceId={rid}&page={p}" if rid else f"{base}?page={p}")
            for p in range(2, total + 1)
        ]
        rid_rows = []
        for h in pages_html:
            rid_rows.extend(parse_rows(h))
        for i, r in enumerate(rid_rows, 1):       # order = rank within sub-race
            r["rank"] = i
            r["race_label"] = label or r.get("category")
        all_rows.extend(rid_rows)
    return all_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh", action="store_true", help="ignore per-contest cache")
    args = ap.parse_args()

    worklist = json.load(open(os.path.join(RAW, "bravelog_cycling_contests.json"), encoding="utf-8"))
    if args.limit:
        worklist = worklist[:args.limit]
    s = common.make_session()
    records = []
    stamp = "2026-06-04"

    for i, c in enumerate(worklist, 1):
        uid = c["uid"]
        year = common.extract_year(c.get("start_date") or "") or common.extract_year(uid[:4])
        date = (c.get("start_date") or "")[:10] or None
        cache = os.path.join(CACHE, f"{uid}.json")
        if os.path.exists(cache) and not args.refresh:
            rows = json.load(open(cache, encoding="utf-8"))
        else:
            try:
                rows = crawl_contest(s, uid)
            except Exception as e:
                print(f"[{i}/{len(worklist)}] {uid} ERROR {e}")
                continue
            json.dump(rows, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"[{i}/{len(worklist)}] {uid} {c['title'][:34]:<34} rows={len(rows)}")
        for r in rows:
            gender = common.gender_from_group(r.get("gender_group"))
            records.append(common.make_record(
                source_platform="bravelog.tw",
                source_url=f"{BASE}/{uid}",
                source_format="web-table",
                race_name_raw=c["title"], year=year, date=date,
                race_type="cycling", region=c.get("city"),
                result_label=r.get("race_label"), category_raw=r.get("category") or r.get("race_label"),
                gender=gender, age_group=None,
                rank_overall=r.get("rank"), bib=r.get("bib"),
                name_raw=r.get("name"), team=None,
                finish_time=r.get("finish"), scraped_at=stamp))

    # dedup + outputs
    deduped, seen = [], set()
    for r in records:
        k = (r["race_key"], r["year"], r["category_raw"], r["bib"], r["finish_time"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(r)
    records = deduped

    full = os.path.join(OUT_DIR, "bravelog_2024_2026.json")
    json.dump(records, open(full, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    pub = [{k: v for k, v in r.items() if k != "name_raw"} for r in records]
    json.dump(pub, open(os.path.join(OUT_DIR, "bravelog_2024_2026.public.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    races = {(r["race_key"], r["year"]) for r in records}
    gd = {}
    for r in records:
        gd[r["gender"]] = gd.get(r["gender"], 0) + 1
    print(f"\n=== DONE === records={len(records)} distinct races={len(races)}")
    print(f"  gender dist: {gd}")
    print(f"  -> {os.path.relpath(full)} (+ .public.json)")


if __name__ == "__main__":
    main()
