# -*- coding: utf-8 -*-
"""Recover 臺灣自行車聯賽 (Taiwan Cyclist League) results from cyclist.org.tw —
a gap our main cyclist_crawl misses because these races publish via
`results_txt.asp?pno=N` LANDING pages (個人計時/團隊計時/公路繞圈/累計總排名),
each linking 成績公告 PDFs under /upfile/file/…pdf, rather than the PDF list
that cyclist_crawl scrapes. Found via discover.py (桃園航空城/桃園繞圈賽).

The PDFs are clean tables: `排名 編號 姓名 組別 車隊 [出發 終點] 完成時間 均速`.
We parse them with the same pdfplumber approach; the result time is reliably
the LAST HH:MM:SS token on the row (avg-speed is a bare int after it).

Output: data/processed/cycling_league.json (merge.py globs cycling_*).
"""
import io
import json
import os
import re
import ssl
import sys
import urllib.request

import pdfplumber

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}
BASE = "https://www.cyclist.org.tw"
LEAGUE_LIST = BASE + "/results_list.asp?pno=13"          # 臺灣自行車聯賽 section
PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdf", "league")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PDF_DIR, exist_ok=True)

TIME = re.compile(r"\d{1,2}:\d{2}:\d{2}(?:\.\d{1,3})?")
DIV = re.compile(r"^(?:[MWF男女]\d{1,2}組?|男子\w*|女子\w*|菁英\w*|青年\w*|公開\w*|社會\w*|U\d{1,2}|"
                 r"\w{1,4}歲組?|分齡\w*|挑戰\w*|市民\w*|甲組|乙組|丙組|身障\w*)$")
ROC = re.compile(r"(20\d{2})")


def _get(url, enc="utf-8"):
    return urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=40,
                                  context=_CTX).read().decode(enc, "replace")


def landing_pages():
    """results_txt.asp?pno=N landing pages for the league + each page's title."""
    html = _get(LEAGUE_LIST)
    pnos = sorted(set(int(x) for x in re.findall(r"results_txt\.asp\?pno=(\d+)", html)))
    out = []
    for pno in pnos:
        try:
            page = _get(f"{BASE}/results_txt.asp?pno={pno}")
        except Exception:
            continue
        m = re.search(r"<title>(.*?)</title>", page, re.S)
        title = re.sub(r"\s+", "", re.sub(r"成績紀錄[-—]?", "", m.group(1))) if m else f"聯賽{pno}"
        pdfs = re.findall(r'(?:href|src)="(/upfile/file/[^"]+\.pdf)"', page)
        out.append((pno, title[:40], sorted(set(pdfs))))
    return out


def download(href):
    fn = re.sub(r"[^0-9A-Za-z._-]", "_", href.rsplit("/", 1)[-1])
    path = os.path.join(PDF_DIR, fn)
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return path
    try:
        d = urllib.request.urlopen(urllib.request.Request(BASE + href, headers=H), timeout=40,
                                   context=_CTX).read()
        if d[:4] == b"%PDF":
            open(path, "wb").write(d)
            return path
    except Exception as e:
        print(f"   ! download failed {href}: {e}")
    return None


def parse_pdf(path, race_name, year):
    rows, seen = [], set()
    try:
        pdf = pdfplumber.open(path)
    except Exception as e:
        print(f"   ! open error {os.path.basename(path)}: {e}")
        return rows
    with pdf:
        event = None
        for page in pdf.pages:
            for ln in (page.extract_text() or "").splitlines():
                s = ln.strip()
                em = re.search(r"(個人計時賽|團隊計時賽|公路繞圈賽|繞圈賽|累計總排名|公路賽|計時賽)", s)
                if em and len(s) < 40:
                    event = em.group(1)
                toks = s.split()
                if len(toks) < 6 or not toks[0].isdigit():
                    continue
                tidx = [i for i, t in enumerate(toks) if TIME.fullmatch(t)]
                if not tidx:
                    continue
                # Individual finisher rows carry a 組別 token; TTT-race and the
                # 積分/累計 standings do NOT (team-based) — skip those here.
                divs = [i for i in range(1, tidx[0]) if DIV.match(toks[i])]
                if not divs:
                    continue
                di = divs[0]
                rank = int(toks[0])
                result = toks[tidx[-1]]                  # last HH:MM:SS = 完成時間
                div = toks[di]
                if di == 1:                              # layout: 排名 組別 編號 姓名 車隊 …
                    bib = toks[2] if len(toks) > 2 else None
                    rest = toks[3:tidx[0]]
                    name = rest[0] if rest else None
                    team = " ".join(rest[1:]).strip() or None
                else:                                    # layout: 排名 編號 姓名 … 組別 車隊 …
                    bib = toks[1]
                    name = " ".join(toks[2:di]).strip()
                    team = " ".join(toks[di + 1:tidx[0]]).strip() or None
                if not name or not re.search(r"[一-鿿A-Za-z]", name):
                    continue
                gender, age = common.parse_division(div or "")
                key = (event, bib, name, result)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(common.make_record(
                    source_platform="cyclist.org.tw", source_url=path,
                    source_format="pdf", race_name_raw=f"{year} {race_name}",
                    year=year, race_type="road", result_label=event, category_raw=div,
                    gender=gender, age_group=age, rank_overall=rank, bib=bib,
                    name_raw=name, team=team, finish_time=result,
                    finish_seconds=common.time_to_seconds(result), scraped_at="2026-06-11"))
    return rows


def main():
    pages = landing_pages()
    print(f"league landing pages: {len(pages)}")
    records = []
    for pno, title, pdfs in pages:
        year = int((ROC.search(title) or ROC.search(" ".join(pdfs)) or [None, 0])[1]) or None
        n0 = len(records)
        for href in pdfs:
            path = download(href)
            if path:
                records.extend(parse_pdf(path, re.sub(r"^20\d{2}", "", title).strip(), year))
        print(f"  pno={pno} {title[:30]:<30} pdfs={len(pdfs)} rows={len(records) - n0}")
    # Avoid double-counting: the road 公路賽 PDFs duplicate existing 環花東/
    # 陽明山王/太平山王/KOM data. Keep only genuinely-new individual results:
    #  - 個人計時賽 (ITT): a time-trial format we don't otherwise have
    #  - 桃園繞圈賽: an entirely new race (its ITT + 繞圈各分組 results)
    # TTT-race + 積分/累計 standings are already dropped (no 組別 token).
    records = [r for r in records
               if r.get("result_label") != "累計總排名"          # derived sum — would double-count
               and (r.get("result_label") == "個人計時賽" or "桃園繞圈" in (r.get("race_name_raw") or ""))]
    out = os.path.join(OUT_DIR, "cycling_league.json")
    json.dump(records, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    from collections import Counter
    print(f"\n=== records={len(records)} (個人計時賽 ITT only) ===")
    print(f"  years: {dict(Counter(r['year'] for r in records))}")
    print(f"  labels: {dict(Counter(r['result_label'] for r in records))}")
    print(f"  -> {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
