# Taiwan Road-Cycling Race Data (tw-cycling-data)

> 🌐 繁體中文:**[README.md](README.md)**

Collect, clean, and normalize Taiwan road-cycling race results (2015–2026) into a unified dataset, then an interactive visualization dashboard, deployed as a static site on Vercel.

## Status

| Stage | State |
|---|---|
| Source reconnaissance (16-agent workflow) | ✅ `recon-report.md` / `recon-raw.json` |
| Scrape feasibility PoC (cyclist + Bravelog) | ✅ `poc-findings.md` |
| **Phase 1a: cyclist.org.tw pipeline (2024–26)** | ✅ **3,913 rows / 12 races** (competitive; gender 83% + age-group 95%) |
| **Phase 1b: Bravelog pipeline (2018–26)** | ✅ **44,850 rows / 61 races** (citizen/challenge; triathlons excluded) |
| **Phase 1d: cycling.org.tw national source** | ✅ National road championship **203 rows (2025, with UCI IDs)**; old wide-table years deferred |
| Normalization + merge + validation tooling | ✅ `normalize.py` / `merge.py` (year-agnostic, auto-discovers sources) / `validate.py` |
| **★ Merged master dataset** | ✅ **56,329 rows / 2015–2026 / 72 races / 3 sources**, de-identified |
| **Phase 2: interactive dashboard (4 pages)** | ✅ `web/` (Overview / Explore / Race / Climbs; Astro+React+ECharts, Claude aesthetic, responsive) |
| **Vercel deployment** | ✅ Live (Root Directory=`web`; auto-deploys on push) |
| **Phase 1c: historical backfill (cyclist 2014–23 + Bravelog 2018–23)** | ✅ +7,363 + historical Bravelog |
| Phase 3: per-athlete tracking (name-primary, UCI-assisted) | TODO (next) |

## Layout

```
recon-report.md / recon-raw.json   source-landscape reconnaissance
poc-findings.md                    scraper feasibility PoC
cycorg-poc-findings.md             cycling.org.tw (national source) recon
docs/superpowers/                  design specs + implementation plans (brainstorm→plan)
scrapers/
  common.py            shared: HTTP, division/gender/age normalization, name masking (PDPA), race_key, unified record
  normalize.py         cross-source normalization: race_class (award-group type) + series tables
  cyclist_crawl.py     ★ crawler for cyclist.org.tw (supports --years backfill, --out)
  bravelog_calendar.py ★ Bravelog contest discovery (/search API) + cycling-race classifier
  bravelog_crawl.py    ★ crawler for Bravelog (contest→raceId sub-race→pagination, per-contest cache)
  merge.py             ★ merge all sources → master dataset (applies normalize)
  validate.py          data-quality checks (dupes / times / rank inversions / coverage / year drift)
  build_viz.py         ★ master.public → frontend data files (viz/races/race; pytest-tested)
  summarize.py         per-dataset summary stats
  *_poc.py / *_inspect.py / *_probe.py / bravelog_parse.py   one-off PoC/exploration scripts (kept for reference)
data/processed/
  master.public.json     ★ de-identified merged dataset (for frontend)
  *_summary.json                   summary stats
web/                               Astro frontend dashboard (see below)
```

## Data pipeline (Python)

```powershell
pip install -r requirements.txt

# Phase 1a — cyclist.org.tw
python scrapers\cyclist_crawl.py                      # full 2024–2026 (fast if PDFs cached)
python scrapers\cyclist_crawl.py --years 2014-2023 --out cyclist_2014_2023.json  # historical backfill

# Phase 1b — Bravelog
python scrapers\bravelog_calendar.py 2024 2025 2026   # 1) build the cycling-contest worklist
python scrapers\bravelog_crawl.py                     # 2) crawl results (resumable; --limit N for a smoke test)

# Merge + validate
python scrapers\merge.py                               # merge all sources → master
python scrapers\validate.py master.json      # data-quality report
```

## Frontend dashboard (`web/`)

Astro + React islands + Tailwind v4 + ECharts, "Claude" warm aesthetic. Four pages: `/` (Overview), `/explore` (Explore), `/race` (Race detail), `/climbs` (Legendary climbs).

```powershell
python scrapers\build_viz.py            # master.public → web/public/data/{viz,races,race/*}.json
cd web
npm install
npm run dev                             # dev server at http://localhost:4321
npm test                                # vitest unit tests (pure functions)
npx astro check                         # type-check
npm run build                           # static output to web/dist
```

## Deployment (Vercel, auto from GitHub)

- `web/public/data/*` is **committed** (deploy artifact — Vercel's build has no Python to regenerate it). To refresh data: rerun `python scrapers\build_viz.py`, then commit.
- Vercel settings: **Root Directory = `web`**, Framework = Astro (auto-detected), Output = `dist`. Pure static — no adapter needed.
- Push to GitHub (private) → connect the repo in Vercel → every push auto-deploys.

## Unified record schema (one row = one athlete in one race)

`source_platform` `source_url` `source_format` ｜ `race_name_raw` `race_name_canonical` `race_key` (dedupe/merge key) `year` `date` `race_type` `region` ｜ `result_label` `category_raw` (raw division) `gender` (M/F/None) `age_group` (`24-35`/`U15`/`MASTER`…) ｜ `rank_overall` `bib` ｜ `name_raw` (internal) `name_masked` (`李○○`, PDPA) `nationality` `team` ｜ `finish_time` `finish_seconds` `splits` ｜ `scraped_at`

## Notes & limitations

- **cyclist.org.tw**: listing → event page → PDF → pdfplumber **line-based text** parsing; **column order varies per PDF**, so the parser reads the Chinese header to auto-detect order (`detect_order`); the division code yields gender + age band directly; cross-category duplicates removed by `(race_key, year, bib, finish)`.
- **Bravelog**: contests discovered via the `/search` JSON API → server-rendered rank pages parsed with pagination (no JS/headless needed).
- **gender=None ≈ 16%** is mostly legitimate (U13–U15 youth / challenge / e-bike groups aren't gender-coded; many Bravelog citizen races are ungrouped).
- **PDPA**: only `*.public.json` (no `name_raw`) is published; the UI shows masked names; the site footer states sources and a takedown note.
- **race_key / category** use conservative normalization; a curated race/category mapping table is still a refinement TODO (the three different "武嶺" races must not be merged; KOM Challenge ≠ KOM-no-michi).

## Next steps

- **cycling.org.tw national source** (Tour de Taiwan / national championships / team selection, includes **UCI IDs**).
- **Phase 3 per-athlete tracking** (join on UCI ID, build athlete pages).
- Dashboard enhancements: cross-page links, race/athlete search, race/category normalization table, ECharts tree-shake, mobile filter drawer, a11y, custom domain.
