# -*- coding: utf-8 -*-
"""
PoC step 2 — drill into ONE cyclist.org.tw event page, map (link-text -> PDF),
download a PDF, and parse it with pdfplumber to prove the full chain:
  listing -> event page -> PDF -> structured rows.
"""
import os
import re
import sys
import requests
import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.cyclist.org.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9",
}
PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdf")
os.makedirs(PDF_DIR, exist_ok=True)


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.encoding = r.apparent_encoding or "utf-8"
    return r


def event_page(event_pno):
    url = f"{BASE}/results_txt.asp?pno={event_pno}"
    print(f"\n=== EVENT PAGE results_txt.asp?pno={event_pno} ===\n{url}")
    r = fetch(url)
    print(f"  status={r.status_code} bytes={len(r.content)}")
    html = r.text
    # title from <title> and first big heading-ish text
    title = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    print(f"  <title>: {title.group(1).strip() if title else '(none)'}")
    # anchor text -> href for PDFs (this gives category labels like 總排名/各分組排名)
    anchors = re.findall(r'<a[^>]+href=["\']([^"\']+\.pdf)["\'][^>]*>(.*?)</a>', html, re.I | re.S)
    print(f"  PDF anchors: {len(anchors)}")
    mapped = []
    for href, txt in anchors:
        label = re.sub(r"<[^>]+>", "", txt)
        label = re.sub(r"\s+", " ", label).strip()
        mapped.append((label, href))
        print(f"    [{label}]  ->  {href}")
    # date hints
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    dates = re.findall(r"(20\d\d[./年-]\s?\d{1,2}[./月-]\s?\d{1,2})", text)
    print(f"  date hints: {dates[:5]}")
    return mapped


def download_pdf(href):
    url = href if href.startswith("http") else f"{BASE}/{href.lstrip('/')}"
    fn = re.sub(r"[^0-9A-Za-z._-]", "_", os.path.basename(href))
    path = os.path.join(PDF_DIR, fn)
    r = requests.get(url, headers=HEADERS, timeout=60)
    print(f"\n  DOWNLOAD {url}\n    status={r.status_code} ctype={r.headers.get('Content-Type')} bytes={len(r.content)}")
    if r.status_code == 200 and r.content[:4] == b"%PDF":
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"    saved -> {path}")
        return path
    print("    NOT a valid PDF")
    return None


def parse_pdf(path, max_rows=15):
    print(f"\n=== PARSE {os.path.basename(path)} ===")
    with pdfplumber.open(path) as pdf:
        print(f"  pages={len(pdf.pages)}")
        page = pdf.pages[0]
        tables = page.extract_tables()
        print(f"  tables on page 1: {len(tables)}")
        if tables:
            t = tables[0]
            print(f"  table[0] rows={len(t)} cols={len(t[0]) if t else 0}")
            for row in t[:max_rows]:
                cells = [(c or "").replace("\n", " ").strip() for c in row]
                print("   | " + " | ".join(cells))
        else:
            # fallback: raw text
            txt = page.extract_text() or ""
            for line in txt.splitlines()[:max_rows]:
                print("   . " + line)


if __name__ == "__main__":
    # 2026 臺灣自行車聯賽 event (numeric-named PDFs) — tests category-from-anchor-text
    mapped = event_page(165)
    if mapped:
        p = download_pdf(mapped[min(1, len(mapped) - 1)][1])
        if p:
            parse_pdf(p)
