# -*- coding: utf-8 -*-
"""
PoC — parse Bravelog /contest/rank/{id} server-rendered HTML into structured rows.
Confirms Bravelog needs NO JS for the rank list (data is in the document).
Each row: rank, name, raceId, bib, category, gender-group, finish_time + athlete detail URL.
"""
import json
import os
import re
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9",
}

# one athlete block: athlete link (raceId/bib) ... name ... detail spans ... time
BLOCK = re.compile(
    r'href="https://www\.bravelog\.tw/athlete/(?P<raceId>\d+)/(?P<bib>[0-9A-Za-z]+)"'
    r'.*?<div class="name">(?P<name>.*?)</div>'
    r'.*?<div class="detail-info">(?P<detail>.*?)</div>'
    r'.*?<div class="time">\s*<span>\s*(?P<time>[0-9:]+)',
    re.S,
)


def parse_html(html):
    rows = []
    seen = set()
    for i, m in enumerate(BLOCK.finditer(html), 1):
        spans = re.findall(r"<span[^>]*>(.*?)</span>", m.group("detail"), re.S)
        spans = [re.sub(r"\s+", "", s) for s in spans]
        key = (m.group("raceId"), m.group("bib"))
        if key in seen:   # rank list may repeat athlete link (avatar + chevron)
            continue
        seen.add(key)
        bib = spans[0] if len(spans) > 0 else m.group("bib")
        category = spans[1] if len(spans) > 1 else None     # e.g. 104公里挑戰組
        gender_grp = spans[2] if len(spans) > 2 else None   # 男子組/女子組
        rows.append({
            "rank_in_view": len(rows) + 1,
            "race_id": m.group("raceId"),
            "bib": bib,
            "name_raw": re.sub(r"\s+", " ", m.group("name")).strip(),
            "category_raw": category,
            "gender_group": gender_grp,
            "gender": "M" if gender_grp == "男子組" else ("F" if gender_grp == "女子組" else None),
            "finish_time": m.group("time"),
            "athlete_url": f"https://www.bravelog.tw/athlete/{m.group('raceId')}/{m.group('bib')}",
        })
    return rows


def fetch(contest_id):
    url = f"https://www.bravelog.tw/contest/rank/{contest_id}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.encoding = "utf-8"
    return r.text


if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else "2025101802"
    html = fetch(cid)
    rows = parse_html(html)
    print(f"PARSED {len(rows)} athlete rows from contest/rank/{cid}\n")
    for r in rows[:12]:
        print(f"  {r['rank_in_view']:>3}. bib={r['bib']:<8} {r['name_raw'][:22]:<22} "
              f"{(r['category_raw'] or '')[:14]:<14} {r['gender_group'] or '':<4} {r['finish_time']}")
    out = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                       f"sample_bravelog_{cid}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\n  -> wrote {len(rows)} rows to {os.path.relpath(out)}")
    cats = {}
    for r in rows:
        cats[r["category_raw"]] = cats.get(r["category_raw"], 0) + 1
    print(f"  category dist: {cats}")
