# Taiwan Road-Cycling Race Data (tw-cycling-data)

> 繁體中文:**[README.md](README.md)** ｜ Data-source registry (scraped / blocked / discovery): **[SOURCES.md](SOURCES.md)**

Collect, clean, and normalize Taiwan road-cycling race results (2009–2026) into a unified dataset, then an interactive visualization dashboard, deployed as a static site on Vercel.

## Public API

Read-only JSON API (CC BY 4.0, de-identified). Base: `https://tw-cycling-data.vercel.app/data/v1`, entry [`manifest.json`](https://tw-cycling-data.vercel.app/data/v1/manifest.json). Endpoints and schema in [`docs/API.md`](docs/API.md). A Python MCP server is also provided (see [`mcp-server/`](mcp-server/)).

## Open Dataset

De-identified row-level results (147,609 rows, 2009–2026, CC BY 4.0) are downloadable: see [Releases](https://github.com/TTigger/tw-cycling-data/releases) and [DATASET.en.md](DATASET.en.md). External identifiers are removed; data subjects can request removal via [Issues](https://github.com/TTigger/tw-cycling-data/issues).

## What this is & who it's for (Why)

Taiwan's cycling results are **scattered across 4+ platforms** and mostly only queryable race-by-race — there's no single place to compare across races or follow a rider's career. This project aggregates, de-identifies and normalizes those public results into a **free, open, interactive** explorer — currently the **only** unified, analyzable view of Taiwan road-cycling results (**118,501 rows / 130 races / 2009–2026 / 6 sources**, plus an overseas collection).

Ten pages: **Overview** (the scene at a glance) · **Explore** (filter & analyze distributions) · **Race** (leaderboard + "what % did you beat" percentile + **Race DNA** 6-axis radar with side-by-side compare + **similar-race finder** + **severity/attrition estimate** + **completion rate** (FIN/DNF/DNS, criteriums) + race search) · **Series** (**multi-station season standings** for 96聯賽/捷安特/崇越/雪巴…) · **Athletes** (22,035 trackable riders: career history, progression, **season review**, **cross-year difficulty calibration**, climber-vs-rouleur radar, **riding doppelgangers**, **1v1 head-to-head**, rivals) · **Teams** (roster, team records, activity timeline; 805 teams) · **Climbs** (VAM climbing index + cross-race Climbing King + all-time course records) · **Insights** (peak-age curve, breakout stars, race star-ratings, result converter, geographic hotspots) · **Overseas** (kept separate) · **Coverage** (source transparency + missing-race worklist). The point: turn "scattered, query-only" results into a **searchable, career-trackable, comparable** community resource. PDPA-safe (masked names only). Coverage is disclosed honestly in **[SOURCES.md](SOURCES.md)**.

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

Astro + React islands + Tailwind v4 + ECharts, "Claude" warm aesthetic. Ten pages (dark mode, favorites, mobile drawer):
- `/` (Overview), `/explore` (Explore), `/race` (Race detail), `/series`, `/overseas`, `/coverage`
- `/athletes` (Athlete tracking + season review + **climber-vs-rouleur radar** + **head-to-head rivals**)
- `/teams` (**Teams**: roster, team records, activity timeline; `teams.json` + `team/<id>.json`)
- `/climbs` (Legendary climbs + **VAM climbing index**: single-race leaderboard + cross-race "Climbing King" + estimated W/kg, from a curated `climb_profiles.json`)
- `/insights` (peak-age curve, breakout stars, race star-ratings, result converter, region hotspots)

```powershell
python scrapers\build_viz.py            # master.public → web/public/data/{viz,races,race/*}.json
python scrapers\build_athletes.py       # master → athletes/athlete/<id>/climb_vam.json (incl. radar + rivals)
python scrapers\build_insights.py       # master → insights.json (age curve / breakout / ratings / geo)
python scrapers\build_teams.py          # master → teams.json + team/<id>.json (teams page)
python scrapers\build_viz.py            # also emits overview.json (homepage aggregates) + race_crossyear.json
python scrapers\build_og.py             # → web/public/og.png (OG share image; rerun when headline stats change)
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
- **Leaderboard placing**: a competitive event's `category_raw` can lump several sub-events (road race + ITT) into one category, and source `rank_overall` is the within-sub-event placing, not an overall rank. The leaderboard therefore **groups by `(category, label)` and re-ranks 1..N by finish time within the group**, keeping the source rank in an `原始` column — so a displayed place may differ from the organizer's official result (the organizer's announcement governs). See [docs/learnings/race-leaderboard-ranking.md](docs/learnings/race-leaderboard-ranking.md).

## Athlete identity resolution (Phase 3)

- **Stable rider IDs are the strong anchor** — tsu's `tsu_rider_id` (TCU-…) and cycling's `uci_id`: when a name maps to exactly one ID, all its results unify at high confidence. This correctly merges careers across team changes and years (e.g. a 2013–2026 woman across 8 teams is one athlete via her TCU ID).
- **Name fallback** — riders without an ID group by `name_raw` (teams change yearly; a hard name+team key would fragment riders who switch teams).
- **Homonym confidence flag** — a name spanning many distinct teams, or one identity racing as both M and F, is flagged `low` (high homonym risk) with a UI caveat.
- **PDPA** — output carries only masked names (`林○宇`, head+tail kept), a salted non-reversible `athlete_id`, and a `has_uci` boolean — never `name_raw` or the raw UCI ID. Index holds only ≥2-result athletes; each career file is fetched lazily on click.

## Next steps

- Custom domain (if added later, update `astro.config` `site`; currently `tw-cycling-data.vercel.app`).
- Continue race/category normalization (candidate generator `scrapers/suggest_race_merges.py` emits a human-approval table).
- cycling.org.tw old wide-table years backfill (currently 2025 national source only).
- Maintainers: read `docs/learnings/` and `AGENTS.md` first (non-obvious decisions & gotchas from this round).
