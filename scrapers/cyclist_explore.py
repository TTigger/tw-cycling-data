# -*- coding: utf-8 -*-
"""
PoC step 1 — explore cyclist.org.tw (中華民國自行車騎士協會 / TCF) results structure.
Goal: fetch results_list.asp?pno=N listing pages, discover PDF links + how races/years
are laid out. No parsing of PDFs yet — just map the listing HTML.
"""
import re
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.cyclist.org.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9",
}

# pno categories discovered in recon
PNOS = {
    1: "KOM 登山王挑戰",
    2: "俱樂部聯賽",
    13: "臺灣自行車聯賽",
}


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.encoding = r.apparent_encoding or "utf-8"
    return r


def explore(pno, label):
    url = f"{BASE}/results_list.asp?pno={pno}"
    print(f"\n{'='*70}\npno={pno}  {label}\n{url}")
    try:
        r = fetch(url)
    except Exception as e:
        print(f"  ERROR: {e}")
        return
    print(f"  status={r.status_code} bytes={len(r.content)} ctype={r.headers.get('Content-Type')}")
    html = r.text
    # Find all hyperlinks
    links = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
    pdfs = [l for l in links if l.lower().endswith(".pdf") or "resultPDF" in l]
    txts = [l for l in links if "results_txt.asp" in l.lower()]
    print(f"  total links={len(links)}  pdf-like={len(pdfs)}  results_txt={len(txts)}")
    for l in pdfs[:8]:
        print(f"    PDF  {l}")
    for l in txts[:8]:
        print(f"    TXT  {l}")
    # Pull visible text lines that look like race titles / years
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    years = sorted(set(re.findall(r"(20[0-2]\d)", text)))
    print(f"  years seen in text: {years}")
    return pdfs, txts


if __name__ == "__main__":
    for pno, label in PNOS.items():
        explore(pno, label)
