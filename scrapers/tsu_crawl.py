# -*- coding: utf-8 -*-
"""
Crawler for tsu.com.tw (Taiwan Cycling Union 賽事成績平台) — a 4th source that
fills coverage gaps the existing three miss: county 縣長盃 circuit races, 越野/
gravel criteriums, college/local races, AND deep history (year filter spans
2009-2026). Bonus: many result rows carry a stable /rider/detail/TCU-<id>
rider id — a broader identity anchor than UCI for Phase-3 athlete tracking.

Structure (all UTF-8, static HTML, robots Allow: /):
  list:    /race?y=<YYYY>&page=<N>   cards link /race/detail/TCU-<id>; the race
           NAME is the card <img alt="..."> (names are banner images); date in card
  result:  /race/result/TCU-<id>     a per-rider table:
           [_, 總排(rank/cat-size), 組別, 選手, 號碼, 車隊, 完賽時間, 積分, 備註]
           some rows link /rider/detail/TCU-<rider-id>

Usage:
  python tsu_crawl.py --smoke                 # 1 recent year, few races, print sample
  python tsu_crawl.py --years 2009-2026       # full crawl -> cycling_tsu.json
  python tsu_crawl.py                          # default = 2009-2026
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.tsu.com.tw"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

ID = r"TCU-[A-Za-z0-9]+"
TIME = r"\d{1,2}:\d{2}:\d{2}(?:\.\d{1,3})?"
_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _txt(html):
    return _WS.sub(" ", _TAGS.sub(" ", html)).strip()


def _get(session, url, delay=0.8):
    r = common.polite_get(session, url, delay=delay)
    r.encoding = "utf-8"
    return r.text if r.status_code == 200 else None


def list_year(session, year):
    """All (race_id, name, date) cards for one year, across pages."""
    out, seen = [], set()
    for page in range(1, 40):
        html = _get(session, f"{BASE}/race?y={year}&page={page}")
        if not html:
            break
        # split into cards on the detail anchor; capture id + img alt (name) + a date
        cards = re.split(r'(?=<a href="/race/detail/)', html)
        added = 0
        for c in cards:
            m = re.search(r'/race/detail/(' + ID + r')"', c)
            if not m:
                continue
            rid = m.group(1)
            if rid in seen:
                continue
            alt = re.search(r'<img[^>]+alt="([^"]*)"', c)
            name = (alt.group(1).strip() if alt else "") or None
            dm = re.search(r"20[0-2]\d[-/.]\d{1,2}[-/.]\d{1,2}", c)
            date = dm.group(0).replace("/", "-").replace(".", "-") if dm else None
            seen.add(rid)
            out.append((rid, name, date))
            added += 1
        if added == 0:
            break
    return out


def _colmap(ths):
    """Map a result table's header cells -> column indices. Layouts vary per race:
    standard is 總排/分排/組別/選手/號碼/車隊/完賽時間/[積分]/備註 (總排 often blank,
    分排 = in-category rank); the criterium variant uses 級排 for rank and splits
    the category across 個人級別/成績級別/年齡分組. Priority picks the most
    informative column when several candidates exist."""
    rank_pri = {"分排": 0, "級排": 1, "總排": 2, "名次": 2}
    cat_pri = {"組別": 0, "年齡分組": 1, "個人級別": 2, "成績級別": 3}
    idx, rank_best, cat_best = {}, 99, 99
    for i, t in enumerate(ths):
        if t in rank_pri and rank_pri[t] < rank_best:
            idx["rank"], rank_best = i, rank_pri[t]
        if t in cat_pri and cat_pri[t] < cat_best:
            idx["cat"], cat_best = i, cat_pri[t]
        if t in ("選手", "姓名"):
            idx["name"] = i
        elif t == "號碼":
            idx["bib"] = i
        elif t in ("車隊", "隊伍"):
            idx["team"] = i
        elif t in ("完賽時間", "成績", "時間", "晶片時間"):
            idx["time"] = i
    return idx


def parse_result(session, rid, name, date, year):
    """Parse /race/result/<rid> into unified records (one per finisher). Each
    category may be its own <table>; map columns by header per table."""
    html = _get(session, f"{BASE}/race/result/{rid}", delay=0.6)
    if not html:
        return []
    if not date:
        dm = re.search(r"20[0-2]\d-\d{1,2}-\d{1,2}", html)
        date = dm.group(0) if dm else None
    yr = year or common.extract_year(date or "") or common.extract_year(name or "")
    rows, seen = [], set()
    tables = re.findall(r"<table[ >].*?</table>", html, re.S) or [html]
    for table in tables:
        ths = [_txt(t) for t in re.findall(r"<th[ >].*?</th>", table, re.S)]
        cmap = _colmap(ths)
        if "name" not in cmap or "time" not in cmap:
            continue
        need = max(cmap.values())
        for tr in re.findall(r"<tr[ >].*?</tr>", table, re.S):
            rider = re.search(r"/rider/detail/(" + ID + r")", tr)
            cells = [_txt(td) for td in re.findall(r"<td[ >].*?</td>", tr, re.S)]
            if len(cells) <= need:
                continue                          # header row / malformed
            tm = cells[cmap["time"]]
            if not re.fullmatch(TIME, tm):
                continue                          # DNS / DNF / no finish time
            nm = cells[cmap["name"]]
            if not nm:
                continue
            rm = re.match(r"(\d{1,4})", cells[cmap["rank"]]) if "rank" in cmap else None
            cat = cells[cmap["cat"]] if "cat" in cmap else None
            bib = cells[cmap["bib"]] if "bib" in cmap else None
            team = cells[cmap["team"]] if "team" in cmap else None
            key = (cat, bib, nm, tm)
            if key in seen:
                continue
            seen.add(key)
            gender, age = common.parse_division(cat)
            if cat and re.search(r"woman|women|女", cat, re.I):
                gender = "F"
            rows.append(common.make_record(
                source_platform="tsu.com.tw", source_url=f"{BASE}/race/result/{rid}",
                source_format="html", race_name_raw=name or rid, year=yr, date=date,
                race_type="road", category_raw=cat, gender=gender, age_group=age,
                rank_overall=int(rm.group(1)) if rm else None, bib=bib,
                tsu_rider_id=rider.group(1) if rider else None,
                name_raw=nm, team=(team or None), finish_time=tm,
                finish_seconds=common.time_to_seconds(tm), scraped_at="2026-06-11"))
    return rows


def crawl(years, smoke=False):
    s = common.make_session()
    races = []
    for y in years:
        yl = list_year(s, y)
        print(f"  year {y}: {len(yl)} races")
        races.extend(yl)
        if smoke and races:
            break
    if smoke:
        races = races[:4]
    print(f"races to fetch: {len(races)}")
    records = []
    for i, (rid, name, date) in enumerate(races, 1):
        rs = parse_result(s, rid, name, date, common.extract_year(date or ""))
        if rs:
            print(f"  [{i}/{len(races)}] {(name or rid)[:38]:<38} rows={len(rs)}")
        records.extend(rs)
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="1 year, 4 races, print sample")
    ap.add_argument("--years", help="range like 2009-2026 (default)")
    ap.add_argument("--out", default="cycling_tsu.json")
    args = ap.parse_args()

    if args.years:
        a, b = (int(x) for x in args.years.split("-"))
        years = list(range(a, b + 1))
    elif args.smoke:
        years = [2024]
    else:
        years = list(range(2009, 2027))

    records = crawl(years, smoke=args.smoke)
    print(f"\n=== records={len(records)} ===")
    print(f"  years: {dict(sorted(Counter(r['year'] for r in records).items(), key=lambda x: str(x[0])))}")
    print(f"  with rider_id: {sum(1 for r in records if r['tsu_rider_id'])}")
    print(f"  by gender: {dict(Counter(r['gender'] for r in records))}")
    if args.smoke:
        for r in records[:12]:
            print(f"    #{r['rank_overall']} {r['name_masked']} [{r['category_raw']}] "
                  f"{r['team']} {r['finish_time']} rider={r['tsu_rider_id']}")
        return
    out = os.path.join(OUT_DIR, args.out)
    json.dump(records, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  -> {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
