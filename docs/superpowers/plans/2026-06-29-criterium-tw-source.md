# criterium.tw Source (DNF/laps + completion rate) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add criterium.tw as a 6th data source, capturing FIN/DNF/DNS status + lap counts (a first for the dataset), and show a completion-rate block on the /race page.

**Architecture:** A pure HTML parser (`criterium_parse.py`) + an HTTP crawler (`criterium_crawl.py`) emit unified records with two new fields (`status`, `laps`) via `common.make_record`. `merge.py` keeps DNF/DNS rows instead of dropping them. `build_viz.py` computes a per-race-year `completion` object in the races index; a `/race` React component renders it when present.

**Tech Stack:** Python 3 (`requests`, stdlib `re`/`json`/`html`), pytest; Astro + React + TypeScript, vitest.

## Global Constraints

- **PDPA de-identification**: public output carries only `name_masked`; `name_raw` lives only in internal `master.json`. `status`/`laps` are non-PII and may be public.
- **Pipeline shape**: scrapers write `data/processed/<source>_*.json`; `merge.py` auto-discovers files whose basename starts with a `SOURCE_PREFIXES` entry; build scripts read `master.public.json` → `web/public/data/*.json` (all committed; Vercel has no Python).
- **Source platform label**: pin `source_platform="criterium.tw"` (fetch via `events.criterium.tw`; canonical host alias is `events.seh.com.tw` — pin one to avoid duplicate race keys).
- **Per-feature workflow**: build → `python -m pytest scrapers/` → frontend → `npm test` → `npx astro check` → browser-verify → own commit.
- **Seed races (all 5)**: race ids `19554, 19267, 18931, 18772, 18571`.

---

### Task 1: Add `status` + `laps` to the unified record schema

**Files:**
- Modify: `scrapers/common.py` (the `make_record` dict, ~line 219-228)
- Test: `scrapers/test_common.py` (create)

**Interfaces:**
- Produces: `make_record(..., status=None, laps=None)` — record dict now always contains keys `"status"` (None | "FIN" | "DNF" | "DNS") and `"laps"` (None | int).

- [ ] **Step 1: Write the failing test**

Create `scrapers/test_common.py`:

```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import common


def test_make_record_defaults_status_and_laps_to_none():
    r = common.make_record(race_name_raw="苗栗繞圈賽（第七屆）", year=2026)
    assert r["status"] is None
    assert r["laps"] is None


def test_make_record_carries_status_and_laps():
    r = common.make_record(race_name_raw="苗栗繞圈賽（第七屆）", year=2026,
                           name_raw="洪稟詠", status="DNF", laps=25)
    assert r["status"] == "DNF"
    assert r["laps"] == 25
    assert r["finish_seconds"] is None  # DNF has no time
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_common.py -v`
Expected: FAIL — `KeyError: 'status'`.

- [ ] **Step 3: Add the two keys to the record dict**

In `scrapers/common.py`, in `make_record`, add `status` and `laps` to the default dict next to the finish fields:

```python
        "finish_time": None, "finish_seconds": None, "splits": None,
        "status": None, "laps": None,
        "scraped_at": None,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_common.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add scrapers/common.py scrapers/test_common.py
git commit -m "feat(schema): add status + laps fields to unified record"
```

---

### Task 2: criterium.tw pure HTML parsers

**Files:**
- Create: `scrapers/criterium_parse.py`
- Test: `scrapers/test_criterium_parse.py`

**Interfaces:**
- Produces:
  - `parse_event_page(html) -> list[dict]` with keys `rank`(int|None), `bib`(str|None), `name`(str|None), `category`(str|None), `team`(str|None), `finish_time`(str|None), `laps`(int|None), `status`('FIN'|'DNF'|'DNS'|None).
  - `event_name(html) -> str|None` (the `<h1>`, e.g. "男子A組").
  - `parse_category(cat) -> (gender, age_group)` e.g. `"M / M30" -> ("M","30")`, `"M / U23" -> ("M","U23")`.
  - `parse_race_meta(html) -> dict` with keys `name`(str|None), `date`(str|None), `year`(int|None), `region`(str|None), `event_ids`(list[int]).

- [ ] **Step 1: Write the failing test**

Create `scrapers/test_criterium_parse.py`:

```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import criterium_parse as cp

EVENT_HTML = (
    '<h1>男子A組</h1>'
    '<table class="tbl"><thead><tr><th>#</th><th>BIB</th><th>姓名</th>'
    '<th>分組</th><th>隊伍</th><th style="text-align:right">完賽時間</th>'
    '<th style="text-align:right">圈數</th><th>狀態</th></tr></thead><tbody>'
    '<tr class="row-link"><td class="rank"><span class="pos pos-1">01</span></td>'
    '<td class="tnum">2</td><td>馮俊凱<!-- --> <span class="mono">★</span></td>'
    '<td class="tnum">M<!-- --> / M30</td><td>.UTSUNOMIYA BLITZEN 宇都宮車隊</td>'
    '<td class="tnum">00:47:38</td><td class="tnum">35</td>'
    '<td><span class="pill fin"><span class="dot"></span>FIN</span></td></tr>'
    '<tr class="row-link"><td class="rank"><span class="pos">—</span></td>'
    '<td class="tnum">21</td><td>洪稟詠<!-- --> </td>'
    '<td class="tnum">M<!-- --> / U23</td><td>TEAM CYTO TRIGON</td>'
    '<td class="tnum">—</td><td class="tnum">25</td>'
    '<td><span class="pill dnf"><span class="dot"></span>DNF</span></td></tr>'
    '<tr class="row-link"><td class="rank"><span class="pos">—</span></td>'
    '<td class="tnum">13</td><td>朱耿宏<!-- --> </td>'
    '<td class="tnum">M<!-- --> / ELITE</td><td>MSG CYCLING TEAM 衝線單車</td>'
    '<td class="tnum">—</td><td class="tnum">0</td>'
    '<td><span class="pill dnf"><span class="dot"></span>DNS</span></td></tr>'
    '</tbody></table>'
)

OVERVIEW_HTML = (
    '<h1>苗栗繞圈賽</h1>'
    '<script type="application/ld+json">{"@type":"SportsEvent",'
    '"name":"苗栗繞圈賽（第七屆）","startDate":"2026-06-28",'
    '"location":{"@type":"Place","name":"苗栗·後龍"}}</script>'
    '<a href="/races/19554/events/4">男子A組</a>'
    '<a href="/races/19554/events/5">男子B組</a>'
    '<a href="/races/19554/events/4">dup</a>'
)


def test_event_name():
    assert cp.event_name(EVENT_HTML) == "男子A組"


def test_parse_event_page_fin_row():
    rows = cp.parse_event_page(EVENT_HTML)
    assert len(rows) == 3
    fin = rows[0]
    assert fin["rank"] == 1
    assert fin["bib"] == "2"
    assert fin["name"] == "馮俊凱"        # ★ marker stripped
    assert fin["category"] == "M / M30"
    assert fin["team"] == ".UTSUNOMIYA BLITZEN 宇都宮車隊"
    assert fin["finish_time"] == "00:47:38"
    assert fin["laps"] == 35
    assert fin["status"] == "FIN"


def test_parse_event_page_dnf_and_dns():
    rows = cp.parse_event_page(EVENT_HTML)
    dnf, dns = rows[1], rows[2]
    assert dnf["status"] == "DNF" and dnf["rank"] is None
    assert dnf["finish_time"] is None and dnf["laps"] == 25
    # DNS row carries class "pill dnf" but TEXT "DNS" — text wins:
    assert dns["status"] == "DNS" and dns["laps"] == 0


def test_parse_category():
    assert cp.parse_category("M / M30") == ("M", "30")
    assert cp.parse_category("M / U23") == ("M", "U23")
    assert cp.parse_category("M / ELITE") == ("M", None)


def test_parse_race_meta():
    m = cp.parse_race_meta(OVERVIEW_HTML)
    assert m["name"] == "苗栗繞圈賽（第七屆）"
    assert m["date"] == "2026-06-28"
    assert m["year"] == 2026
    assert m["region"] == "苗栗"
    assert m["event_ids"] == [4, 5]   # de-duped, in order
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_criterium_parse.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'criterium_parse'`.

- [ ] **Step 3: Write the parser**

Create `scrapers/criterium_parse.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_criterium_parse.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add scrapers/criterium_parse.py scrapers/test_criterium_parse.py
git commit -m "feat(criterium): pure HTML parsers for events.criterium.tw results"
```

---

### Task 3: criterium.tw crawler (record builder + HTTP orchestration)

**Files:**
- Create: `scrapers/criterium_crawl.py`
- Test: `scrapers/test_criterium_crawl.py`

**Interfaces:**
- Consumes: `criterium_parse.parse_event_page`, `parse_race_meta`, `event_name`, `parse_category`; `common.make_record`, `common.make_session`, `common.polite_get`.
- Produces:
  - `build_records(parsed_rows, race_meta, event_label, event_url, scraped_at) -> list[dict]` (unified records).
  - `crawl(race_ids, session=None) -> list[dict]` (network).
  - `main()` writes `data/processed/criterium_2024_2026.json`.

- [ ] **Step 1: Write the failing test** (record-mapping is pure; network is not tested)

Create `scrapers/test_criterium_crawl.py`:

```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import criterium_crawl as cc

META = {"name": "苗栗繞圈賽（第七屆）", "date": "2026-06-28",
        "year": 2026, "region": "苗栗", "event_ids": [4]}
ROWS = [
    {"rank": 1, "bib": "2", "name": "馮俊凱", "category": "M / M30",
     "team": "宇都宮車隊", "finish_time": "00:47:38", "laps": 35, "status": "FIN"},
    {"rank": None, "bib": "21", "name": "洪稟詠", "category": "M / U23",
     "team": "TEAM CYTO TRIGON", "finish_time": None, "laps": 25, "status": "DNF"},
]


def test_build_records_fin():
    recs = cc.build_records(ROWS, META, "男子A組",
                            "https://events.criterium.tw/races/19554/events/4",
                            "2026-06-29T00:00:00")
    fin = recs[0]
    assert fin["source_platform"] == "criterium.tw"
    assert fin["race_name_raw"] == "苗栗繞圈賽（第七屆）"
    assert fin["year"] == 2026 and fin["date"] == "2026-06-28"
    assert fin["region"] == "苗栗"
    assert fin["result_label"] == "男子A組"
    assert fin["category_raw"] == "M / M30"
    assert fin["gender"] == "M" and fin["age_group"] == "30"
    assert fin["rank_overall"] == 1 and fin["bib"] == "2"
    assert fin["status"] == "FIN" and fin["laps"] == 35
    assert fin["finish_seconds"] == 47 * 60 + 38
    assert fin["name_masked"] == "馮○凱" and "name_raw" in fin


def test_build_records_dnf_has_no_time():
    recs = cc.build_records(ROWS, META, "男子A組", "u", "t")
    dnf = recs[1]
    assert dnf["status"] == "DNF"
    assert dnf["finish_time"] is None and dnf["finish_seconds"] is None
    assert dnf["laps"] == 25
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_criterium_crawl.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'criterium_crawl'`.

- [ ] **Step 3: Write the crawler**

Create `scrapers/criterium_crawl.py`:

```python
# -*- coding: utf-8 -*-
"""Scrape TCU criterium (繞圈賽) results from events.criterium.tw.

A small multi-event timing platform; server-rendered HTML, no JS/auth needed.
Per race: GET the overview page for name/date + event sub-page ids, then GET
each /races/{id}/events/{n} and parse the results table. This is the ONLY
source that exposes FIN/DNF/DNS status + lap counts. /api/ is robots-disallowed,
so we scrape the rendered pages. Output: data/processed/criterium_2024_2026.json
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402
import criterium_parse as cp  # noqa: E402

BASE = "https://events.criterium.tw"
SEED_RACE_IDS = [19554, 19267, 18931, 18772, 18571]
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                   "criterium_2024_2026.json")


def build_records(parsed_rows, race_meta, event_label, event_url, scraped_at):
    recs = []
    for row in parsed_rows:
        gender, age = cp.parse_category(row.get("category"))
        recs.append(common.make_record(
            source_platform="criterium.tw", source_url=event_url,
            source_format="html",
            race_name_raw=race_meta.get("name"), year=race_meta.get("year"),
            date=race_meta.get("date"), region=race_meta.get("region"),
            result_label=event_label, category_raw=row.get("category"),
            gender=gender, age_group=age,
            rank_overall=row.get("rank"), bib=row.get("bib"),
            team=row.get("team"), name_raw=row.get("name"),
            finish_time=row.get("finish_time"),
            status=row.get("status"), laps=row.get("laps"),
            scraped_at=scraped_at))
    return recs


def crawl(race_ids, session=None):
    session = session or common.make_session()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for rid in race_ids:
        ov = common.polite_get(session, f"{BASE}/races/{rid}").text
        meta = cp.parse_race_meta(ov)
        print(f"  race {rid}: {meta.get('name')} ({meta.get('date')}) "
              f"events={meta.get('event_ids')}")
        for n in meta["event_ids"]:
            url = f"{BASE}/races/{rid}/events/{n}"
            html = common.polite_get(session, url).text
            rows = cp.parse_event_page(html)
            out.extend(build_records(rows, meta, cp.event_name(html), url, now))
    return out


def main():
    recs = crawl(SEED_RACE_IDS)
    json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  {len(recs)} rows -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_criterium_crawl.py -v`
Expected: PASS (2 passed). (`馮俊凱` masks to `馮○凱` per `common.mask_name`.)

- [ ] **Step 5: Commit**

```bash
git add scrapers/criterium_crawl.py scrapers/test_criterium_crawl.py
git commit -m "feat(criterium): crawler + record builder for TCU criterium results"
```

---

### Task 4: merge.py — keep DNF/DNS rows, discover criterium files, count status

**Files:**
- Modify: `scrapers/merge.py` (`SOURCE_PREFIXES` line 25; drop check ~line 62-65; summary ~line 102-109)
- Test: `scrapers/test_merge.py` (create)

**Interfaces:**
- Produces: `should_drop_zero_time(r) -> bool` — pure predicate used by `main()`.

- [ ] **Step 1: Write the failing test**

Create `scrapers/test_merge.py`:

```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import merge


def test_keeps_dnf_dns_rows_without_time():
    assert merge.should_drop_zero_time({"status": "DNF", "finish_seconds": None}) is False
    assert merge.should_drop_zero_time({"status": "DNS", "finish_seconds": 0}) is False


def test_drops_zero_time_noise_without_status():
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": 0}) is True
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": -5}) is True


def test_keeps_normal_finisher():
    assert merge.should_drop_zero_time({"status": "FIN", "finish_seconds": 2858}) is False
    assert merge.should_drop_zero_time({"status": None, "finish_seconds": 2858}) is False


def test_criterium_prefix_discovered():
    assert "criterium_" in merge.SOURCE_PREFIXES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_merge.py -v`
Expected: FAIL — `AttributeError: module 'merge' has no attribute 'should_drop_zero_time'`.

- [ ] **Step 3: Implement**

In `scrapers/merge.py`:

(a) add the prefix (line 25):

```python
SOURCE_PREFIXES = ("criterium_", "cyclist_", "bravelog_", "cycling_", "irunner_")
```

(b) add the predicate above `main()`:

```python
def should_drop_zero_time(r):
    """Drop genuine zero/negative-time noise, but KEEP explicit DNF/DNS rows —
    criterium.tw reports non-finishers, which legitimately have no finish time."""
    if r.get("status") in ("DNF", "DNS"):
        return False
    fs = r.get("finish_seconds")
    return fs is not None and fs <= 0
```

(c) replace the inline drop check inside the loop (was `if fs is not None and fs <= 0:`):

```python
            fs = r.get("finish_seconds")
            if should_drop_zero_time(r):      # zero-time noise, but keep DNF/DNS
                n_zero += 1
                continue
```

(d) add a status counter — declare it with the other Counters (line ~56):

```python
    by_platform, by_year, by_gender, by_class, by_series = (Counter() for _ in range(5))
    by_status = Counter()
```

increment it in the loop next to the others:

```python
            by_status[r.get("status")] += 1
```

and add to `summary`:

```python
        "by_status": dict(by_status),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_merge.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add scrapers/merge.py scrapers/test_merge.py
git commit -m "feat(merge): keep DNF/DNS rows, discover criterium_, count by_status"
```

---

### Task 5: Confirm race_type classifies 繞圈 as 'crit'

**Files:**
- Test: `scrapers/test_race_type.py` (add one case)

**Interfaces:**
- Consumes: `race_type.classify(name, category=None) -> 'climb'|'crit'|'tt'|'road'` (already detects `繞圈` → `'crit'`).

- [ ] **Step 1: Add the assertion**

Append to `scrapers/test_race_type.py`:

```python
def test_criterium_name_classifies_as_crit():
    import race_type
    assert race_type.classify("苗栗繞圈賽（第七屆）") == "crit"
```

- [ ] **Step 2: Run it**

Run: `python -m pytest scrapers/test_race_type.py -v`
Expected: PASS (already handled by the `CRIT` pattern; this locks it in).

- [ ] **Step 3: Commit**

```bash
git add scrapers/test_race_type.py
git commit -m "test(race_type): lock criterium 繞圈 -> crit classification"
```

---

### Task 6: build_viz — completion stats in the races index, finisher-only leaderboards

**Files:**
- Modify: `scrapers/build_viz.py` (`build_races_index` ~line 75-92; `main` ~line 218-238)
- Test: `scrapers/test_build_viz.py` (add cases)

**Interfaces:**
- Produces: each `build_races_index` entry gains an optional `"completion": {"fin": int, "dnf": int, "dns": int, "rate": float}` — present only when the race-year has any `status` row.
- `is_finisher(r) -> bool` — `r["status"] not in ("DNF","DNS")`; used to keep non-finishers out of viz + per-race leaderboards.

- [ ] **Step 1: Write the failing test**

Add to `scrapers/test_build_viz.py`:

```python
def test_completion_present_for_status_races():
    import build_viz
    recs = [
        {"race_key": "苗栗繞圈賽第七屆", "year": 2026, "race_name_canonical": "苗栗繞圈賽（第七屆）",
         "series": None, "team": None, "status": "FIN", "finish_seconds": 2858},
        {"race_key": "苗栗繞圈賽第七屆", "year": 2026, "race_name_canonical": "苗栗繞圈賽（第七屆）",
         "series": None, "team": None, "status": "DNF", "finish_seconds": None},
        {"race_key": "苗栗繞圈賽第七屆", "year": 2026, "race_name_canonical": "苗栗繞圈賽（第七屆）",
         "series": None, "team": None, "status": "DNS", "finish_seconds": None},
    ]
    idx = build_viz.build_races_index(recs)
    entry = next(e for e in idx if e["rk"] == "苗栗繞圈賽第七屆")
    assert entry["completion"] == {"fin": 1, "dnf": 1, "dns": 1, "rate": round(1 / 3, 3)}


def test_completion_absent_without_status():
    import build_viz
    recs = [{"race_key": "彰化經典百K", "year": 2024, "race_name_canonical": "彰化經典百K",
             "series": None, "team": None, "status": None, "finish_seconds": 3600}]
    idx = build_viz.build_races_index(recs)
    entry = next(e for e in idx if e["rk"] == "彰化經典百K")
    assert "completion" not in entry


def test_is_finisher():
    import build_viz
    assert build_viz.is_finisher({"status": "FIN"}) is True
    assert build_viz.is_finisher({"status": None}) is True
    assert build_viz.is_finisher({"status": "DNF"}) is False
    assert build_viz.is_finisher({"status": "DNS"}) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_build_viz.py -k "completion or finisher" -v`
Expected: FAIL — `KeyError: 'completion'` / `AttributeError: is_finisher`.

- [ ] **Step 3: Implement**

In `scrapers/build_viz.py`:

(a) add `is_finisher` near the top (after imports):

```python
def is_finisher(r):
    """A row that belongs in finisher-only views (leaderboards, histograms).
    DNF/DNS rows (criterium.tw) carry no finish time and are excluded there;
    they are still counted for completion in build_races_index."""
    return r.get("status") not in ("DNF", "DNS")
```

(b) in `build_races_index`, accumulate status counts and emit `completion`:

```python
def build_races_index(records):
    """One entry per (race_key, year): name, series, count, multi-year flag,
    has_team, and completion (fin/dnf/dns/rate) when status data exists."""
    agg = defaultdict(lambda: {"rows": 0, "team": False,
                               "fin": 0, "dnf": 0, "dns": 0, "status_rows": 0})
    years = defaultdict(set)
    meta = {}
    for r in records:
        key = (r.get("race_key"), r.get("year"))
        a = agg[key]
        a["rows"] += 1
        a["team"] = a["team"] or bool(r.get("team"))
        st = r.get("status")
        if st in ("FIN", "DNF", "DNS"):
            a["status_rows"] += 1
            a[st.lower()] += 1
        years[r.get("race_key")].add(r.get("year"))
        meta[r.get("race_key")] = {"rn": r.get("race_name_canonical"), "s": r.get("series")}
    out = []
    for (rk, y), a in agg.items():
        entry = {"rk": rk, "y": y, "rn": meta[rk]["rn"], "s": meta[rk]["s"],
                 "rows": a["rows"], "multi_year": len([x for x in years[rk] if x]) > 1,
                 "has_team": a["team"], "file": race_file_name(rk, y)}
        if a["status_rows"]:
            total = a["fin"] + a["dnf"] + a["dns"]
            entry["completion"] = {"fin": a["fin"], "dnf": a["dnf"], "dns": a["dns"],
                                   "rate": round(a["fin"] / total, 3) if total else 0.0}
        out.append(entry)
    return sorted(out, key=lambda x: (-(x["rows"]), str(x["rk"])))
```

(c) in `main()`, keep non-finishers out of viz + per-race leaderboards (index still uses all `records`):

```python
def main():
    records = list(common.iter_records(IN))  # RAM-frugal streaming parse
    finishers = [r for r in records if is_finisher(r)]
    os.makedirs(os.path.join(OUT, "race"), exist_ok=True)
    viz = [slim_record(r) for r in finishers]
```

and the detail grouping loop:

```python
    groups = defaultdict(list)
    for r in finishers:
        groups[race_file_name(r.get("race_key"), r.get("year"))].append(r)
```

(leave `idx = build_races_index(records)` using the full `records`).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_build_viz.py -k "completion or finisher" -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add scrapers/build_viz.py scrapers/test_build_viz.py
git commit -m "feat(build_viz): per-race completion stats; finisher-only leaderboards"
```

---

### Task 7: Frontend — completion-rate block on /race

**Files:**
- Modify: `web/src/lib/types.ts` (`RaceIndex` ~line 9-11)
- Create: `web/src/lib/completion.ts`, `web/src/lib/completion.test.ts`
- Create: `web/src/components/race/Completion.tsx`
- Modify: `web/src/components/race/RaceDetailApp.tsx` (render `<Completion>` near `RaceSeverity`)

**Interfaces:**
- Consumes: `RaceIndex.completion?` from `loadRaces()` (already loaded by `RaceDetailApp`).
- Produces: `completionParts(c: Completion) -> { fin; dnf; dns; total; ratePct: number }`.

- [ ] **Step 1: Write the failing test**

Create `web/src/lib/completion.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { completionParts } from "./completion";

describe("completionParts", () => {
  it("computes total and rounded percent", () => {
    expect(completionParts({ fin: 64, dnf: 30, dns: 6, rate: 0.64 })).toEqual({
      fin: 64, dnf: 30, dns: 6, total: 100, ratePct: 64,
    });
  });
  it("handles all-finished", () => {
    const p = completionParts({ fin: 10, dnf: 0, dns: 0, rate: 1 });
    expect(p.total).toBe(10);
    expect(p.ratePct).toBe(100);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test -- completion`
Expected: FAIL — cannot find module `./completion`.

- [ ] **Step 3: Implement type + helper + component + wiring**

In `web/src/lib/types.ts`, add the `Completion` interface and field:

```ts
export interface Completion {
  fin: number; dnf: number; dns: number; rate: number;
}
export interface RaceIndex {
  rk: string; y: number | null; rn: string; s: string | null;
  rows: number; multi_year: boolean; has_team: boolean; file: string;
  completion?: Completion;
}
```

(merge the `completion?` line into the existing `RaceIndex` block; don't duplicate it.)

Create `web/src/lib/completion.ts`:

```ts
import type { Completion } from "./types";

/** Derive display parts from a prebuilt completion object. */
export function completionParts(c: Completion) {
  const total = c.fin + c.dnf + c.dns;
  return { fin: c.fin, dnf: c.dnf, dns: c.dns, total,
           ratePct: Math.round(c.rate * 100) };
}
```

Create `web/src/components/race/Completion.tsx`:

```tsx
import type { Completion as C } from "../../lib/types";
import { completionParts } from "../../lib/completion";

/** Completion-rate block. Only criterium.tw races carry status today; renders
 * nothing when no completion data exists (graceful absence elsewhere). */
export default function Completion({ completion }: { completion?: C }) {
  if (!completion) return null;
  const p = completionParts(completion);
  return (
    <section className="card">
      <h3 className="section-title">完賽率</h3>
      <p className="text-2xl font-semibold">{p.ratePct}%</p>
      <p className="text-sm text-muted">
        完賽 {p.fin} · DNF {p.dnf} · DNS {p.dns}（共 {p.total} 人報到）
      </p>
    </section>
  );
}
```

In `web/src/components/race/RaceDetailApp.tsx`, import and render it next to the existing `RaceSeverity` using the already-selected race index entry (match the prop name the file uses for the selected `RaceIndex`, e.g. `race`/`selected`):

```tsx
import Completion from "./Completion";
// ...in the render, beside <RaceSeverity .../>:
<Completion completion={race.completion} />
```

- [ ] **Step 4: Run tests + typecheck**

Run: `cd web && npm test -- completion && npx astro check`
Expected: vitest PASS (2 passed); astro check reports 0 errors.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/types.ts web/src/lib/completion.ts web/src/lib/completion.test.ts web/src/components/race/Completion.tsx web/src/components/race/RaceDetailApp.tsx
git commit -m "feat(web): completion-rate block on /race for status-bearing races"
```

---

### Task 8: Ingest the 5 races + rebuild + validate (None-safety check)

**Files:**
- Data: `data/processed/criterium_2024_2026.json` (new), `data/processed/master*.json` (regenerated), `web/public/data/*` (regenerated)

**Interfaces:** none (execution task).

- [ ] **Step 1: Scrape the 5 races**

Run: `python scrapers/criterium_crawl.py`
Expected: prints 5 races with event ids and a total row count (hundreds of rows); writes `data/processed/criterium_2024_2026.json`. Sanity-check it contains FIN + DNF + DNS:

```bash
python -X utf8 -c "import json,collections; d=json.load(open('data/processed/criterium_2024_2026.json',encoding='utf-8')); print(len(d),'rows'); print(collections.Counter(r['status'] for r in d)); print(collections.Counter(r['race_name_canonical'] for r in d))"
```

Expected: a `Counter` with FIN/DNF/DNS keys and 5 distinct race names.

- [ ] **Step 2: Merge**

Run: `python scrapers/merge.py`
Expected: prints `criterium_2024_2026.json` loaded; `by_status` now in `master_summary.json`. Verify no crash and criterium rows present:

```bash
python -X utf8 -c "import json; s=json.load(open('data/processed/master_summary.json',encoding='utf-8')); print('criterium', s['by_platform'].get('criterium.tw')); print('by_status', s.get('by_status'))"
```

Expected: a non-zero `criterium.tw` count and a `by_status` dict with FIN/DNF/DNS.

- [ ] **Step 3: Rebuild all dependent data; verify None-safety**

Run each and confirm no traceback (DNF rows have `finish_seconds=None`; these builds filter on time — confirm they still run clean):

```bash
python scrapers/build_viz.py
python scrapers/build_athletes.py
python scrapers/build_insights.py
python scrapers/build_difficulty.py
python scrapers/build_race_dna.py
python scrapers/build_teams.py
python scrapers/build_series.py
```

Expected: each exits 0. If any raises on `None` finish_seconds, add a guard `if r.get("finish_seconds") is None: continue` (or `is_finisher`-style filter) at that build's record-intake loop, re-run, and note the fix in its commit. (`build_viz` can hit a transient Windows MemoryError under pressure — just retry it.)

- [ ] **Step 4: Validate + run the whole pytest suite**

```bash
python scrapers/validate.py master.json
python -m pytest scrapers/
```

Expected: validate reports no new integrity errors; pytest all green.

- [ ] **Step 5: Verify completion landed in the index**

```bash
python -X utf8 -c "import json; idx=json.load(open('web/public/data/races.json',encoding='utf-8')); c=[e for e in idx if e.get('completion')]; print(len(c),'race-years with completion'); print(c[0] if c else 'NONE')"
```

Expected: ~5+ race-years with a `completion` object.

- [ ] **Step 6: Commit the data**

```bash
git add data/processed/criterium_2024_2026.json web/public/data
git commit -m "data(criterium): ingest 5 TCU criterium races (+FIN/DNF/DNS, laps)"
```

---

### Task 9: Browser verify, memory update, finish

**Files:**
- Modify: memory `data-limitations.md` + `MEMORY.md` pointer (no repo change)

- [ ] **Step 1: Browser-verify /race**

Run `cd web && npm run dev`, open a criterium race (e.g. 苗栗繞圈賽（第七屆）2026) on `/race`, confirm the 完賽率 block shows FIN/DNF/DNS + %, and that a non-criterium race shows NO completion block and an unbroken leaderboard. Also confirm `npx astro check` is clean and `npm run build` succeeds.

- [ ] **Step 2: Update memory**

Edit the `data-limitations` memory: change the opening "NO DNF, NO registration/starter counts" claim to note the exception — criterium.tw provides real FIN/DNF/DNS + lap counts for the 5 TCU criterium races (the only DNF-bearing source); other sources remain finisher-only. Add a one-line `criterium.tw` source note (host `events.criterium.tw`, server-rendered `<table class="tbl">`, seed ids, status text authoritative) to the relevant memory and the `MEMORY.md` index if a new file is created.

- [ ] **Step 3: Final push**

```bash
git push origin master
```

Expected: all criterium commits land on master; Vercel redeploys.

---

## Self-Review

**Spec coverage:**
- Scraper (`criterium_parse` + `criterium_crawl`) → Tasks 2-3 ✓
- Schema `status`/`laps` → Task 1 ✓
- merge keep-DNF + prefix + by_status → Task 4 ✓
- race_type 繞圈 → Task 5 ✓
- build_viz completion + finisher-only views → Task 6 ✓
- Frontend /race completion block → Task 7 ✓
- All-5-races ingest + rebuild + validate + None-safety → Task 8 ✓
- PDPA (name_masked only) → enforced via `make_record`/merge re-mask; asserted in Task 3 ✓
- Memory update → Task 9 ✓
- YAGNI exclusions (lap speeds, /athletes DNF, tsu canonical map, sitemap discovery) → not built ✓

**Placeholder scan:** none — every code/test step contains complete content.

**Type consistency:** `status` ∈ {FIN,DNF,DNS}|None and `laps` int|None used consistently across `make_record` (T1), parser (T2), crawler (T3), merge predicate (T4), build_viz (T6). `Completion {fin,dnf,dns,rate}` matches between build_viz output (T6) and the TS interface/helper (T7). `should_drop_zero_time`, `is_finisher`, `completionParts`, `parse_race_meta` names are referenced identically where used.
