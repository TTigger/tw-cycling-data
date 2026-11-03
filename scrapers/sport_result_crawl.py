# -*- coding: utf-8 -*-
"""Dynamic Intelligences results site (raceresult.sport-result.com).

Since 2026 this timing company publishes full results through a small JSON API:
  /api/contests                                   -> every contest (all sports)
  /api/contests/{slug}                            -> one contest's courses/groups
  /api/contests/{slug}/results?page=N&pageSize=200 -> {rows,total,page,pageSize}

It times the 96 league and L'Étape 日月潭. For 96 武嶺 2026 it has the full
競賽組 + 市民競賽組 field, which the organizer's PDF (sporter96_pdf.py) only
partly covers, so merge.py marks that PDF race-year as superseded.

Row status: "0" = finished with a time. "1" = no time (the PDF splits these
into DNF and DNS, this API doesn't) and "3" is undocumented, so only finishers
are kept.

Raw responses (real names) are cached in data/raw/sport_result/<slug>.json
(gitignored). If the site is unreachable, the cache is used instead.

  python scrapers/sport_result_crawl.py
Output: data/processed/sport_result_2026.json
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

BASE = "https://raceresult.sport-result.com"
SOURCE = "sport-result.com"
ROOT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(ROOT, "data", "raw", "sport_result")
OUT = os.path.join(ROOT, "data", "processed", "sport_result_2026.json")
PAGE = 200  # the API's maximum page size

CYCLING = re.compile(r"自行車|單車|公路|武嶺|96聯賽|96Heroes|KOM|登山王|騎", re.I)
NOT_CYCLING = re.compile(r"鐵人|三項|馬拉松|路跑|健走|越野跑")

# Contest -> the race name already used for earlier editions, so the new year
# lands on the same race page. Contests not listed keep their own name.
RACES = {
    "2026100301": {"race": "L’Étape環法自行車挑戰賽-紐崔萊 • 日月潭站", "region": "南投縣"},
    "2026090701": {"race": "96聯賽武嶺站-挑戰組", "region": "南投縣",
                   "labels": {"96Heroes中華賓士武嶺站-挑戰組": "挑戰組-武嶺站"}},
    "2026090702": {"race": "96聯賽武嶺站競賽組及市民競賽組", "region": "南投縣"},
}
_AGE = re.compile(r"[MWFmwf](\d{2})")


def gender_of(row):
    g = (row.get("gender") or "").strip()
    return {"男": "M", "女": "F", "M": "M", "F": "F"}.get(g)


def build_records(rows, contest, scraped_at):
    """Unified records for one contest's finishers."""
    slug = contest["slug"]
    meta = RACES.get(slug, {})
    date = contest.get("event_date") or None
    year = int(date[:4]) if date else common.extract_year(contest["name"])
    race = meta.get("race") or re.sub(r"^\s*20\d\d\s*", "", contest["name"])
    labels = meta.get("labels", {})
    out = []
    for r in rows:
        if r.get("status") != "0" or not r.get("time_official"):
            continue
        course = (r.get("race_name") or "").strip()
        group = (r.get("group_name") or "").strip() or None
        age = _AGE.search(group or "")
        out.append(common.make_record(
            source_platform=SOURCE, source_url=f"{BASE}/contests/{slug}",
            source_format="json",
            race_name_raw=f"{year} {race}", year=year, date=date,
            race_type="cycling", region=meta.get("region"),
            result_label=labels.get(course, course) or None, category_raw=group,
            gender=gender_of(r), age_group=age.group(1) if age else None,
            rank_overall=r.get("total_place"), bib=r.get("bib") or None,
            team=(r.get("team_name") or "").strip() or None,
            name_raw=(r.get("name") or "").strip() or None,
            finish_time=r["time_official"], scraped_at=scraped_at))
    return out


def fetch_rows(session, slug):
    rows, page = [], 1
    while True:
        url = f"{BASE}/api/contests/{slug}/results?page={page}&pageSize={PAGE}"
        d = common.polite_get(session, url).json()
        rows += d.get("rows") or []
        if not d.get("rows") or len(rows) >= (d.get("total") or 0):
            return rows
        page += 1


def is_cycling(contest):
    name = contest.get("name") or ""
    return contest["slug"] in RACES or (CYCLING.search(name) and not NOT_CYCLING.search(name))


def crawl(session=None):
    session = session or common.make_session()
    os.makedirs(CACHE, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    contests = common.polite_get(session, f"{BASE}/api/contests").json()
    out = []
    for c in contests:
        if c.get("is_preparing") or not is_cycling(c):
            continue
        path = os.path.join(CACHE, f"{c['slug']}.json")
        try:
            rows = fetch_rows(session, c["slug"])
            json.dump({"contest": c, "rows": rows}, open(path, "w", encoding="utf-8"),
                      ensure_ascii=False)
        except Exception as e:  # site down -> fall back to the last good pull
            if not os.path.exists(path):
                raise
            print(f"  ! {c['slug']} fetch failed ({e}); using cache")
            rows = json.load(open(path, encoding="utf-8"))["rows"]
        recs = build_records(rows, c, now)
        print(f"  {c['slug']} {c['name']}: {len(rows)} entrants, {len(recs)} finishers")
        out += recs
    # contests that have dropped off the listing: keep them from the cache
    listed = {c["slug"] for c in contests}
    for fn in sorted(os.listdir(CACHE)):
        if fn.endswith(".json") and fn[:-5] not in listed:
            d = json.load(open(os.path.join(CACHE, fn), encoding="utf-8"))
            recs = build_records(d["rows"], d["contest"], now)
            print(f"  {fn[:-5]} (cache only) {d['contest']['name']}: {len(recs)} finishers")
            out += recs
    return out


def main():
    recs = crawl()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print(f"\n  {len(recs)} rows -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
