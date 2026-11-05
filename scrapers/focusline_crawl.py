# -*- coding: utf-8 -*-
"""Scrape TWB (台灣自行車協會) ultra-distance certification results from the
score.focusline.com.tw JSON API. Each event (actCode) has categories (distances);
each category is one race. gunTime = finish time; source rank (totalSort) is
unreliable for certification rides so rank_overall stays None and the frontend
re-ranks by (category, time). Sub-1h finish times are DNF/placeholders -> dropped.
Also collects the ranked road challenges listed in CHALLENGES (source
focusline.com.tw, with ranks).
Output: data/processed/focusline_2023_2026.json
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

BASE = "https://score.focusline.com.tw"
TOWER = re.compile(r"塔|北高|360|四極")
MIN_FINISH_SEC = 3600  # < 1h on a 300-600km ride = placeholder/DNF
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                   "focusline_2023_2026.json")
_AGE = re.compile(r"(\d{2})")

# Ranked road challenges focusline also times (found 2026-11-05). actCode ->
# (race name, region). Unlike the tower certifications these have a real
# ranking, so totalSort is kept. MTB / trail-run / 休閒 (leisure) heats are left out.
CHALLENGES = {
    "60201KR": ("梅山36彎自行車挑戰賽", "嘉義縣"),
    "60321LA": ("櫻花勇士-探索北橫·騎行羅馬", "桃園市"),
    "51130JY": ("西螺媽祖太平媽祈福自行車挑戰賽", "雲林縣"),
    "41117HN": ("西螺媽祖太平媽祈福自行車挑戰賽", "雲林縣"),
    "50928JG": ("蘭陽百K自行車挑戰賽", "宜蘭縣"),
    "30910CM": ("蘭陽百K自行車挑戰賽", "宜蘭縣"),
    "51214KF": ("全球百鐵認證高雄百K自行車挑戰賽", "高雄市"),
    "31126AM": ("第五屆經典新玉門關公路自行車賽", None),
}
SKIP_CATEGORY = re.compile(r"休閒|接力")


def gender_of(row):
    g = (row.get("gender") or "").strip()
    if g in ("男", "M", "m"):
        return "M"
    if g in ("女", "W", "F", "w", "f"):
        return "F"
    grp = (row.get("group") or "").strip()
    if grp[:1] in ("M", "m", "男"):
        return "M"
    if grp[:1] in ("W", "F", "w", "f", "女"):
        return "F"
    return None


def build_records(rows, meta, scraped_at):
    out = []
    for r in rows:
        fs = common.time_to_seconds(r.get("gunTime"))
        if fs is None or fs < MIN_FINISH_SEC:
            continue
        grp = r.get("group")
        age = _AGE.search(grp or "")
        race = meta.get("race")  # set for CHALLENGES, None for tower certifications
        rank = str(r.get("totalSort") or "")
        out.append(common.make_record(
            source_platform="focusline.com.tw" if race else "twbike.org",
            source_url=meta["url"], source_format="json",
            race_name_raw=f"{meta['year']} {race}" if race else f"{meta['category']} {meta['year']}",
            year=meta["year"], date=meta["date"], region=meta.get("region"),
            race_type="cycling" if race else None,
            result_label=meta["category"], category_raw=grp,
            gender=gender_of(r), age_group=age.group(1) if age else None,
            rank_overall=int(rank) if race and rank.isdigit() and int(rank) > 0 else None,
            bib=r.get("number"), team=None,
            name_raw=r.get("name"), finish_time=r.get("gunTime"),
            scraped_at=scraped_at))
    return out


def crawl(session=None):
    session = session or common.make_session()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    acts = common.polite_get(session, f"{BASE}/api/Activity?urlPath=focusline").json()
    out = []
    for a in acts:
        challenge = CHALLENGES.get(a.get("actCode"))
        if not challenge and not TOWER.search(a.get("actName") or ""):
            continue
        date = (a.get("actDate") or "")[:10] or None
        year = a.get("year") or (int(date[:4]) if date else None)
        print(f"  {a.get('actCode')} {year} {a.get('actName')}")
        for c in (a.get("categories") or []):
            number, cat = c.get("number"), c.get("name")
            if SKIP_CATEGORY.search(cat or ""):
                continue  # relay = different time semantics; 休閒 = unranked leisure ride
            page = 1
            while True:
                url = (f"{BASE}/api/Member/focusline?code={a['actCode']}"
                       f"&categoryName={number}&nameOrNumber=&page={page}")
                rows = common.polite_get(session, url).json()
                if not rows:
                    break
                meta = {"category": cat, "year": year, "date": date, "url": url}
                if challenge:
                    meta["race"], meta["region"] = challenge
                out.extend(build_records(rows, meta, now))
                if len(rows) < 30:
                    break
                page += 1
    return out


def main():
    recs = crawl()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print(f"\n  {len(recs)} rows -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
