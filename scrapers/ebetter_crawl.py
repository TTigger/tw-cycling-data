# -*- coding: utf-8 -*-
"""伊貝特 (e-better) results site, gr.e-better.com.tw.

伊貝特 runs registration (bao-ming.com, behind a bot check we do not bypass) and
also chip timing. Its results site is separate and public:
  GET  /eb/gr/{sn}           -> page (title "成績查詢 - <event>") + session cookie
  POST /eb/gr/{sn}/getList   -> JSON {data: {datas: [...]}} 100 rows per page

The site only keeps recent events: older result pages are taken down after a
few months. So every pull is cached in data/raw/ebetter/<sn>.json (gitignored,
real names) and a cached event is never re-fetched; the build reads the cache.

Worklist: data/raw/ebetter_events.json (committed, no personal data). Find new
events with `--scan LO HI` (prints cycling events in that sn range; add them to
the worklist by hand with the race name used for earlier editions).

  python scrapers/ebetter_crawl.py              # fetch missing events + build
  python scrapers/ebetter_crawl.py --scan 7000 7300
Output: data/processed/ebetter_2026.json
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

BASE = "https://gr.e-better.com.tw/eb/gr"
SOURCE = "e-better.com.tw"
ROOT = os.path.join(os.path.dirname(__file__), "..")
WORKLIST = os.path.join(ROOT, "data", "raw", "ebetter_events.json")
CACHE = os.path.join(ROOT, "data", "raw", "ebetter")
OUT = os.path.join(ROOT, "data", "processed", "ebetter_2026.json")
PAGE = 100

# CJK counts as a word character, so "280KM雙城" has no \b after KM: match the
# distance without a word boundary. Series names cover titles with no cycling word.
CYCLING = re.compile(r"自行車|單車|公路|武嶺|騎|bike|GIANT|LIVDAY|KOM|雪巴|大滿貫|瘋系列|環台|"
                     r"Wilier|\d{2,3}\s*K(?:M)?(?![A-Za-z])", re.I)
NOT_CYCLING = re.compile(r"鐵人|三項|馬拉松|路跑|健走|越野|Run\b", re.I)
_AGE = re.compile(r"[MWFmwf](\d{2})")
_TITLE = re.compile(r"<title>\s*成績查詢\s*-\s*(.*?)\s*</title>", re.S)


def gender_of(row):
    """gender_ is "1" male / "0" female. Some events never fill it in (all "1"),
    so the worklist can switch it off per event (gender: false)."""
    return {"1": "M", "0": "F"}.get(str(row.get("gender_") or ""))


def build_records(rows, ev, scraped_at):
    """Unified records for one event's timed finishers."""
    out = []
    for r in rows:
        if str(r.get("canceled_") or "0") != "0":
            continue
        t = (r.get("result_") or "").strip()
        if not common.time_to_seconds(t):
            continue
        group = (r.get("subgroup_title_") or "").strip() or None
        age = _AGE.search(group or "")
        rank = str(r.get("rank_") or "")
        out.append(common.make_record(
            source_platform=SOURCE, source_url=f"{BASE}/{ev['sn']}", source_format="json",
            race_name_raw=f"{ev['year']} {ev['race']}", year=ev["year"], date=ev.get("date"),
            race_type="cycling", region=ev.get("region"),
            result_label=(r.get("group_title_") or "").strip() or None, category_raw=group,
            gender=gender_of(r) if ev.get("gender", True) else None, age_group=age.group(1) if age else None,
            rank_overall=int(rank) if rank.isdigit() and int(rank) > 0 else None,
            bib=(r.get("runner_num_") or "").strip() or None,
            team=(r.get("team_") or "").strip() or None,
            name_raw=(r.get("name_") or "").strip() or None,
            finish_time=t, scraped_at=scraped_at))
    return out


def title_of(session, sn):
    r = session.get(f"{BASE}/{sn}", timeout=40)
    m = _TITLE.search(r.text) if r.ok else None
    return m.group(1).strip() if m else None


def fetch_rows(session, sn):
    """All rows of one event (the GET first sets the session cookie)."""
    if not title_of(session, sn):
        raise RuntimeError(f"e-better {sn}: no results page (taken down?)")
    rows, page = [], 1
    headers = {"X-Requested-With": "XMLHttpRequest", "Referer": f"{BASE}/{sn}"}
    while True:
        form = {"group": 0, "subgroup": 0, "runnerNum": "", "name": "", "teamName": "",
                "pageNum": page, "pageSize": PAGE}
        r = session.post(f"{BASE}/{sn}/getList", data=form, headers=headers, timeout=40)
        r.raise_for_status()
        common.archive_response(f"{BASE}/{sn}/getList?pageNum={page}", r.content)
        batch = ((r.json().get("data") or {}).get("datas")) or []
        rows += batch
        if len(batch) < PAGE:
            return rows
        page += 1
        time.sleep(0.6)


def load_worklist():
    return json.load(open(WORKLIST, encoding="utf-8"))


def crawl(session=None):
    session = session or common.make_session()
    os.makedirs(CACHE, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = []
    for ev in load_worklist():
        path = os.path.join(CACHE, f"{ev['sn']}.json")
        if os.path.exists(path):
            rows = json.load(open(path, encoding="utf-8"))
        else:
            rows = fetch_rows(session, ev["sn"])
            json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        recs = build_records(rows, ev, now)
        print(f"  {ev['sn']} {ev['year']} {ev['race']}: {len(rows)} rows, {len(recs)} finishers")
        out += recs
    return out


def scan(lo, hi):
    """Print cycling-looking events with a live results page in sn range [lo, hi]."""
    s = common.make_session()
    known = {e["sn"] for e in load_worklist()}
    for sn in range(lo, hi + 1):
        try:
            t = title_of(s, sn)
        except Exception:
            t = None
        if t and CYCLING.search(t) and not NOT_CYCLING.search(t):
            print(f"  {sn}{' (in worklist)' if sn in known else ''}  {t}")
        time.sleep(0.4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", nargs=2, type=int, metavar=("LO", "HI"))
    a = ap.parse_args()
    if a.scan:
        return scan(*a.scan)
    recs = crawl()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print(f"\n  {len(recs)} rows -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
