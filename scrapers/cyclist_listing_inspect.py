# -*- coding: utf-8 -*-
"""Inspect how results_list.asp?pno=N lays out individual events (title + results_txt link + date)."""
import re
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}

url = "https://www.cyclist.org.tw/results_list.asp?pno=13"
r = requests.get(url, headers=H, timeout=30)
r.encoding = r.apparent_encoding or "utf-8"
html = r.text

# Find each event block: anchor to results_txt.asp?pno=NNN and nearby visible text
for m in re.finditer(r'results_txt\.asp\?pno=(\d+)', html):
    s = max(0, m.start() - 400)
    chunk = html[s:m.end() + 60]
    chunk = re.sub(r"<[^>]+>", " ", chunk)
    chunk = re.sub(r"\s+", " ", chunk).strip()
    print(f"pno={m.group(1)} ... {chunk[-160:]}")
