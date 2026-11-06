# -*- coding: utf-8 -*-
"""cyclist.org.tw result pages that no category listing links to (2013-2021).

Found by scanning every results_txt.asp?pno (2026-11-03) and kept in
data/known_races.json as FOUND until this module. Their PDFs come in about six
layouts (2013-2015 club league, 2016-2017 KOM, 2018-2021 滿天星 / Taiwan Cup).
Foreign riders' names are several words long and sit next to the team, so a
whitespace split can't tell name from team. Instead each word goes to the
column whose header sits above it (pdfplumber word x positions).

The year comes from the PDF header ("2018 ALL STAR Challenge Series"), not the
page: many pages carry a shared 2017 calendar PDF whose upload date is wrong.

  python scrapers/cyclist_archive.py
Output: data/processed/cyclist_archive.json (merge.py globs cyclist_*).
"""
import json
import os
import re
import sys

import pdfplumber

sys.path.insert(0, os.path.dirname(__file__))
import common          # noqa: E402
import cyclist_crawl   # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "cyclist_archive.json")

# pno -> (year, race name used by later editions, date, label filter)
# `take` lists substrings of the PDF link labels to parse. Each listed PDF is a
# full field; 分組排名 copies and 前六名 / team / points sheets are left out.
PAGES = {
    "41":  (2013, "全國俱樂部聯賽-第8站彰濱工業區公路繞圈賽", "2013-08-04", ["菁英組成績", "市民組成績", "女子總排名"]),
    "23":  (2014, "全國俱樂部聯賽-第5站彰濱工業區公路繞圈賽", None, ["各分組總排名"]),
    "24":  (2014, "全國俱樂部聯賽-第6站阿里山自行車賽", None, ["各分組總排名"]),
    "25":  (2014, "全國俱樂部聯賽-第7站玉山塔塔加自行車賽", None, ["各分組總排名"]),
    "43":  (2014, "全國俱樂部聯賽-第3站環東台灣自行車賽", "2014-04-13", ["R1R2分組總排名", "R3R4分組總排名"]),
    "13":  (2015, "全國俱樂部聯賽-第2站台南四草公路繞圈賽", "2015-03-22", ["總排名"]),
    "73":  (2016, "臺灣自行車登山王挑戰", None, ["Result Overall"]),
    "57":  (2017, "臺灣KOM登山王之路-春季", "2017-04-17", ["總排名"]),
    "74":  (2017, "臺灣自行車登山王挑戰", "2017-10-20", ["Result Overall"]),
    "75":  (2018, "扶輪盃北海櫻木花道", "2018-03-10", ["總排名"]),
    "76":  (2018, "環花東365超級挑戰", "2018-04-21", ["總排名"]),
    "77":  (2018, "環海岸山脈挑戰", "2018-05-12", ["總排名"]),
    "79":  (2018, "臺灣KOM登山王之路-春季", "2018-04-23", ["總排名"]),
    "78":  (2018, "詩情畫意羅馬公路挑戰", "2018-07-07", ["總排名"]),
    "80":  (2018, "臺灣KOM登山王之路-夏季", "2018-07-14", ["總排名"]),
    "83":  (2018, "陽明山自行車登山王挑戰", None, ["Result Overall"]),
    "82":  (2018, "臺灣自行車登山王挑戰", "2018-10-26", ["Result Overall"]),
    "87":  (2018, "日月潭Come!Bikeday", "2018-11-17", ["總排名"]),
    "88":  (2019, "扶輪盃北海櫻木花道", "2019-03-09", ["總排名"]),
    "89":  (2019, "環花東365超級挑戰", "2019-04-20", ["總排名"]),
    "90":  (2019, "環海岸山脈挑戰", "2019-05-11", ["總排名"]),
    "92":  (2019, "詩情畫意羅馬公路挑戰", "2019-07-06", ["總排名"]),
    "91":  (2019, "臺灣KOM登山王之路-夏季", "2019-06-29", ["總排名"]),
    "96":  (2019, "臺灣自行車登山王挑戰", "2019-10-25", ["Result Overall"]),
    "104": (2020, "日月潭Come!Bikeday", "2020-10-31", ["總排名"]),
    # 11/29 競賽組 only has a two-day total (分組排名), not a stage result
    "105": (2020, "環花東365超級挑戰", "2020-11-28", ["總排名"]),
    "108": (2021, "日月潭Come!Bikeday", "2021-03-20", ["總排名"]),
}

FIELDS = {
    "rank": {"總排名", "總排", "Place", "Rank", "GC", "名次"},
    "divtot": {"Div/Tot"},   # place within category; kept out of rank_overall
    "bib": {"編號", "個編", "選手號碼", "No.", "NO.", "No"},
    "name": {"姓名", "Name"},
    "div": {"組別", "分組", "DIV", "Div", "Div.", "Cat."},
    "team": {"車隊", "團體", "TEAM", "Team"},
    "nat": {"國籍", "Nat.", "Nat"},
    "time": {"完成時間", "Time", "Wuling", "Finish"},
}
LABEL = {w: f for f, ws in FIELDS.items() for w in ws}
TIME_RE = re.compile(r"(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\.\d{1,3})?")
STATUS = {"DNF", "DNS", "DSQ", "OTL", "DQ"}


def _lines(page):
    words = page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False)
    rows = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if rows and abs(rows[-1][0] - w["top"]) <= 2.5:
            rows[-1][1].append(w)
        else:
            rows.append([w["top"], [w]])
    return [sorted(ws, key=lambda w: w["x0"]) for _, ws in rows]


def _header(ws):
    """Header words [(x0, x1, field)] when this line is a table header."""
    texts = [w["text"] for w in ws]
    if not ({"姓名", "Name"} & set(texts)) or not any(LABEL.get(t) == "time" for t in texts):
        return None
    return [(w["x0"], w["x1"], LABEL.get(w["text"])) for w in ws]


def _columns(rows):
    """Column x-ranges: runs of x covered by some data row's ink. Gaps no row
    writes across are the gutters between columns."""
    if not rows:
        return []
    right = int(max(w["x1"] for ws in rows for w in ws)) + 2
    ink = [False] * right
    for ws in rows:
        for w in ws:
            for x in range(int(w["x0"]), int(w["x1"]) + 1):
                ink[x] = True
    cols, start = [], None
    for x, on in enumerate(ink + [False]):
        if on and start is None:
            start = x
        elif not on and start is not None:
            cols.append((start, x))
            start = None
    return cols


def _split_tight(cols, header):
    """Tightly set tables (2013 league) leave no gutter between some columns;
    split a column that sits under two or more header labels at their x0."""
    out = []
    for a, b in cols:
        inside = [hx0 for hx0, hx1, f in header if a <= (hx0 + hx1) / 2 <= b]
        cuts = [int(x) for x in sorted(inside)[1:] if a < x < b]
        edges = [a] + cuts + [b]
        out += [(edges[k], edges[k + 1] - (1 if k + 1 < len(edges) - 1 else 0))
                for k in range(len(edges) - 1)]
    return out


def _field_map(cols, header):
    """Column index -> field. Labels first take the column they overlap most;
    a label left over (short names make a narrow column that doesn't reach
    under 姓名) takes the nearest free column between its neighbours' columns.
    An empty rank column on a DNF page leaves no column there, so 名次 gets
    nothing instead of stealing the name column."""
    if not cols:
        return {}
    labels = [(hx0, hx1, f) for hx0, hx1, f in header if f]
    cand = []
    for j, (hx0, hx1, f) in enumerate(labels):
        for i, (a, b) in enumerate(cols):
            ov = min(b, hx1) - max(a, hx0)
            if ov > 0:
                cand.append((ov, i, j))
    col_of = {}
    for ov, i, j in sorted(cand, reverse=True):
        if j not in col_of and i not in col_of.values():
            col_of[j] = i
    for j, (hx0, hx1, f) in enumerate(labels):
        if j in col_of:
            continue
        lo = max((col_of[k] for k in col_of if k < j), default=-1)
        hi = min((col_of[k] for k in col_of if k > j), default=len(cols))
        free = [i for i in range(lo + 1, hi) if i not in col_of.values()]
        if free:
            mid = (hx0 + hx1) / 2
            col_of[j] = min(free, key=lambda i: abs((cols[i][0] + cols[i][1]) / 2 - mid))
    out = {i: labels[j][2] for j, i in col_of.items()}
    # a text column can split in two where no row bridges a word gap; give an
    # unlabelled piece to the text column it nearly touches
    for i in range(len(cols)):
        if i in out:
            continue
        for k in (i + 1, i - 1):
            if out.get(k) in ("name", "team", "div"):
                gap = cols[k][0] - cols[i][1] if k > i else cols[i][0] - cols[k][1]
                if gap < 8:
                    out[i] = out[k]
                    break
    return out


def _cells(ws, cols, fmap):
    out = {}
    for w in ws:
        mid = (w["x0"] + w["x1"]) / 2
        i = next((k for k, (a, b) in enumerate(cols) if a - 1 <= mid <= b + 1), None)
        if i is None:
            continue
        out.setdefault(fmap.get(i, f"_{i}"), []).append(w["text"])
    return out


def _gender(div):
    d = (div or "").upper()
    if re.match(r"^(W|F|女|RW|WE)", d) or "女" in d or "WOMEN" in d:
        return "F"
    if re.match(r"^(M|男|RM|RE|ELITE)", d) or "男" in d or "菁英" in d:
        return "M"
    return None


def parse_row(cells):
    rank_t = " ".join(cells.get("rank", []))
    bib = " ".join(cells.get("bib", []))
    name = " ".join(cells.get("name", [])).strip()
    times = [t for t in cells.get("time", []) if TIME_RE.fullmatch(t)]
    status = next((t.upper() for v in cells.values() for t in v if t.upper() in STATUS), None)
    if not name or not re.fullmatch(r"\d{1,4}", bib):  # 2014 prints 0017
        return None
    rank = int(rank_t) if rank_t.isdigit() else None
    if not times and not status:
        return None
    ft = times[-1] if times and not status else None
    secs = common.time_to_seconds(ft) if ft else None
    if ft and ft.count(":") == 1:  # 2013 league prints MM:SS
        m, s = ft.split(":")
        ft = f"00:{int(m):02d}:{s}"
        secs = common.time_to_seconds(ft)
    if secs is not None and secs <= 0:
        return None
    team = " ".join(cells.get("team", []))
    team = TIME_RE.sub("", team).strip() or None
    div = " ".join(cells.get("div", [])) or None
    return {"rank": rank, "bib": bib, "name": name, "div": div, "team": team,
            "nat": " ".join(cells.get("nat", [])) or None,
            "time": ft, "secs": secs, "status": status}


def _is_data(ws):
    """A rider row: starts with a rank / bib / n-of-total or a status, and
    carries a time or a status. Page titles ("365KM Challenge ... 06:00") don't."""
    first = ws[0]["text"].upper()
    second = ws[1]["text"] if len(ws) > 1 else ""
    lead_cat = re.fullmatch(r"[A-Z]{1,3}\d{0,2}", first) and second.isdigit()  # 2014 "RM15 185 ..."
    if not (re.fullmatch(r"\d{1,4}(?:/\d{1,4})?", first) or first in STATUS or lead_cat):
        return False
    return any(TIME_RE.fullmatch(w["text"]) or w["text"].upper() in STATUS for w in ws)


def _blocks(page, header=None):
    """(header, data rows) for each table on the page. `header` carries over
    from the previous page: most books print it on page 1 only."""
    rows, out = [], []
    for ws in _lines(page):
        h = _header(ws)
        if h:
            if header:
                out.append((header, rows))
            header, rows = h, []
        elif header and _is_data(ws):
            rows.append(ws)
    if header:
        out.append((header, rows))
    return out


def _sequential(cells, field):
    """Share of rows whose value is the previous row's + 1 (a rank column)."""
    vals = [" ".join(c.get(field, [])) for c in cells]
    hits = sum(1 for a, b in zip(vals, vals[1:]) if a.isdigit() and b.isdigit() and int(b) == int(a) + 1)
    return hits / max(1, len(vals) - 1)


def parse_block(header, data):
    """Rider rows of one table (header line + its data lines)."""
    if not data:
        return []
    cols = _split_tight(_columns(data), header)
    fmap = _field_map(cols, header)
    cells = [_cells(ws, cols, fmap) for ws in data]
    if _sequential(cells, "bib") > 0.5 > _sequential(cells, "rank") and "rank" in fmap.values():
        # the labels sit over the wrong number column (編號 總排名)
        for c in cells:
            c["bib"], c["rank"] = c.get("rank", []), c.get("bib", [])
    return [r for r in map(parse_row, cells) if r]


def parse_pdf(path):
    rows = []
    header = None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for header, data in _blocks(page, header):
                rows += parse_block(header, data)
    return rows


def pick(pdfs, take):
    out = []
    for label, href in pdfs:
        if not label or label.startswith("請按此") or "積分" in label or "前六名" in label:
            continue
        hit = [t for t in take if t in label]
        # 分組排名 repeats the 總排名 riders; only take it when asked for by name
        if hit and ("分組排名" not in label or any("分組排名" in t for t in hit)) \
                and (label, href) not in out:
            out.append((label, href))
    return out


def main():
    s = common.make_session()
    records = []
    for pno, (year, race, date, take) in PAGES.items():
        _, _, pdfs = cyclist_crawl.event_pdfs(s, pno)
        chosen = pick(pdfs, take)
        n0 = len(records)
        seen = set()
        for label, href in chosen:
            path = cyclist_crawl.download_pdf(s, href)
            if not path:
                print(f"   ! {pno} download failed: {label}")
                continue
            for r in parse_pdf(path):
                # the same sheet is sometimes linked twice under two labels;
                # a rider on another day/stage has a different time
                key = (r["bib"], r["name"], r["secs"], r["status"])
                if key in seen:
                    continue
                seen.add(key)
                records.append(common.make_record(
                    source_platform="cyclist.org.tw",
                    source_url=f"{cyclist_crawl.BASE}/results_txt.asp?pno={pno}",
                    source_format="pdf", race_name_raw=race, year=year, date=date,
                    race_type="road", result_label=label, category_raw=r["div"],
                    gender=_gender(r["div"]), rank_overall=r["rank"], bib=r["bib"],
                    name_raw=r["name"], nationality=r["nat"], team=r["team"],
                    finish_time=r["time"], finish_seconds=r["secs"], status=r["status"],
                    scraped_at="2026-11-06"))
        print(f"{pno:>4} {year} {race[:26]:<26} pdfs={len(chosen)} rows={len(records) - n0}")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
    print(f"{len(records)} rows -> {OUT}")


if __name__ == "__main__":
    main()
