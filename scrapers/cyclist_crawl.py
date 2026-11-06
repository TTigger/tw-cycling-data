# -*- coding: utf-8 -*-
"""
Phase-1 crawler for cyclist.org.tw (TCF) — competitive road-cycling results 2024-2026.

Pipeline:  category listings -> event pages -> ranking PDFs -> parsed rows -> unified records.
Politeness: rate-limited, PDFs cached on disk (re-runs are cheap).

Usage:
  python cyclist_crawl.py            # full 2024-2026 run
  python cyclist_crawl.py --limit 3  # only first 3 events (smoke test)
"""
import argparse
import hashlib
import json
import os
import re
import sys
import pdfplumber

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.cyclist.org.tw"
PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdf", "cyclist")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# Events that were in the dataset but have since been removed from the category
# listing pages (their result pages + PDFs still exist). (pno, year, title, category)
DELISTED_EVENTS = [
    ("99", 2020, "扶輪盃陽明山自行車登山王挑戰", 1),
    ("149", 2025, "環花東國際自行車賽", 13),
    # the listing links the 2026 環大臺北 entry to its certificate page (169);
    # the results PDFs are on the unlisted sibling page 168
    ("168", 2026, "環大臺北自行車挑戰 成績", 4),
    # Result pages no listing links to (found by scanning every pno, 2026-11-03).
    # Year from the PDF upload names; each checked against master for a sibling
    # page with the same race-year (e.g. 137/147/143 duplicate 136/148/144).
    # Pre-2021 unlisted pages (unreliable years) and 108 (2021 日月潭, PDF layout
    # the parser can't read) are listed in data/known_races.json instead.
    ("109", 2021, "環花東自行車競賽&挑戰", 13),
    ("117", 2022, "環花東自行車競賽&挑戰", 13),
    ("118", 2022, "DOSUN 蘇花公路爬坡計時賽&挑戰", 1),
    ("120", 2022, "DOSUN 太平山自行車賽&挑戰", 1),
    ("135", 2024, "陽明山王 公路賽.團隊計時賽&挑戰", 1),
    ("139", 2024, "太平山王 公路賽.團隊計時賽&挑戰", 1),
    ("141", 2024, "環花東-團隊計時賽&公路賽", 13),
    ("145", 2024, "雲林公路繞圈賽", 13),
    ("146", 2025, "陽明山王公路賽.團隊計時賽&挑戰", 1),
]
YEARS = {2024, 2025, 2026}  # default; override with --years (e.g. 2014-2023 backfill)
# category listing pages (pno) that hold competitive ROAD events
CATEGORIES = {
    1: "KOM登山王挑戰", 2: "俱樂部聯賽", 3: "登山王之路", 4: "環大臺北",
    11: "花蓮太平洋盃", 12: "TAIWAN SUMMIT SERIES", 13: "臺灣自行車聯賽",
}

TIME = r"\d{1,2}:\d{2}:\d{2}(?:\.\d{1,2})?"
_TIME_RE = re.compile(TIME)
_LEAD = re.compile(r"^(?P<rank>\d{1,4})\s+(?P<bib>\d{1,5})\s+(?P<rest>.+)$")
_NATDIV = re.compile(r"^(?P<name>.+?)\s+(?P<nat>[A-Z]{3})\s+(?P<rest>.+)$")
_DIVHEAD = re.compile(r"^(?P<name>.+?)\s+(?P<div>" + common.DIV_TOKEN + r")(?:\s+(?P<rest>.*))?$")


def detect_order(page_text):
    """Read the Chinese header row to learn column order of 姓名/國籍/組別/車隊.
    Returns 'natdiv' (Nat before Div, glued div+team) or 'divnat' (Div before Nat)."""
    for ln in page_text.splitlines():
        if "姓名" in ln and "組別" in ln and ("完成時間" in ln or "編號" in ln):
            i_nat, i_div = ln.find("國籍"), ln.find("組別")
            if i_nat != -1 and i_nat < i_div:
                return "natdiv"
            return "divnat"
    return "natdiv"  # default: most PDFs are Nat-before-Div


def parse_row(line, order):
    lm = _LEAD.match(line)
    if not lm:
        return None
    rest = lm.group("rest")
    times = _TIME_RE.findall(rest)
    if not times:
        return None
    mid = rest[:rest.find(times[0])].strip()
    name = nat = div = team = None
    if order == "natdiv":
        mm = _NATDIV.match(mid)
        if not mm:
            return None
        name, nat = mm.group("name").strip(), mm.group("nat")
        div, team = common.split_division_team(mm.group("rest"))
    else:  # divnat: name DIV team [NAT]
        mm = _DIVHEAD.match(mid)
        if not mm:
            return None
        name, div = mm.group("name").strip(), mm.group("div")
        rest2 = (mm.group("rest") or "").strip()
        if re.fullmatch(r"[A-Z]{3}", rest2):           # nationality only, no team
            nat, team = rest2, None
        elif (nm := re.match(r"^(.+?)\s([A-Z]{3})$", rest2)):  # team + trailing nationality
            team, nat = nm.group(1).strip() or None, nm.group(2)
        else:
            team = rest2 or None
    g, age = common.parse_division(div)
    return {"rank": int(lm.group("rank")), "bib": lm.group("bib"), "name": name,
            "nat": nat, "div": div, "gender": g, "age_group": age, "team": team,
            "splits": times[:-1], "finish": times[-1]}


def list_events(session, cat_pno, cat_name):
    """Return [(event_pno, title, year)] from a category listing page."""
    url = f"{BASE}/results_list.asp?pno={cat_pno}"
    r = common.polite_get(session, url)
    r.encoding = r.apparent_encoding or "utf-8"
    html = r.text
    events = []
    for m in re.finditer(r'results_txt\.asp\?pno=(\d+)', html):
        # current layout: <h2>2025 環大臺北自行車挑戰 成績</h2> <ul><li><a results_txt…>
        h2 = re.findall(r"(?s)<h2[^>]*>(.*?)</h2>", html[max(0, m.start() - 600):m.start()])
        if h2:
            title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h2[-1])).strip()
            events.append((m.group(1), title, common.extract_year(title)))
            continue
        pre = re.sub(r"<[^>]+>", " ", html[max(0, m.start() - 500):m.start()])
        pre = re.sub(r"\s+", " ", pre).strip()
        # title sits right before the "活動簡介＆證書下載" marker
        mt = re.search(r"([^ ].{0,60}?)\s*活動簡介", pre)
        title = mt.group(1).strip() if mt else pre[-50:]
        events.append((m.group(1), title, common.extract_year(title)))
    # de-dup event pnos, keep first title seen
    seen, out = set(), []
    for pno, title, yr in events:
        if pno in seen:
            continue
        seen.add(pno)
        out.append((pno, title, yr))
    return out


def event_pdfs(session, event_pno):
    """Return (clean_title, date_str, [(label, pdf_url)]) for an event page."""
    url = f"{BASE}/results_txt.asp?pno={event_pno}"
    r = common.polite_get(session, url)
    r.encoding = r.apparent_encoding or "utf-8"
    html = r.text
    t = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = common.canonical_race_name(t.group(1)) if t else ""
    anchors = re.findall(r'<a[^>]+href=["\']([^"\']+\.pdf)["\'][^>]*>(.*?)</a>', html, re.S | re.I)
    pdfs = []
    for href, txt in anchors:
        label = re.sub(r"<[^>]+>", "", txt)
        label = re.sub(r"\s+", " ", label).strip()
        if "行事曆" in label or "積分" in label and "排名" not in label:
            continue
        pdfs.append((label, href))
    # date from any /YYYYMMDD/ in the pdf urls
    date = None
    for _, href in pdfs:
        dm = re.search(r"/(20\d{6})/", href)
        if dm:
            d = dm.group(1)
            date = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            break
    return title, date, pdfs


def local_name(href):
    """Cache file name. Old names turned every CJK char into '_', so pdfs like
    41/菁英組成績.pdf and 41/市民組成績.pdf (same length) shared one file.
    ASCII-only hrefs keep their old name; the rest get a hash of the URL."""
    flat = href.strip("/").replace("/", "_")
    safe = re.sub(r"[^0-9A-Za-z._-]", "_", flat)
    if safe == flat:
        return safe
    stem = safe[:-4] if safe.lower().endswith(".pdf") else safe
    return f"{stem[:60]}-{hashlib.md5(href.encode()).hexdigest()[:8]}.pdf"


def download_pdf(session, href):
    url = href if href.startswith("http") else f"{BASE}/{href.lstrip('/')}"
    path = os.path.join(PDF_DIR, local_name(href))
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    r = common.polite_get(session, url)
    if r.status_code == 200 and r.content[:4] == b"%PDF":
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    return None


def parse_pdf_rows(path):
    rows = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                order = detect_order(text)
                for line in text.splitlines():
                    row = parse_row(line.strip(), order)
                    if row:
                        rows.append(row)
    except Exception as e:
        print(f"      ! parse error {os.path.basename(path)}: {e}")
    return rows


def pick_pdfs(pdfs):
    """Prefer overall (總排名) PDFs (full field + division); fall back to 分組排名."""
    overall = [(l, h) for l, h in pdfs if "總排名" in l and "積分" not in l]
    if overall:
        return overall
    return [(l, h) for l, h in pdfs if "排名" in l and "積分" not in l]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--years", default="2024-2026",
                    help="year range to crawl, e.g. '2024-2026' or '2014-2023' (backfill)")
    ap.add_argument("--out", default="cyclist_2024_2026.json",
                    help="output filename under data/processed/")
    args = ap.parse_args()
    global YEARS
    lo, hi = (int(x) for x in args.years.split("-")) if "-" in args.years else (int(args.years),) * 2
    YEARS = set(range(lo, hi + 1))

    s = common.make_session()
    records, seen_rows = [], set()
    stamp = "2026-06-04"
    events_done = 0

    for cat_pno, cat_name in CATEGORIES.items():
        try:
            events = list_events(s, cat_pno, cat_name)
        except Exception as e:
            print(f"[cat {cat_pno} {cat_name}] LIST ERROR {e}")
            continue
        kept = [e for e in events if e[2] in YEARS]
        kept += [(pno, f"(delisted) {t}", y) for pno, y, t, cat in DELISTED_EVENTS
                 if cat == cat_pno and y in YEARS and pno not in {e[0] for e in events}]
        print(f"\n[cat {cat_pno} {cat_name}] events={len(events)} in-range({min(YEARS)}-{max(YEARS)})={len(kept)}")
        for event_pno, ltitle, yr in kept:
            if args.limit and events_done >= args.limit:
                break
            title, date, pdfs = event_pdfs(s, event_pno)
            chosen = pick_pdfs(pdfs)
            print(f"   - {yr} {title[:36]:<36} pdfs={len(pdfs)} parse={len(chosen)} date={date}")
            n_before = len(records)
            for label, href in chosen:
                path = download_pdf(s, href)
                if not path:
                    continue
                for row in parse_pdf_rows(path):
                    key = (event_pno, row["bib"], row["finish"])
                    if key in seen_rows:
                        continue
                    seen_rows.add(key)
                    records.append(common.make_record(
                        source_platform="cyclist.org.tw",
                        source_url=f"{BASE}/results_txt.asp?pno={event_pno}",
                        source_format="pdf",
                        race_name_raw=title, year=yr, date=date,
                        race_type="road", region=None,
                        result_label=label, category_raw=row["div"],
                        gender=row["gender"], age_group=row["age_group"],
                        rank_overall=row["rank"], bib=row["bib"],
                        name_raw=row["name"], nationality=row["nat"], team=row["team"],
                        finish_time=row["finish"], splits=row["splits"],
                        scraped_at=stamp))
            print(f"        +{len(records) - n_before} rows")
            events_done += 1
        if args.limit and events_done >= args.limit:
            break

    # global dedup: same race (across category listings / name variants) + bib + time
    deduped, seen = [], set()
    for r in records:
        k = (r["race_key"], r["year"], r["bib"], r["finish_time"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(r)
    dropped = len(records) - len(deduped)
    records = deduped
    print(f"\n  dedup: removed {dropped} cross-listed/duplicate rows -> {len(records)}")

    # outputs: full (with raw names, internal) + de-identified (public)
    full = os.path.join(OUT_DIR, args.out)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    pub = [{k: v for k, v in r.items() if k != "name_raw"} for r in records]
    pubp = os.path.join(OUT_DIR, args.out.replace(".json", ".public.json"))
    with open(pubp, "w", encoding="utf-8") as f:
        json.dump(pub, f, ensure_ascii=False, indent=2)

    races = {(r["race_name_canonical"], r["year"]) for r in records}
    print(f"\n=== DONE === records={len(records)} distinct races={len(races)}")
    print(f"  -> {os.path.relpath(full)}  (+ .public.json de-identified)")
    gd = {}
    for r in records:
        gd[r["gender"]] = gd.get(r["gender"], 0) + 1
    print(f"  gender dist: {gd}")


if __name__ == "__main__":
    main()
