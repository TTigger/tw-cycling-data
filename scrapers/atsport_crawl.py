# -*- coding: utf-8 -*-
"""ATSport 運計科技 (atsport.com.tw) — early cycling races it timed (2012–2020).

Mostly a triathlon timer, but its archive holds full public result lists for a
handful of road events we have nowhere else (戀戀197 2012–2019, 2012 環花東,
2013 金針山, 2018 全國公路錦標賽 youth time trials, 2020 Dan Cup criterium). Earlier attempts failed because the
site blocks overseas cloud IPs; it works from a Taiwan connection.

  /race/{id}?event_detail_id={course}&p={page}   20 rows per page, server-rendered

Each race's courses come from the page's course menu. Only rows with a finish
time are kept. Real-name HTML is cached in data/raw/atsport/ (gitignored).

  python scrapers/atsport_crawl.py
Output: data/processed/atsport_2012_2020.json
"""
import html as html_mod
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

BASE = "https://atsport.com.tw"
SOURCE = "atsport.com.tw"
ROOT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(ROOT, "data", "raw", "atsport")
OUT = os.path.join(ROOT, "data", "processed", "atsport_2012_2020.json")

# race id -> (race name, region). Names match later editions where they exist
# (戀戀197 2022+ is on bravelog), so all years share one race page.
RACES = {
    12: ("環花東國際自行車大賽", "花蓮縣"),
    19: ("戀戀197", "臺東縣"),
    27: ("戀戀197", "臺東縣"),
    28: ("金針山自行車登山賽", "臺東縣"),
    61: ("戀戀197", "臺東縣"),
    62: ("戀戀197", "臺東縣"),
    63: ("全國自由車公路錦標賽青少年計時賽", None),   # U13/U15 ITT + TTT only
    65: ("戀戀197", "臺東縣"),
    67: ("Dan Cup 桃園市主委盃公路繞圈賽", "桃園市"),
}
# Left out on purpose: 23 (2012 輪轉花東) returns the same list for its 100K and
# 200K courses, so the course of each row is unknowable; 66/68–70 (2020 Dan Cup)
# are off-road, balance-bike and kids' heats.

_COURSE = re.compile(r"event_detail_item\"[^>]*data-id='(\d+)'[^>]*data-name='([^']*)'\s*>\s*"
                     r"[^<(]*\((\d{4}-\d{2}-\d{2})\)")
_TITLE = re.compile(r"成績查詢</a>.*?(\d{4}-\d{2}-\d{2}).*?<[^>]*>\s*([^<]+?)\s*<", re.S)
_ROW = re.compile(r'class="score_detail_link.*?</a>', re.S)
_AGE = re.compile(r"[MWFmwf](\d{2})")


def _text(s):
    return html_mod.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_courses(page):
    """[(course_id, name, date)] from a race page's course menu."""
    seen, out = set(), []
    for cid, name, date in _COURSE.findall(page):
        if cid not in seen:
            seen.add(cid)
            out.append((cid, html_mod.unescape(name).strip(), date))
    return out


def parse_rows(page):
    """[{rank, name, bib, group, time}] for one results page."""
    out = []
    for blk in _ROW.findall(page):
        m = re.search(r"<h5>(.*?)</h5>", blk, re.S)
        if not m:
            continue
        name = _text(re.sub(r'<span class="row-no[^"]*">.*?</span>', "", m.group(1)))
        ps = [_text(p) for p in re.findall(r"<p>(.*?)</p>", blk, re.S)]
        rank = _text((re.search(r'rank-oa">\s*<b[^>]*>(.*?)</b>', blk, re.S) or [None, ""])[1])
        t = re.search(r'class="score-time">([^<]*)<', blk)
        out.append({"rank": int(rank) if rank.isdigit() else None, "name": name,
                    "bib": ps[0] if ps else None, "group": ps[1] if len(ps) > 1 and ps[1] else None,
                    "time": t.group(1).strip() if t else None})
    return out


def get(session, url):
    """Cached GET (pages hold real names, so the cache is gitignored)."""
    key = re.sub(r"[^\w]+", "_", url.split("//", 1)[1])
    path = os.path.join(CACHE, key + ".html")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    r = common.polite_get(session, url)
    r.raise_for_status()
    open(path, "w", encoding="utf-8").write(r.text)
    return r.text


def crawl_race(session, rid, scraped_at):
    race, region = RACES[rid]
    first = get(session, f"{BASE}/race/{rid}?p=1")
    out = []
    for cid, cname, date in parse_courses(first):
        year = int(date[:4])
        page, n = 1, 0
        while True:
            url = f"{BASE}/race/{rid}?event_detail_id={cid}&p={page}"
            rows = parse_rows(get(session, url))
            for r in rows:
                if not common.time_to_seconds(r["time"]):
                    continue
                age = _AGE.search(r["group"] or "")
                g = (r["group"] or "")[:1].upper()
                out.append(common.make_record(
                    source_platform=SOURCE, source_url=f"{BASE}/race/{rid}?event_detail_id={cid}",
                    source_format="web-table",
                    race_name_raw=f"{year} {race}", year=year, date=date,
                    race_type="cycling", region=region,
                    result_label=cname, category_raw=r["group"],
                    gender={"M": "M", "W": "F", "F": "F"}.get(g) or
                           ("F" if "女" in cname else "M" if "男" in cname else None),
                    age_group=age.group(1) if age else None,
                    rank_overall=r["rank"], bib=r["bib"], name_raw=r["name"],
                    finish_time=r["time"], scraped_at=scraped_at))
                n += 1
            if len(rows) < 20:
                break
            page += 1
        print(f"  {rid} {year} {race} / {cname}: {n} finishers")
    return out


def crawl(session=None):
    session = session or common.make_session()
    os.makedirs(CACHE, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = []
    for rid in RACES:
        out += crawl_race(session, rid, now)
    return out


def main():
    recs = crawl()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print(f"\n  {len(recs)} rows -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
