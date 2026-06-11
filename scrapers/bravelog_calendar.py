# -*- coding: utf-8 -*-
"""
Bravelog contest discovery via the /search JSON endpoint (found via DevTools):
  GET /search?start=YYYY/MM/DD&end=YYYY/MM/DD&orderBy=start_date|asc   (returns ALL sports)

Fetches 2024-2026, classifies CYCLING contests by title/tag keywords (excluding
triathlon), and writes the cycling-contest worklist for the rank crawler.
"""
import io
import json
import os
import re
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUT, exist_ok=True)

# strong cycling signals in the title/tags
CYCLING = re.compile(
    r"自行車|單車|公路車|鐵馬|武嶺|KOM|登山王|繞圈賽?|環花東|環台|環島|"
    r"落日飛車|銅礦|96聯賽|96\s|雪巴|大滿貫|Étape|L['’]?Etape|經典賽|盃自行車|"
    r"自由車|bike|cycling|"
    r"咖啡公路|寂寞公路|LIVDAY|悠遊騎", re.I)  # LIVDAY/咖啡公路 challenge-ride series
# triathlon / running — exclude even if a cycling word appears
EXCLUDE = re.compile(
    r"鐵人|三項|IRON\s?MAN|IRONMAN|IRONKIDS|小鐵人|duathlon|swimrun|路跑|馬拉松|"
    r"TRI\b|Triathlon|Challenge\s?Taiwan|226|超鐵", re.I)
# distances that strongly imply road cycling (>=60km single leg)
BIG_KM = re.compile(r"(\d{2,3})\s?[Kk][Mm]")


def classify(c):
    """Return 'cycling' / 'maybe' / 'no' for a contest dict."""
    blob = " ".join(str(x) for x in [c.get("title", ""), c.get("host", ""),
                                      " ".join(c.get("tags") or [])])
    if CYCLING.search(blob) and not EXCLUDE.search(c.get("title", "")):
        return "cycling"
    # heuristic: very long single-leg distance + not running/triathlon
    if not EXCLUDE.search(blob):
        for km in BIG_KM.findall(blob):
            if int(km) >= 60:
                return "maybe"
    return "no"


def fetch_year(year):
    url = (f"https://www.bravelog.tw/search?start={year}/01/01"
           f"&end={year}/12/31&orderBy=start_date|asc")
    r = requests.get(url, headers=H, timeout=40)
    r.raise_for_status()
    return r.json().get("contests", [])


def main():
    years = [int(a) for a in sys.argv[1:]] or [2024, 2025, 2026]
    allc, cycling = [], []
    for y in years:
        cs = fetch_year(y)
        print(f"year {y}: {len(cs)} contests")
        for c in cs:
            allc.append(c)
            tag = classify(c)
            if tag in ("cycling", "maybe"):
                cycling.append({
                    "uid": c.get("uid"), "title": c.get("title"),
                    "host": c.get("host"), "city": c.get("city"),
                    "tags": c.get("tags"), "start_date": c.get("start_date"),
                    "statusTag": c.get("statusTag"), "website": c.get("website"),
                    "confidence": tag,
                })
    cycling.sort(key=lambda x: x["uid"])
    path = os.path.join(OUT, "bravelog_cycling_contests.json")
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(cycling, f, ensure_ascii=False, indent=2)
    print(f"\nCYCLING contests: {len(cycling)} (of {len(allc)} total)")
    for c in cycling:
        flag = "✓" if c["confidence"] == "cycling" else "?"
        print(f"  {flag} {c['uid']}  {c['statusTag']:<6} [{','.join(c['tags'] or [])[:16]:<16}] {c['title'][:38]}")
    print(f"\n-> {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
