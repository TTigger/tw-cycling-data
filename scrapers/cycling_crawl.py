# -*- coding: utf-8 -*-
"""
Crawler for cycling.org.tw (中華民國自由車協會, national federation) ROAD results.

Source: the single static page /下載區/ links ~31 road-race result files (2009-2026).
This crawler targets the PDF result books (which carry **UCI rider IDs** — the key
to Phase-3 athlete tracking). Each results book has, per category, a clean
row-per-rider "成績" table:  名次 選手號 姓名 隊伍 UCI證號碼 時間 ...
We parse those (anchoring on the 10-11 digit UCI id), skipping start lists (出發),
lap-split "Intermediate Points" pages (no 隊伍 column), and team-points pages.

Old podium-wide Excel files (2009-2015, no UCI ids) are NOT handled here — deferred.

Usage:
  python cycling_crawl.py --inspect <local.pdf>   # parse one file, print sample
  python cycling_crawl.py                          # full crawl of road PDFs -> cycling_national.json
"""
import argparse
import json
import os
import re
import sys
import time
import pdfplumber

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

LIST_URL = "https://cycling.org.tw/%e4%b8%8b%e8%bc%89%e5%8d%80/"
PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdf", "cycling")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PDF_DIR, exist_ok=True)

# a clean result row:  rank bib  name+team  UCI(9-11 digits)  time[ ...]
UCI = r"\d{9,11}"
TIME = r"\d{1,2}:\d{2}(?::\d{2})?(?:\.\d{1,3})?"   # H:MM:SS.ff or MM:SS.ff
ROW = re.compile(rf"^(?P<rank>\d{{1,3}})\s+(?P<bib>\d{{1,4}})\s+(?P<mid>.+?)\s+(?P<uci>{UCI})\s+(?P<time>{TIME})")


def roc_year(title):
    """民國年 in title -> Gregorian. '114年...' -> 2025. Falls back to any 20xx."""
    m = re.search(r"(\d{2,3})\s*年", title or "")
    if m:
        y = int(m.group(1))
        if 90 <= y <= 130:
            return y + 1911
    return common.extract_year(title)


def time_seconds(t):
    """Flexible: H:MM:SS(.ff) or MM:SS(.ff)."""
    parts = t.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    except ValueError:
        return None
    return None


def page_category(lines):
    """From the page header (e.g. '男子菁英組/個人計時賽(達標成績：63分50秒)') return
    (division, event) -> ('男子菁英組', '個人計時賽'). Strips parenthetical noise."""
    for ln in lines[:4]:
        ln = re.sub(r"\s+", "", ln.strip())
        if re.search(r"男子|女子", ln) and ("組" in ln or "/" in ln or "菁英" in ln or "U23" in ln):
            ln = re.split(r"[(（]", ln)[0]            # drop "(達標成績…)" etc.
            div, _, event = ln.partition("/")
            return div or None, (event or None)
    return None, None


def is_result_table(lines):
    """A parseable final-result page has a column header with 名次 + 姓名 + 隊伍 + UCI,
    and is not a start list (出發)."""
    text = "\n".join(lines[:8])
    if "出發" in text:
        return False
    for ln in lines[:10]:
        if "名次" in ln and "姓名" in ln and "隊伍" in ln and ("UCI" in ln or "證號" in ln):
            return True
    return False


def split_name_team(mid):
    """'杜志濠 Team Bahrain Victorious' -> ('杜志濠', 'Team Bahrain Victorious').
    Chinese names are a single whitespace-free token; team is the rest."""
    parts = mid.split(None, 1)
    if not parts:
        return None, None
    return parts[0], (parts[1].strip() if len(parts) > 1 else None)


def parse_pdf(path, race_name, year):
    rows, seen = [], set()
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                lines = (page.extract_text() or "").splitlines()
                if not is_result_table(lines):
                    continue
                cat, event = page_category(lines)
                for ln in lines:
                    m = ROW.match(ln.strip())
                    if not m:
                        continue
                    name, team = split_name_team(m.group("mid"))
                    if not name:
                        continue
                    key = (cat, event, m.group("bib"), m.group("uci"))  # event keeps ITT≠road
                    if key in seen:
                        continue
                    seen.add(key)
                    secs = time_seconds(m.group("time"))
                    gender = "F" if cat and "女子" in cat else ("M" if cat and "男子" in cat else None)
                    rows.append(common.make_record(
                        source_platform="cycling.org.tw", source_url=path if path.startswith("http") else race_name,
                        source_format="pdf", race_name_raw=race_name, year=year,
                        race_type="road", result_label=event, category_raw=cat,
                        gender=gender, rank_overall=int(m.group("rank")), bib=m.group("bib"),
                        uci_id=m.group("uci"), name_raw=name, team=team,
                        finish_time=m.group("time"), finish_seconds=secs, scraped_at="2026-06-04"))
    except Exception as e:
        print(f"   ! parse error {os.path.basename(path)}: {e}")
    return rows


def listing(session):
    r = common.polite_get(session, LIST_URL, delay=1.2)
    r.encoding = r.apparent_encoding or "utf-8"
    out = []
    for href, txt in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', r.text, re.S | re.I):
        t = re.sub(r"<[^>]+>", "", txt)
        t = re.sub(r"\s+", "", t)
        if "公路" in t and not re.search(r"場地|登山車|電競|下坡|越野|BMX|規則", t):
            out.append((roc_year(t), t[:60], href))
    return out


def download(session, href):
    fn = re.sub(r"[^0-9A-Za-z._-]", "_", href.rsplit("/", 1)[-1])
    path = os.path.join(PDF_DIR, fn)
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
    records = []
    for year, name, href in files:
        path = download(s, href)
        if not path:
            continue
        rs = parse_pdf(path, name, year)
        print(f"  {year} {name[:34]:<34} rows={len(rs)}")
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
