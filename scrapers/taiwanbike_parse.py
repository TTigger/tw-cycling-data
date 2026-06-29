# -*- coding: utf-8 -*-
"""Pure parsers for TBA (中華民國自行車協會) results on taiwanbike.org.

Two pieces, both HTTP-free so they're unit-testable:
- extract_sheet_links: pull Google-Sheet result links (2022+) from the listing page.
- map_row: map one xlsx row to unified fields, tolerant to per-event schema drift
  (synonym columns, a duplicated 組別 header where one value is the event name and
  the other an age-group code, gun-vs-chip time). Source rank is ignored (rank is
  re-derived by the frontend from category+time)."""
import re

_SHEET = re.compile(
    r'<a\s+href="https://docs\.google\.com/spreadsheets/d/([\w-]+)[^"]*"[^>]*>(.*?)</a>',
    re.S)
_YEAR = re.compile(r"(20\d{2})")
_AGECODE = re.compile(r"^(?:[MWFmwf]\d{1,2}|U\d{1,2}|MASTER|[男女]\d{1,2})$")
_TIME = re.compile(r"^\d{1,2}:\d{2}:\d{2}")

# column-name synonyms (first match wins, scanning all columns)
_BIB = ("參加編號", "參賽編號", "選手編號", "號碼布", "號碼")
_NAME = ("姓名",)
_TEAM = ("隊名", "車隊", "隊伍")
_GENDER = ("性別",)
_GROUP = ("組別", "分組", "性別組")
_FINISH = ("淨時間", "晶片成績", "大會成績", "總成績", "成績")   # priority order (淨時間= net/chip time)


def extract_sheet_links(html):
    out = []
    for sid, title in _SHEET.findall(html or ""):
        title = re.sub(r"<[^>]+>", "", title).strip()
        y = _YEAR.search(title)
        year = int(y.group(1)) if y else None
        if year is None or year < 2022:
            continue
        out.append({"title": title, "year": year, "sheet_id": sid})
    return out


def _cells(header, row):
    """All (name, value) pairs; names may repeat (duplicated 組別)."""
    return [(str(h).strip(), ("" if v is None else str(v)).strip())
            for h, v in zip(header, row)]


def _first(cells, names):
    for want in names:                       # priority order
        for h, v in cells:
            if h == want and v:
                return v
    return None


def map_row(header, row):
    cells = _cells(header, row)
    finish = _first(cells, _FINISH)
    if not finish or not _TIME.match(finish):
        return None
    # age-group code: among 組別/分組 columns, prefer the one that looks like a code
    group = None
    for h, v in cells:
        if h in _GROUP and _AGECODE.match(v):
            group = v
            break
    if group is None:                        # fall back to first non-empty group col
        group = _first(cells, _GROUP)
    gender = _first(cells, _GENDER)
    g = "M" if gender in ("男", "M") else "F" if gender in ("女", "W", "F") else None
    if g is None and group:
        g = "M" if group[:1] in ("M", "男") else "F" if group[:1] in ("W", "F", "女") else None
    return {"bib": _first(cells, _BIB), "name": _first(cells, _NAME),
            "team": _first(cells, _TEAM), "category": group, "gender": g,
            "finish_time": finish}
