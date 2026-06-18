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
- `discover.py` writes `coverage.json`.

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
