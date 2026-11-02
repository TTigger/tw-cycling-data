# -*- coding: utf-8 -*-
"""96聯賽 (96sporter.com) results published as PDF.

Since 2026 the 96 league is timed by Dynamic Intelligences and its results are no
longer on Bravelog / tsu: the organizer posts one PDF per stop (Dropbox link on
https://www.96sporter.com/player_rank.htm). This module downloads the PDFs in the
committed worklist data/raw/sporter96_pdfs.json and parses the per-category
"本站成績 / Stage Results" pages into unified records.

The PDF is read by text POSITION, not by plain text: long names and team names
wrap onto a second line, so plain text can't tell where a name ends and a team
begins. Column x-ranges come from the page's own header row (Rank/BIB/Name/Team/
Time/Gap/Points).

  python scrapers/sporter96_pdf.py            # download + parse every worklist entry
  python scrapers/sporter96_pdf.py --find     # list result-PDF links on 96sporter.com
                                              # (add new stops to the worklist by hand)
"""
import argparse
import json
import os
import re
import sys
import unicodedata

import requests

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
WORKLIST = os.path.join(ROOT, "data", "raw", "sporter96_pdfs.json")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "sporter96")
OUT_DIR = os.path.join(ROOT, "data", "processed")
SOURCE = "96sporter.com"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/124.0 Safari/537.36"}

STATUS = {"DNF", "DNS", "OTL", "DSQ"}
TIME = re.compile(r"\d{1,2}:\d{2}:\d{2}(?:\.\d+)?|\d{1,2}:\d{2}(?:\.\d+)?")
HEADER_COLS = ("Rank", "BIB", "Name", "Team", "Time", "Gap", "Points")
# 市民競賽組 = the masters (M30/M40…) categories; everything else is 競賽組.
CITIZEN = re.compile(r"M\d{2}")


def norm(s):
    """NFKC folds the CJK compatibility radicals the PDF font uses (⼦ -> 子, ⿈ -> 黃)."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s or "")).strip()


def page_fragments(page):
    """[(y, x, text)] for every text run on a pypdf page, in PDF user space (y up).

    pypdf, not pdfplumber (used by the other PDF sources): these PDFs' fonts have
    no FontBBox, so pdfplumber mis-measures glyphs and drops ~80% of the rows."""
    frags = []

    def visit(text, cm, tm, _font, _size):
        text = text.replace("\n", "")
        if not text:
            return
        x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
        y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
        frags.append((round(y, 1), round(x, 1), text))

    page.extract_text(visitor_text=visit)
    return frags


def lines_of(frags):
    """Group fragments into visual lines (same y), each sorted left-to-right.
    Glyphs of one text run share the run's start x, so the sort must be stable on
    x alone to keep their drawing order (sorting on text too scrambles names)."""
    by_y = {}
    for y, x, t in frags:
        by_y.setdefault(y, []).append((x, t))
    return [(y, sorted(v, key=lambda f: f[0]))
            for y, v in sorted(by_y.items(), key=lambda kv: -kv[0]) if "".join(t for _x, t in v).strip()]


def column_edges(lines):
    """Left x of each header column -> list of (name, x_start) sorted by x, or None."""
    starts = {}
    for _y, frs in lines:
        for x, t in frs:
            t = t.strip()
            if t in HEADER_COLS and t not in starts:
                starts[t] = x
    if not {"Rank", "BIB", "Name", "Team", "Time"} <= starts.keys():
        return None
    # Cells are drawn a little left of their header label (team text starts ~13pt
    # before "Team"), so split halfway between neighbouring header starts.
    cols = sorted(starts.items(), key=lambda kv: kv[1])
    edges = []
    for i, (name, x) in enumerate(cols):
        lo = -1e9 if i == 0 else (cols[i - 1][1] + x) / 2
        edges.append((name, lo))
    return edges


def col_of(x, edges):
    name = edges[0][0]
    for n, lo in edges:
        if x >= lo:
            name = n
    return name


def parse_stage_page(page):
    """-> (category, [row dict]) for a 本站成績 page, or (None, []) otherwise."""
    return parse_stage_lines(lines_of(page_fragments(page)))


def parse_stage_lines(lines):
    """Core of parse_stage_page on [(y, [(x, text)])] lines (testable without a PDF)."""
    text = norm(" ".join(t for _y, frs in lines for _x, t in frs))
    if "Stage Results" not in text:
        return None, []
    edges = column_edges(lines)
    if not edges:
        return None, []
    category = norm("".join(t for _x, t in lines[0][1]))
    header_y = min(y for y, frs in lines if any(t.strip() in HEADER_COLS for _x, t in frs))
    body = []                           # (y, cells) between the header and the footer
    for y, frs in lines:
        if y >= header_y - 20:          # title, header and its Chinese sub-header
            continue
        joined = "".join(t for _x, t in frs)
        if "Participants" in joined:
            break                       # footer: DNF/DNS counts + legend
        if "Report Created" in joined or "Timing and Results" in joined:
            continue                    # page footer timestamp
        if re.search(r"名\s*次|號\s*碼\s*布|姓\s*名", norm(joined)):
            continue                    # Chinese sub-header under Rank/BIB/Name
        if norm(joined).startswith("#"):
            continue                    # commissaire's note (penalties)
        cells = {}
        for x, t in frs:
            c = col_of(x, edges)
            cells[c] = cells.get(c, "") + t
        cells = {k: norm(v) for k, v in cells.items() if norm(v)}
        if cells:
            body.append((y, cells))
    anchors = [i for i, (_y, c) in enumerate(body)
               if re.fullmatch(r"\d+", c.get("Rank", "")) or c.get("Rank") in STATUS]
    if not anchors:
        return category, []
    # A wrapped cell is drawn vertically centred on its row, so its extra lines sit
    # above AND below the line that holds the rank: give each extra line to the
    # nearest rank line, then join every row's cells top-to-bottom.
    parts = {i: [body[i]] for i in anchors}
    for j, (y, cells) in enumerate(body):
        if j in parts:
            continue
        near = min(anchors, key=lambda i: abs(body[i][0] - y))
        # a centred wrapped name can start left of the Name column (in BIB/Rank)
        moved = {}
        for k, v in cells.items():
            k = "Name" if k in ("Rank", "BIB") else k
            moved[k] = norm(moved.get(k, "") + " " + v)
        parts[near].append((y, moved))
    rows = []
    for i in anchors:
        merged = {}
        for _y, cells in sorted(parts[i], key=lambda p: -p[0]):
            for k, v in cells.items():
                merged[k] = norm(merged.get(k, "") + " " + v)
        rows.append(merged)
    return category, rows


def to_record(cells, category, entry):
    rank_s = cells.get("Rank", "")
    status = rank_s if rank_s in STATUS else None
    # site status codes (web/src/lib/completion.ts): over time limit counts as a
    # did-not-finish, disqualified is "DQ".
    status = {"OTL": "DNF", "DSQ": "DQ"}.get(status, status)
    tm = cells.get("Time", "")
    tm = TIME.search(tm).group(0) if TIME.search(tm) else None
    name = cells.get("Name")
    if not name:
        return None
    team = cells.get("Team")
    if team in ("個人", "-", ""):
        team = None
    gender, age = common.parse_division(category)
    m = re.search(r"\bM(\d{2})\b", category) or re.search(r"\b(U\d{2})$", category)
    if m:
        age = m.group(1)                # 男子 M30 -> "30", 男子 U15 -> "U15" (as other sources)
    if re.search(r"女", category):
        gender = "F"
    elif re.search(r"男", category):
        gender = gender or "M"
    label = "市民競賽組" if CITIZEN.search(category) else "競賽組"
    return common.make_record(
        source_platform=SOURCE, source_url=entry["url"], source_format="pdf",
        race_name_raw=entry["race"], year=entry["year"], date=entry["date"],
        race_type="road", region=entry.get("region"),
        result_label=label, category_raw=category, gender=gender, age_group=age,
        rank_overall=int(rank_s) if rank_s.isdigit() else None,
        bib=cells.get("BIB"), name_raw=name, team=team,
        finish_time=tm if not status else None,
        finish_seconds=common.time_to_seconds(tm) if tm and not status else None,
        status=status or "FIN", scraped_at=entry.get("scraped_at"))


def parse_pdf(path, entry):
    import pypdf
    out, cats = [], []
    for page in pypdf.PdfReader(path).pages:
        cat, rows = parse_stage_page(page)
        if not cat:
            continue
        if cat not in cats:
            cats.append(cat)
        for cells in rows:
            r = to_record(cells, cat, entry)
            if r:
                out.append(r)
    return out, cats


def download(entry):
    os.makedirs(PDF_DIR, exist_ok=True)
    path = os.path.join(PDF_DIR, f"{entry['id']}.pdf")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    url = entry["url"]
    if "dropbox.com" in url:
        url = re.sub(r"([?&])dl=0", r"\1dl=1", url)
        if "dl=1" not in url:
            url += ("&" if "?" in url else "?") + "dl=1"
    r = requests.get(url, headers=UA, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise RuntimeError(f"{entry['id']}: not a PDF ({r.headers.get('content-type')})")
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def find_links():
    """Print candidate result-PDF links on the organizer's site (for curating the worklist)."""
    for page in ("player_rank.htm", "event.htm"):
        html = requests.get(f"https://www.96sporter.com/{page}", headers=UA, timeout=40).text
        for href, label in re.findall(r'href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
            label = norm(re.sub(r"<[^>]+>", "", label))
            if "dropbox" in href or href.lower().endswith(".pdf") or "成績" in label:
                print(f"{page}: {label or '-'}  {href}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--find", action="store_true")
    a = ap.parse_args()
    if a.find:
        find_links()
        return
    entries = json.load(open(WORKLIST, encoding="utf-8"))
    total = []
    for e in entries:
        recs, cats = parse_pdf(download(e), e)
        fin = sum(1 for r in recs if r["finish_seconds"])
        print(f"  {e['id']}: {len(recs)} rows ({fin} finishers) in {len(cats)} categories: {', '.join(cats)}")
        total.extend(recs)
    out = os.path.join(OUT_DIR, "sporter96_pdf.json")
    json.dump(total, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"96sporter PDF: {len(total)} rows -> {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
