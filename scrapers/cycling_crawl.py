# -*- coding: utf-8 -*-
"""
Crawler for cycling.org.tw (中華民國自由車協會, national federation) ROAD results.

Source: the single static page /下載區/ links ~31 road-race result files (2009-2026).
The PDF result books (2016-2026) come in about a dozen layouts; cycling_generic
reads the per-category result pages (rank, bib, name, [UCI id], team, time) and
skips podium summaries, start lists, combined-time tables and team events.
Files are saved as <ascii-stem>-<md5(url)[:8]>.pdf so CJK-only names can't collide.

Old podium-wide Excel files (2009-2015, no UCI ids) are NOT handled here — deferred.

Usage:
  python cycling_crawl.py --inspect <local.pdf>   # parse one file, print sample
  python cycling_crawl.py                          # full crawl of road PDFs -> cycling_national.json
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import pdfplumber

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402
import cycling_generic  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

LIST_URL = "https://cycling.org.tw/%e4%b8%8b%e8%bc%89%e5%8d%80/"
PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdf", "cycling")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PDF_DIR, exist_ok=True)


def roc_year(title):
    """民國年 in title -> Gregorian. '114年...' -> 2025. Falls back to any 20xx."""
    m = re.search(r"(\d{2,3})\s*年", title or "")
    if m:
        y = int(m.group(1))
        if 90 <= y <= 130:
            return y + 1911
    return common.extract_year(title)


def parse_pdf(path, race_name, year, source_url=None):
    """All layouts go through cycling_generic (it reproduces the old 114年 parser
    row for row and also reads the 105-115年 layouts)."""
    try:
        with pdfplumber.open(path) as pdf:
            pages = [(pg.extract_text() or "").splitlines() for pg in pdf.pages]
    except Exception as e:
        print(f"   ! parse error {os.path.basename(path)}: {e}")
        return []
    rows = []
    for r in cycling_generic.parse_dedup(pages):
        rows.append(common.make_record(
            source_platform="cycling.org.tw", source_url=source_url or race_name,
            source_format="pdf", race_name_raw=race_name, year=year,
            race_type="road", result_label=r["event"], category_raw=r["category"],
            gender=r["gender"], rank_overall=r["rank"], bib=r["bib"],
            uci_id=r["uci"], name_raw=r["name"], team=r["team"],
            finish_time=r["time"], finish_seconds=r["secs"], status=r["status"],
            scraped_at="2026-11-06"))
    return rows


def listing(session):
    r = common.polite_get(session, LIST_URL, delay=1.2)
    r.encoding = r.apparent_encoding or "utf-8"
    out = []
    for href, txt in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', r.text, re.S | re.I):
        t = html.unescape(re.sub(r"<[^>]+>", "", txt))
        t = re.sub(r"\s+", "", t)
        if "公路" in t and not re.search(r"場地|登山車|電競|下坡|越野|BMX|規則", t):
            out.append((roc_year(t), t[:60], href))
    return out


def _old_name(href):
    return re.sub(r"[^0-9A-Za-z._-]", "_", href.rsplit("/", 1)[-1])


def local_name(href):
    """Old names replaced every CJK char with '_', so two 110年 files with
    same-length titles landed on one path. Add a short hash of the URL."""
    stem = _old_name(href)[:-4] if _old_name(href).lower().endswith(".pdf") else _old_name(href)
    return f"{stem[:40]}-{hashlib.md5(href.encode()).hexdigest()[:8]}.pdf"


def migrate_names(hrefs):
    """Rename files saved under the old scheme, unless two URLs shared that name
    (then the file on disk is only one of them: delete-free, just re-download)."""
    from collections import Counter
    olds = Counter(_old_name(h) for h in hrefs)
    for h in hrefs:
        old, new = os.path.join(PDF_DIR, _old_name(h)), os.path.join(PDF_DIR, local_name(h))
        if olds[_old_name(h)] == 1 and os.path.exists(old) and not os.path.exists(new):
            os.rename(old, new)


def download(session, href):
    path = os.path.join(PDF_DIR, local_name(href))
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return path
    for attempt in range(3):                       # cycling.org.tw rate-limits aggressively
        r = common.polite_get(session, href, delay=2.5)
        if r.status_code == 200 and r.content[:4] == b"%PDF":
            open(path, "wb").write(r.content)
            return path
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))         # backoff 10s, 20s
            continue
        break
    print(f"   ! download failed {r.status_code} {href}")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", help="parse a single local PDF and print a sample")
    args = ap.parse_args()

    if args.inspect:
        rows = parse_pdf(args.inspect, race_name="(inspect)", year=roc_year(os.path.basename(args.inspect)))
        print(f"parsed {len(rows)} rows")
        from collections import Counter
        print("by category:", dict(Counter(r["category_raw"] for r in rows)))
        print("with uci_id:", sum(1 for r in rows if r["uci_id"]))
        for r in rows[:12]:
            print(f"  #{r['rank_overall']:>3} {r['name_masked']:<8} {r['category_raw']} "
                  f"{r['result_label']} uci={r['uci_id']} {r['finish_time']} ({r['finish_seconds']})")
        return

    s = common.make_session()
    files = listing(s)
    print(f"road PDFs: {len(files)}")
    migrate_names([h for _, _, h in files])
    records = []
    for year, name, href in files:
        path = download(s, href)
        if not path:
            continue
        rs = parse_pdf(path, name, year, source_url=href)
        fin = sum(1 for r in rs if not r["status"])
        print(f"  {year} {name[:34]:<34} rows={len(rs)} finishers={fin}")
        records.extend(rs)

    out = os.path.join(OUT_DIR, "cycling_national.json")
    json.dump(records, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    from collections import Counter
    print(f"\n=== DONE === records={len(records)}")
    print(f"  years: {dict(sorted(Counter(r['year'] for r in records).items(), key=lambda x: str(x[0])))}")
    print(f"  with uci_id: {sum(1 for r in records if r['uci_id'])}")
    print(f"  -> {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
