# -*- coding: utf-8 -*-
"""
PoC — probe Bravelog: is /contest/rank data in the initial HTML (static-scrapable)
or loaded via JS/XHR? Try a few candidate contest IDs and inspect.
"""
import re
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9",
}

CANDIDATES = [
    "https://www.bravelog.tw/contest/rank/2025101802",
    "https://www.bravelog.tw/contest",
    "https://www.bravelog.tw/calendar",
]


def probe(url):
    print(f"\n{'='*68}\n{url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except Exception as e:
        print(f"  ERROR {e}")
        return
    html = r.text
    print(f"  status={r.status_code} bytes={len(r.content)} ctype={r.headers.get('Content-Type')}")
    # signals of SPA vs SSR
    has_next = "__NEXT_DATA__" in html or "_nuxt" in html.lower() or "id=\"app\"" in html
    has_react_root = 'id="root"' in html or "data-reactroot" in html
    # does the raw HTML already contain result-ish data?
    names_zh = len(re.findall(r"[一-鿿]{2,4}", html))
    times = re.findall(r"\d{1,2}:\d{2}:\d{2}", html)
    table_rows = len(re.findall(r"<tr[ >]", html, re.I))
    json_blobs = re.findall(r"(window\.__[A-Z_]+__\s*=|application/json)", html)
    print(f"  SPA-markers: __NEXT_DATA__/_nuxt/app={has_next}  root={has_react_root}")
    print(f"  <tr> rows in HTML={table_rows}  time-strings={len(times)}  zh-tokens={names_zh}")
    print(f"  json-blobs={json_blobs[:3]}")
    # find API-ish references
    apis = sorted(set(re.findall(r"[\"'](/api/[^\"']+|https?://[^\"']*api[^\"']*)[\"']", html)))
    for a in apis[:10]:
        print(f"    api-ref: {a}")
    if times[:5]:
        print(f"  sample times in HTML: {times[:5]}")


if __name__ == "__main__":
    for u in CANDIDATES:
        probe(u)
