# -*- coding: utf-8 -*-
"""Pure HTML parsers for criterium.tw (events.criterium.tw) results pages.
No HTTP here — criterium_crawl.py fetches; these functions parse, so they are
unit-testable against fixtures. The results table is server-rendered static
HTML (<table class="tbl">), 8 columns: # / BIB / 姓名 / 分組 / 隊伍 / 完賽時間
/ 圈數 / 狀態. Status TEXT inside the pill span is authoritative (a DNS row may
carry class "pill dnf" but text "DNS")."""
import json
import os
import re
import sys
from html import unescape

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

_TABLE = re.compile(r'<table class="tbl">.*?</table>', re.S)
_ROW = re.compile(r'<tr class="row-link">(.*?)</tr>', re.S)
_CELL = re.compile(r'<td\b[^>]*>(.*?)</td>', re.S)
_TAG = re.compile(r'<[^>]+>')
_H1 = re.compile(r'<h1[^>]*>(.*?)</h1>', re.S)
_LDJSON = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
_EVENT_HREF = re.compile(r'/races/\d+/events/(\d+)')
_TIME = re.compile(r'\d{1,2}:\d{2}:\d{2}')


def _text(frag):
    """Strip HTML comments + tags + record-marker stars, collapse whitespace."""
    s = re.sub(r'<!--.*?-->', '', frag or '', flags=re.S)
    s = _TAG.sub('', s)
    s = unescape(s).replace('★', '').replace('☆', '')
    return re.sub(r'\s+', ' ', s).strip()


def event_name(html):
    m = _H1.search(html or '')
    return _text(m.group(1)) if m else None


def parse_event_page(html):
    """Return a list of row dicts from a criterium event results page."""
    mt = _TABLE.search(html or '')
    if not mt:
        return []
    out = []
    for rm in _ROW.finditer(mt.group(0)):
        cells = [_text(c) for c in _CELL.findall(rm.group(1))]
        if len(cells) < 8:
            continue
        rank_s, bib, name, category, team, ftime, laps_s, status = cells[:8]
        rank = int(rank_s) if rank_s.isdigit() else None
        laps = int(laps_s) if laps_s.isdigit() else None
        ftime = ftime if _TIME.match(ftime) else None
        status = status.upper() if status.upper() in ('FIN', 'DNF', 'DNS') else None
        out.append({"rank": rank, "bib": bib or None, "name": name or None,
                    "category": category or None, "team": team or None,
                    "finish_time": ftime, "laps": laps, "status": status})
    return out


def parse_category(cat):
    """'M / M30' -> ('M','30'); 'M / U23' -> ('M','U23'); 'M / ELITE' -> ('M',None)."""
    if not cat:
        return None, None
    parts = [p.strip() for p in cat.split('/')]
    head = parts[0]
    if head.startswith(('M', 'm', '男')):
        gender = 'M'
    elif head.startswith(('W', 'w', 'F', 'f', '女')):
        gender = 'F'
    else:
        gender = None
    sub = parts[1] if len(parts) > 1 else parts[0]
    g2, age = common.parse_division(sub)
    return (gender or g2), age


def parse_race_meta(html):
    """Extract race name/date/year/region + event sub-page ids from the overview page."""
    name = date = region = year = None
    for blob in _LDJSON.findall(html or ''):
        try:
            d = json.loads(blob)
        except ValueError:
            continue
        for it in (d if isinstance(d, list) else [d]):
            if it.get('@type') == 'SportsEvent':
                name = it.get('name') or name
                date = it.get('startDate') or date
                loc = it.get('location')
                if isinstance(loc, dict):
                    region = loc.get('name') or region
                elif isinstance(loc, str):
                    region = loc or region
    if not name:
        name = event_name(html)
    if date:
        year = common.extract_year(date)
    if region:
        region = re.split(r'[·•・]', region)[0].strip() or None
    seen, event_ids = set(), []
    for n in _EVENT_HREF.findall(html or ''):
        i = int(n)
        if i not in seen:
            seen.add(i)
            event_ids.append(i)
    return {"name": name, "date": date, "year": year, "region": region,
            "event_ids": event_ids}
