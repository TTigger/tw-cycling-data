# Data pipeline & rebuild

There is **no scheduler / auto-ingest** — the site is rebuilt manually (or when
triggered) after source data changes.

## Flow
```
scrapers (cyclist.org.tw / bravelog.tw / cycling.org.tw)
        │  <source>_*.json in data/processed/
        ▼
merge.py  ── applies normalize.enrich() (race_class, series, age_band,
        │   RACE_KEY_CANONICAL re-key, gender/age back-fill), de-identifies
        ▼
data/processed/master.json         (INTERNAL — has name_raw, gitignored)
data/processed/master.public.json  (de-identified — feeds the builders)
data/processed/master_summary.json (QC stats)
        ▼
build_*.py  ──►  web/public/data/*.json   (browser-ready, de-identified)
```

## Who writes what (scrapers/)
- `build_viz.py` ← `master.public.json` → `viz.json`, `races.json`,
  `race/<key>__<year>.json`, **`overview.json`**, **`race_crossyear.json`**.
- `build_athletes.py` ← `master.json` → `athletes.json`, `athlete/<id>.json`,
  `athlete_features.json`, `course_records.json`, `climb_profiles.json`, `climb_vam.json`.
- `build_teams.py`, `build_difficulty.py`, `build_race_dna.py`, `build_series.py`,
  `build_insights.py`, `build_og.py` (the share image), `build_fonts.py`.
- `discover.py` writes `coverage.json`. Run it locally (`scrapers/freshness_local.sh`
  or `.ps1`) — the calendars 403 cloud IPs. Without `master.public.json` it diffs
  against `races.json` and keeps the previous summary numbers. A calendar that fails
  to fetch keeps its previous gaps (marked `stale`). Dated calendars (RACE ON) also
  get a per-year check: a race held this year whose earlier editions are in master
  but this year's isn't is flagged `NOT_INGESTED` — the plain name diff strips the
  year and can't see that.

## Rebuild from scratch (new machine / lost master.json)
`master.json` + `data/raw` are gitignored and live on ONE machine. In 2026-11 that
machine was lost with no backup, so the dataset was re-crawled. On a fresh clone:
```
python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt
scrapers/rebuild_all.sh crawl all          # or one source per job, in parallel
scrapers/rebuild_all.sh build              # merge → validate → builders → manifest
.venv/bin/python scrapers/compare_rebuild.py   # diff vs the committed site data
```
`pipeline refresh` alone is NOT a from-scratch rebuild: it assumes caches exist
(irunner runs in test mode, bravelog_calendar covers one year, cyclist 2024+).
Athlete ids are salted hashes of the identity key, so a faithful rebuild keeps
every /athlete/<id> URL. Then run `scrapers/backup.py` so it can't happen again.

## To rebuild after a data/normalization change
1. `python scrapers/merge.py` (regenerates both master files).
2. Run the affected builders. A race_key change touches almost all of them; also
   `rm -rf web/public/data/race` first to clear **orphan** per-race files whose
   keys changed.
3. `pytest scrapers/` · `npx astro check` · `npx astro build` · browser-verify.

## Gotchas
- **`build_viz` can hit a transient Windows `MemoryError`** parsing the large
  `master.public.json` under memory pressure. Just re-run it — do not kill the
  Claude/node harness process to "free memory". `build_athletes` reads the even
  larger `master.json` fine, so it is pressure, not a hard limit.
- `PYTHONIOENCODING=utf-8` is needed for CJK console output on Windows.
- Identity grouping is rider-based (`build_group_keys`: tsu → UCI → name); merging
  race keys never changes athlete ids. See [PDPA](./pdpa-deidentification.md).
- Builders that consume aggregates instead of raw rows: see
  [client data loading](./client-data-loading.md).
- **96聯賽 PDFs need pypdf, not pdfplumber**: their fonts have no FontBBox, so
  pdfplumber mis-measures glyphs and drops ~80% of rows. `sporter96_pdf.py` reads
  pypdf text runs with their coordinates and splits columns at the midpoints
  between header labels. Glyphs of one run share its start x, so sort lines on x
  only (stable) or names come out scrambled.


## Unattended weekly ingest (2026-11-06)
`scrapers/auto_ingest.py` runs every source, then gates before opening a PR:
no race-year disappears or loses rows, no athlete URL breaks, no real name,
pytest passes. A source whose output shrinks (site down, half a crawl) gets its
previous file back, so one broken site never blocks the rest. Worklist sources
(e-better, 96 PDFs) need a person to name new events; the PR lists e-better
candidates it found. iRunner's event list is re-scanned up to 150 ids past the
newest known event.
