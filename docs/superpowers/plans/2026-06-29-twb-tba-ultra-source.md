# TWB/TBA Ultra-Distance Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new data sources — TWB (台灣自行車協會, via the score.focusline JSON API) and TBA (中華民國自行車協會, via taiwanbike.org Google Sheets) ultra-distance certification rides — feeding the existing unified pipeline.

**Architecture:** Two independent HTTP scrapers (no headless). `focusline_crawl.py` reads a clean JSON API; `taiwanbike_crawl.py` reads the listing page → public Google Sheets `export?format=xlsx` → openpyxl. Both emit unified records via `common.make_record`; `merge.py` discovers them by filename prefix. No schema/build/frontend changes — finish times only, `rank_overall=None` (frontend re-ranks by category+time), sub-1h placeholders filtered.

**Tech Stack:** Python 3 (`requests`, `openpyxl`, stdlib `json`/`re`/`urllib`), pytest.

## Global Constraints

- **PDPA**: public output carries only `name_masked`; `name_raw` only in internal `master.json`. Per-source `focusline_*.json` / `taiwanbike_*.json` are gitignored (`data/processed/*.json`), like every source — never committed.
- **Pipeline shape**: scrapers write `data/processed/<source>_*.json`; `merge.py` auto-discovers files whose basename starts with a `SOURCE_PREFIXES` entry; build scripts read `master.public.json`. `data/processed/*.json` is gitignored except `*summary*.json`; `web/public/data/` is committed.
- **Source platform labels**: `source_platform="twbike.org"` for focusline rows; `source_platform="taiwanbike.org"` for TBA Sheet rows.
- **Decision — rank**: `rank_overall = None` for ALL rows from both sources (source rank is unreliable for certification rides). The frontend already re-ranks leaderboards by (category, finish time).
- **Placeholder filter**: drop any row whose finish time parses to `< 3600` seconds (1 hour) — these are 300–600 km rides; the fastest legit finish is ~10 h, so sub-1h values are DNF/placeholder/anomaly.
- **Per-feature workflow**: build → `python -m pytest scrapers/` → `validate.py` → `npx astro check` → browser-verify → own commit.

---

### Task 1: focusline (TWB) scraper

**Files:**
- Create: `scrapers/focusline_crawl.py`
- Test: `scrapers/test_focusline_crawl.py`

**Interfaces:**
- Consumes: `common.make_record`, `common.make_session`, `common.polite_get`, `common.time_to_seconds`.
- Produces:
  - `gender_of(row) -> 'M'|'F'|None`
  - `build_records(rows, meta, scraped_at) -> list[dict]` where `meta={'category','year','date','url'}`
  - `crawl(session=None) -> list[dict]` (network), `main()` writes `data/processed/focusline_2023_2026.json`.

- [ ] **Step 1: Write the failing test**

Create `scrapers/test_focusline_crawl.py`:

```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import focusline_crawl as fc

META = {"category": "雙塔", "year": 2025, "date": "2025-11-14",
        "url": "https://score.focusline.com.tw/api/Member/focusline?code=51114JR&categoryName=100102"}
ROWS = [
    {"name": "林玉清", "number": "H75532", "gender": "", "category": "雙塔",
     "group": "M50", "gunTime": "17:39:10", "totalSort": "1"},
    {"name": "陳美玲", "number": "W1234", "gender": "女", "category": "雙塔",
     "group": "W40", "gunTime": "20:05:00", "totalSort": "5"},
    {"name": "張弘瑜", "number": "D42012", "gender": "", "category": "雙塔",
     "group": "M30", "gunTime": "00:00:07", "totalSort": "291"},  # placeholder -> dropped
]


def test_gender_of_falls_back_to_group():
    assert fc.gender_of({"gender": "", "group": "M50"}) == "M"
    assert fc.gender_of({"gender": "女", "group": "W40"}) == "F"
    assert fc.gender_of({"gender": "", "group": "W40"}) == "F"
    assert fc.gender_of({"gender": "", "group": "?"}) is None


def test_build_records_maps_and_filters_placeholder():
    recs = fc.build_records(ROWS, META, "2026-06-29T00:00:00Z")
    assert len(recs) == 2  # placeholder (00:00:07) dropped
    r = recs[0]
    assert r["source_platform"] == "twbike.org"
    assert r["race_name_raw"] == "雙塔 2025"
    assert r["year"] == 2025 and r["date"] == "2025-11-14"
    assert r["result_label"] == "雙塔"
    assert r["category_raw"] == "M50"
    assert r["gender"] == "M"
    assert r["bib"] == "H75532"
    assert r["finish_time"] == "17:39:10"
    assert r["finish_seconds"] == 17 * 3600 + 39 * 60 + 10
    assert r["rank_overall"] is None and r["team"] is None
    assert r["name_masked"] == "林○清" and "name_raw" in r
    assert recs[1]["gender"] == "F"  # 陳美玲 from gender field
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_focusline_crawl.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'focusline_crawl'`.

- [ ] **Step 3: Write the scraper**

Create `scrapers/focusline_crawl.py`:

```python
# -*- coding: utf-8 -*-
"""Scrape TWB (台灣自行車協會) ultra-distance certification results from the
score.focusline.com.tw JSON API. Each event (actCode) has categories (distances);
each category is one race. gunTime = finish time; source rank (totalSort) is
unreliable for certification rides so rank_overall stays None and the frontend
re-ranks by (category, time). Sub-1h finish times are DNF/placeholders -> dropped.
Output: data/processed/focusline_2023_2026.json
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

BASE = "https://score.focusline.com.tw"
TOWER = re.compile(r"塔|北高|360|四極")
MIN_FINISH_SEC = 3600  # < 1h on a 300-600km ride = placeholder/DNF
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                   "focusline_2023_2026.json")
_AGE = re.compile(r"(\d{2})")


def gender_of(row):
    g = (row.get("gender") or "").strip()
    if g in ("男", "M", "m"):
        return "M"
    if g in ("女", "W", "F", "w", "f"):
        return "F"
    grp = (row.get("group") or "").strip()
    if grp[:1] in ("M", "m", "男"):
        return "M"
    if grp[:1] in ("W", "F", "w", "f", "女"):
        return "F"
    return None


def build_records(rows, meta, scraped_at):
    out = []
    for r in rows:
        fs = common.time_to_seconds(r.get("gunTime"))
        if fs is None or fs < MIN_FINISH_SEC:
            continue
        grp = r.get("group")
        age = _AGE.search(grp or "")
        out.append(common.make_record(
            source_platform="twbike.org", source_url=meta["url"], source_format="json",
            race_name_raw=f"{meta['category']} {meta['year']}",
            year=meta["year"], date=meta["date"],
            result_label=meta["category"], category_raw=grp,
            gender=gender_of(r), age_group=age.group(1) if age else None,
            rank_overall=None, bib=r.get("number"), team=None,
            name_raw=r.get("name"), finish_time=r.get("gunTime"),
            scraped_at=scraped_at))
    return out


def crawl(session=None):
    session = session or common.make_session()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    acts = common.polite_get(session, f"{BASE}/api/Activity?urlPath=focusline").json()
    out = []
    for a in acts:
        if not TOWER.search(a.get("actName") or ""):
            continue
        year = a.get("year")
        date = (a.get("actDate") or "")[:10] or None
        print(f"  {a.get('actCode')} {year} {a.get('actName')}")
        for c in (a.get("categories") or []):
            number, cat = c.get("number"), c.get("name")
            page = 1
            while True:
                url = (f"{BASE}/api/Member/focusline?code={a['actCode']}"
                       f"&categoryName={number}&nameOrNumber=&page={page}")
                rows = common.polite_get(session, url).json()
                if not rows:
                    break
                meta = {"category": cat, "year": year, "date": date, "url": url}
                out.extend(build_records(rows, meta, now))
                if len(rows) < 30:
                    break
                page += 1
    return out


def main():
    recs = crawl()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print(f"\n  {len(recs)} rows -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_focusline_crawl.py -v`
Expected: PASS (2 passed). (`林玉清` masks to `林○清`.)

- [ ] **Step 5: Commit**

```bash
git add scrapers/focusline_crawl.py scrapers/test_focusline_crawl.py
git commit -m "feat(focusline): TWB ultra-distance scraper (JSON API, finish-time only)"
```

---

### Task 2: taiwanbike (TBA) tolerant parsers

**Files:**
- Create: `scrapers/taiwanbike_parse.py`
- Test: `scrapers/test_taiwanbike_parse.py`

**Interfaces:**
- Consumes: `common` (none required directly).
- Produces:
  - `extract_sheet_links(html) -> list[dict]` with keys `title`, `year`(int|None), `sheet_id`.
  - `map_row(header, row) -> dict|None` with keys `bib`, `name`, `team`, `category`, `gender`, `finish_time` (None if no finish time).

- [ ] **Step 1: Write the failing test**

Create `scrapers/test_taiwanbike_parse.py`:

```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import taiwanbike_parse as tp

LISTING = (
    '<a href="https://docs.google.com/spreadsheets/d/1-OSl9p_AAA/edit?usp=sharing">'
    '2025雙塔520自行車認證</a>'
    '<a href="https://drive.google.com/file/d/9zzz/view">2019雙塔520</a>'  # not a sheet -> skip
    '<a href="https://docs.google.com/spreadsheets/d/1-BBB/edit">2026環大苗栗107K</a>'
    '<a href="https://docs.google.com/spreadsheets/d/1-CCC/edit">2018北高360</a>'  # <2022 -> skip
)

# 雙塔520 (duplicate 組別 header: event-name col + age-group col)
H1 = ["參加編號", "姓名", "隊名", "組別", "性別", "組別", "起點時間", "終點時間", "成績"]
R1 = ["6000", "蔡正一", "騎就對了", "2025TBA雙塔520自行車認證", "男", "M25",
      "2025-11-08 00:01:25", "2025-11-08 22:05:15", "22:03:49"]

# 環大苗栗 (has 名次 + chip time; different schema)
H2 = ["名次", "選手編號", "姓名", "組別", "分組排名", "性別排名", "大會成績", "晶片成績"]
R2 = ["1", "A12", "王大明", "M30", "1", "1", "03:10:00", "03:09:55"]

# row with no finish time -> skipped
H3 = ["參加編號", "姓名", "成績"]
R3 = ["7", "李四", ""]


def test_extract_sheet_links_filters_to_2022plus_sheets():
    links = tp.extract_sheet_links(LISTING)
    assert [(l["year"], l["sheet_id"]) for l in links] == [(2025, "1-OSl9p_AAA"), (2026, "1-BBB")]


def test_map_row_dual_group_picks_age_code_and_chip_time():
    m = tp.map_row(H1, R1)
    assert m["bib"] == "6000"
    assert m["name"] == "蔡正一"
    assert m["team"] == "騎就對了"
    assert m["category"] == "M25"        # the age-group code, not the event name
    assert m["gender"] == "M"
    assert m["finish_time"] == "22:03:49"


def test_map_row_prefers_chip_time_and_ignores_rank():
    m = tp.map_row(H2, R2)
    assert m["bib"] == "A12" and m["name"] == "王大明"
    assert m["category"] == "M30" and m["gender"] == "M"
    assert m["finish_time"] == "03:09:55"   # 晶片成績 preferred over 大會成績


def test_map_row_without_finish_time_is_none():
    assert tp.map_row(H3, R3) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_taiwanbike_parse.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'taiwanbike_parse'`.

- [ ] **Step 3: Write the parser**

Create `scrapers/taiwanbike_parse.py`:

```python
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
_YEAR = re.compile(r"(20[12]\d)")
_AGECODE = re.compile(r"^(?:[MWFmwf]\d{1,2}|U\d{1,2}|MASTER|[男女]\d{1,2})$")
_TIME = re.compile(r"^\d{1,2}:\d{2}:\d{2}")

# column-name synonyms (first match wins, scanning all columns)
_BIB = ("參加編號", "選手編號", "號碼布", "號碼")
_NAME = ("姓名",)
_TEAM = ("隊名", "車隊", "隊伍")
_GENDER = ("性別",)
_GROUP = ("組別", "分組", "性別組")
_FINISH = ("晶片成績", "大會成績", "總成績", "成績")   # priority order


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_taiwanbike_parse.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add scrapers/taiwanbike_parse.py scrapers/test_taiwanbike_parse.py
git commit -m "feat(taiwanbike): tolerant TBA sheet-link + row parsers"
```

---

### Task 3: taiwanbike (TBA) crawler (xlsx)

**Files:**
- Create: `scrapers/taiwanbike_crawl.py`
- Modify: `requirements.txt` (add `openpyxl`)

**Interfaces:**
- Consumes: `taiwanbike_parse.extract_sheet_links`, `taiwanbike_parse.map_row`; `common.make_record`, `common.make_session`, `common.polite_get`, `common.time_to_seconds`.
- Produces: `records_from_sheet(workbook_rows_by_tab, title, year, scraped_at) -> list[dict]`; `crawl()`, `main()` writes `data/processed/taiwanbike_2022_2026.json`.

- [ ] **Step 1: Write the failing test** (the pure `records_from_sheet`; network/openpyxl not unit-tested)

Append to `scrapers/test_taiwanbike_parse.py`:

```python
import taiwanbike_crawl as tc

def test_records_from_sheet_maps_and_masks():
    tabs = {"雙塔520選手總表": [
        ["參加編號", "姓名", "隊名", "組別", "性別", "組別", "成績"],
        ["6000", "蔡正一", "騎就對了", "2025TBA雙塔520", "男", "M25", "22:03:49"],
        ["7", "李四", "", "x", "男", "M30", ""],          # no time -> dropped
        ["8", "陳一", "隊B", "y", "男", "M40", "00:00:30"],  # placeholder <1h -> dropped
    ]}
    recs = tc.records_from_sheet(tabs, "2025雙塔520自行車認證", 2025, "2026-06-29T00:00:00Z")
    assert len(recs) == 1
    r = recs[0]
    assert r["source_platform"] == "taiwanbike.org"
    assert r["race_name_raw"] == "雙塔520自行車認證 2025"  # year stripped from title
    assert r["team"] == "騎就對了" and r["category_raw"] == "M25"
    assert r["rank_overall"] is None
    assert r["finish_seconds"] == 22 * 3600 + 3 * 60 + 49
    assert r["name_masked"] == "蔡○一"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_taiwanbike_parse.py::test_records_from_sheet_maps_and_masks -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'taiwanbike_crawl'`.

- [ ] **Step 3: Implement crawler + add dependency**

Add `openpyxl` to `requirements.txt` (append a line `openpyxl`).

Create `scrapers/taiwanbike_crawl.py`:

```python
# -*- coding: utf-8 -*-
"""Scrape TBA (中華民國自行車協會) ultra-distance certification results: the
taiwanbike.org listing page links to public Google Sheets (2022+); fetch each as
xlsx and parse every tab with the tolerant mapper. Finish time only; rank_overall
None (frontend re-ranks); sub-1h placeholders dropped.
Output: data/processed/taiwanbike_2022_2026.json
"""
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402
import taiwanbike_parse as tp  # noqa: E402

LISTING = "https://taiwanbike.org/index.php/2009-07-18-17-11-16"
SHEET_XLSX = "https://docs.google.com/spreadsheets/d/{}/export?format=xlsx"
MIN_FINISH_SEC = 3600
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                   "taiwanbike_2022_2026.json")
_YEAR = re.compile(r"^20[12]\d\s*")


def records_from_sheet(tabs, title, year, scraped_at):
    """tabs: dict{tab_name: list[list]} (first row = header). Reads the per-rider
    roster tab(s); skips obvious rank-only re-sort tabs to avoid double counting."""
    race = _YEAR.sub("", title).strip()
    out, seen = [], set()
    for name, rows in tabs.items():
        if any(k in name for k in ("排序", "排名")) and "總表" not in name:
            continue  # rank-sort tabs duplicate the roster
        if not rows or len(rows) < 2:
            continue
        header = rows[0]
        for row in rows[1:]:
            m = tp.map_row(header, row)
            if not m:
                continue
            fs = common.time_to_seconds(m["finish_time"])
            if fs is None or fs < MIN_FINISH_SEC:
                continue
            key = (m["bib"], m["name"], int(fs))
            if key in seen:
                continue
            seen.add(key)
            out.append(common.make_record(
                source_platform="taiwanbike.org",
                source_url=LISTING, source_format="xlsx",
                race_name_raw=f"{race} {year}", year=year,
                result_label=race, category_raw=m["category"],
                gender=m["gender"], age_group=None,
                rank_overall=None, bib=m["bib"], team=m["team"],
                name_raw=m["name"], finish_time=m["finish_time"],
                scraped_at=scraped_at))
    return out


def _xlsx_tabs(content):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    tabs = {}
    for ws in wb.worksheets:
        tabs[ws.title] = [[c for c in row] for row in ws.iter_rows(values_only=True)]
    wb.close()
    return tabs


def crawl(session=None):
    session = session or common.make_session()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    html = common.polite_get(session, LISTING).text
    links = tp.extract_sheet_links(html)
    print(f"  {len(links)} sheet links (2022+)")
    out = []
    for lk in links:
        try:
            content = common.polite_get(session, SHEET_XLSX.format(lk["sheet_id"])).content
            tabs = _xlsx_tabs(content)
            recs = records_from_sheet(tabs, lk["title"], lk["year"], now)
            print(f"    {lk['title']}: {len(recs)} rows")
            out.extend(recs)
        except Exception as e:  # one bad sheet must not abort the run
            print(f"    ! skip {lk['title']}: {e}")
    return out


def main():
    recs = crawl()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print(f"\n  {len(recs)} rows -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_taiwanbike_parse.py -v`
Expected: PASS (5 passed). (`蔡正一` masks to `蔡○一`.)

- [ ] **Step 5: Commit**

```bash
git add scrapers/taiwanbike_crawl.py scrapers/test_taiwanbike_parse.py requirements.txt
git commit -m "feat(taiwanbike): TBA xlsx crawler (Google Sheets export)"
```

---

### Task 4: merge — discover the two new sources

**Files:**
- Modify: `scrapers/merge.py` (`SOURCE_PREFIXES`)
- Test: `scrapers/test_merge.py` (add assertion)

**Interfaces:**
- Consumes: existing `merge.SOURCE_PREFIXES`.

- [ ] **Step 1: Write the failing test**

Add to `scrapers/test_merge.py`:

```python
def test_focusline_and_taiwanbike_prefixes_discovered():
    assert "focusline_" in merge.SOURCE_PREFIXES
    assert "taiwanbike_" in merge.SOURCE_PREFIXES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_merge.py::test_focusline_and_taiwanbike_prefixes_discovered -v`
Expected: FAIL — assertion error (prefixes absent).

- [ ] **Step 3: Add the prefixes**

In `scrapers/merge.py`, add both prefixes to the tuple (keep existing entries):

```python
SOURCE_PREFIXES = ("criterium_", "cyclist_", "bravelog_", "cycling_", "irunner_",
                   "focusline_", "taiwanbike_")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_merge.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scrapers/merge.py scrapers/test_merge.py
git commit -m "feat(merge): discover focusline_ + taiwanbike_ sources"
```

---

### Task 5: Ingest both + rebuild + validate

**Files:** Data only (`data/processed/{focusline,taiwanbike}_*.json` new/gitignored; `data/processed/master*.json` regenerated; `web/public/data/*` regenerated).

**Interfaces:** none (execution task).

- [ ] **Step 1: Scrape both sources**

```bash
python scrapers/focusline_crawl.py
python scrapers/taiwanbike_crawl.py
```

Expected: focusline prints ~5 tower events and a total (hundreds–thousands of rows); taiwanbike prints sheet links + per-sheet counts. Sanity-check each:

```bash
python -X utf8 -c "import json,collections as c; \
d=json.load(open('data/processed/focusline_2023_2026.json',encoding='utf-8')); \
print('focusline', len(d), 'rows'); print(c.Counter(r['race_name_canonical'] for r in d)); \
import statistics; ts=[r['finish_seconds'] for r in d]; print('finish_sec min/max', min(ts), max(ts))"
```

Expected: all `finish_seconds >= 3600`; race names like `雙塔 2025` / `西三塔 2025` / `北高360 2023`. Repeat for `taiwanbike_2022_2026.json` (expect race names like `雙塔520自行車認證 2025`, a non-empty `team` on most rows).

- [ ] **Step 2: Merge + verify**

```bash
python scrapers/merge.py
python -X utf8 -c "import json; s=json.load(open('data/processed/master_summary.json',encoding='utf-8')); \
print('twbike.org', s['by_platform'].get('twbike.org'), '| taiwanbike.org', s['by_platform'].get('taiwanbike.org'))"
```

Expected: non-zero counts for both new platforms; no crash.

- [ ] **Step 3: Rebuild all dependent data**

```bash
python scrapers/build_viz.py
python scrapers/build_athletes.py
python scrapers/build_insights.py
python scrapers/build_difficulty.py
python scrapers/build_race_dna.py
python scrapers/build_teams.py
python scrapers/build_series.py
```

Expected: each exits 0. (`rank_overall=None` rows: `build_viz.detail_record` already emits `rank=None`, and its leaderboard sort handles None — `key=(x["rank"] is None, x["rank"] or 0)`. If any build raises on None rank/age, add an `if ... is None` guard at that build's intake and note it in the commit. `build_viz` may hit a transient Windows MemoryError — just retry.)

- [ ] **Step 4: Validate + full pytest**

```bash
python scrapers/validate.py master.json
python -m pytest scrapers/
```

Expected: validate reports no new integrity failures (some `missing_age`/`missing_team` warnings are fine — focusline has no team, partial ages); pytest all green.

- [ ] **Step 5: Commit the data**

```bash
git add -A -- web/public/data data/processed/master_summary.json
git commit -m "data(ultra): ingest TWB focusline + TBA taiwanbike ultra-distance results"
```

---

### Task 6: Browser verify, memory, finish

**Files:** memory only (no repo change).

- [ ] **Step 1: Browser-verify a tower race on /race**

`cd web && npm run dev`, open a TWB race (e.g. `西三塔 2025`) and a TBA race (e.g. `雙塔520自行車認證 2025`) on `/race`. Confirm: the leaderboard is sorted by finish time ascending within a category (rank re-derived correctly despite source `rank_overall=None`); finish times are multi-hour (no sub-1h rows); the TBA race shows teams. Confirm `npx astro check` is clean and `npm run build` succeeds.

- [ ] **Step 2: Update memory**

Update the `data-freshness-routine` memory: the TWB/TBA `BLOCKED` leads are now implemented as the `focusline` / `taiwanbike` sources. Update the source count (6 → 8) wherever a memory states it (`data-limitations` / source totals), noting the new ultra-distance (300–600 km) coverage.

- [ ] **Step 3: Final push**

```bash
git push origin feat/twb-tba-source
```

Then finish the branch (PR or merge) per superpowers:finishing-a-development-branch.

---

## Self-Review

**Spec coverage:**
- focusline (TWB) JSON scraper, gunTime→finish, placeholder filter, rank None → Task 1 ✓
- taiwanbike (TBA) tolerant parsers (sheet links + drifting columns + dup 組別 + chip-time) → Task 2 ✓
- taiwanbike xlsx crawler + openpyxl dep → Task 3 ✓
- merge prefixes → Task 4 ✓
- ingest + rebuild + validate, None-rank safety → Task 5 ✓
- browser verify + memory → Task 6 ✓
- PDPA (name_masked only; per-source files gitignored) → enforced via make_record/merge; asserted in Tasks 1 & 3 ✓
- source_platform labels twbike.org / taiwanbike.org → Tasks 1 & 3 ✓
- YAGNI (old xls/PDF/OneDrive, 輪霸西濱, relay) → not built ✓

**Placeholder scan:** none — every code/test step has complete content.

**Type consistency:** `gender_of`, `build_records(rows, meta, scraped_at)`, `extract_sheet_links`, `map_row(header, row)`, `records_from_sheet(tabs, title, year, scraped_at)` are referenced identically where used. `meta` keys (`category`/`year`/`date`/`url`) and `map_row` output keys (`bib`/`name`/`team`/`category`/`gender`/`finish_time`) match across tasks. `rank_overall=None`, `finish_time`/`finish_seconds`, `MIN_FINISH_SEC=3600` consistent across both scrapers.
