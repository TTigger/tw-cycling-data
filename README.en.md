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
| **Phase 1e: tsu.com.tw results platform** | ✅ **24,925 rows / 2009–2025** (county criteriums/gravel/NeverStop Wuling/96 series; carries **TCU rider IDs**, fills the deepest history) |
| **Phase 1f: cycling.org.tw old wide-table backfill** | ✅ `cycling_oldroad.py` recovers the 2013 national road championship **146 rows** (wide→long reshape; other years are 404) |
| Normalization + merge + validation tooling | ✅ `normalize.py` / `merge.py` (year-agnostic, auto-discovers sources, cross-source dedup) / `validate.py` |
| **★ Merged master dataset** | ✅ **83,103 rows / 2009–2026 / 115 races / 4 sources**, de-identified |
| **Phase 2: interactive dashboard (4 pages)** | ✅ `web/` (Overview / Explore / Race / Climbs; Astro+React+ECharts, Claude aesthetic, responsive) |
| **Vercel deployment** | ✅ Live (Root Directory=`web`; auto-deploys on push) |
| **Phase 1c: historical backfill (cyclist 2014–23 + Bravelog 2018–23)** | ✅ +7,363 + historical Bravelog |
| **Phase 3: per-athlete tracking (TCU/UCI-ID-anchored, name fallback)** | ✅ `/athletes` **15,301 trackable athletes** (≥2 results); progression + career table + homonym confidence flag; 650 anchored by TCU ID, 101 by UCI |

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
  cycling_crawl.py     ★ crawler for cycling.org.tw national PDF result books (carry UCI IDs)
  tsu_crawl.py         ★ crawler for tsu.com.tw (/race?y= year×page → /race/result header-mapped tables; carries TCU rider IDs)
  merge.py             ★ merge all sources → master dataset (applies normalize, cross-source dedup)
  validate.py          data-quality checks (dupes / times / rank inversions / coverage / year drift)
  build_viz.py         ★ master.public → frontend data files (viz/races/race; pytest-tested)
  build_athletes.py    ★ master → athlete-tracking data (athletes index + athlete/<id>: identity grouping, homonym flag, climb_vam, trait radar, head-to-head rivals; pytest-tested)
  build_insights.py    ★ master → insights.json (peak-age curve / breakout / race ratings / region hotspots; pytest-tested)
  race_type.py         race discipline classifier (climb/crit/tt/road; pytest-tested)
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

Astro + React islands + Tailwind v4 + ECharts, "Claude" warm aesthetic. Six pages:
- `/` (Overview), `/explore` (Explore), `/race` (Race detail)
- `/athletes` (Athlete tracking + **climber-vs-rouleur radar** + **head-to-head rivals**)
- `/climbs` (Legendary climbs + **VAM climbing index**: single-race leaderboard + cross-race "Climbing King" + estimated W/kg, from a curated `climb_profiles.json`)
- `/insights` (peak-age curve, breakout stars, race star-ratings, result converter, region hotspots)

```powershell
python scrapers\build_viz.py            # master.public → web/public/data/{viz,races,race/*}.json
python scrapers\build_athletes.py       # master → athletes/athlete/<id>/climb_vam.json (incl. radar + rivals)
python scrapers\build_insights.py       # master → insights.json (age curve / breakout / ratings / geo)
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

`source_platform` `source_url` `source_format` ｜ `race_name_raw` `race_name_canonical` `race_key` (dedupe/merge key) `year` `date` `race_type` `region` ｜ `result_label` `category_raw` (raw division) `gender` (M/F/None) `age_group` (`24-35`/`U15`/`MASTER`…) `age_band` (coarse decade band) ｜ `rank_overall` `bib` `uci_id` `tsu_rider_id` (identity anchors) ｜ `name_raw` (internal) `name_masked` (`李○明`, head+tail, PDPA) `nationality` `team` ｜ `finish_time` `finish_seconds` `splits` ｜ `scraped_at`

## Notes & limitations

- **cyclist.org.tw**: listing → event page → PDF → pdfplumber **line-based text** parsing; **column order varies per PDF**, so the parser reads the Chinese header to auto-detect order (`detect_order`); the division code yields gender + age band directly; cross-category duplicates removed by `(race_key, year, bib, finish)`.
- **Bravelog**: contests discovered via the `/search` JSON API → server-rendered rank pages parsed with pagination (no JS/headless needed).
- **gender=None ≈ 16%** is mostly legitimate (U13–U15 youth / challenge / e-bike groups aren't gender-coded; many Bravelog citizen races are ungrouped).
- **PDPA**: only `*.public.json` (no `name_raw`) is published; the UI shows masked names; the site footer states sources and a takedown note.
- **Age-group normalization**: raw `age_group` mixes two schemes across sources (5-year-start codes 20/25/30… and explicit ranges 24-35/40-49); `normalize.age_band()` unifies them into coarse decade bands (`U19/19-29/30-39/40-49/50-59/60+/MASTER`) for the explore filter + boxplot, while the raw `age_group` is kept on each result.
- **race_key / race-class** use conservative normalization; a curated race-name mapping table is still a refinement TODO (the three different "武嶺" races must not be merged; KOM Challenge ≠ KOM-no-michi).

## Athlete identity resolution (Phase 3)

- **Stable rider IDs are the strong anchor** — tsu's `tsu_rider_id` (TCU-…) and cycling's `uci_id`: when a name maps to exactly one ID, all its results unify at high confidence. This correctly merges careers across team changes and years (e.g. a 2013–2026 woman across 8 teams is one athlete via her TCU ID).
- **Name fallback** — riders without an ID group by `name_raw` (teams change yearly; a hard name+team key would fragment riders who switch teams).
- **Homonym confidence flag** — a name spanning many distinct teams, or one identity racing as both M and F, is flagged `low` (high homonym risk) with a UI caveat.
- **PDPA** — output carries only masked names (`林○宇`, head+tail kept), a salted non-reversible `athlete_id`, and a `has_uci` boolean — never `name_raw` or the raw UCI ID. Index holds only ≥2-result athletes; each career file is fetched lazily on click.

## Next steps

- Dashboard enhancements: race/category normalization table (unify M20/20-24/M24-35), ECharts tree-shake, mobile filter drawer, a11y, custom domain.
- cycling.org.tw old wide-table years backfill (currently 2025 national source only).
