# Client data loading & performance

Core principle: **don't ship raw row dumps to the browser.** This is a static
Astro site with React islands; whatever a page `fetch()`es is downloaded AND
parsed on the main thread.

## The viz.json lesson (2026-06)
`viz.json` is 116,953 records / **24.5MB raw** (≈955KB gzip) and was loaded on the
homepage, explore, AND every race page — just to compute a few aggregates. Parsing
24.5MB of JSON blocked first paint on the landing page.

Fix: **precompute at build time** in `build_viz.py` (mirror the TS aggregation,
match `aggregate.ts` quantile):
- `overview.json` (~4KB) — the 5 homepage aggregates (`build_overview`). The
  homepage and its charts now take precomputed props instead of raw rows.
- `race_crossyear.json` (~8KB) — per-race winner/median (`build_crossyear`); the
  race page loads this (cached) instead of `viz.json`.
- `viz.json` is still built but only `explore` loads it — that page does genuine
  row-level interactive filtering, so it is the one legitimate consumer.

Result: homepage data 24.5MB → 4KB; race page → 8KB (cached across races).

## Lazy-load below-the-fold heavy data
- `web/src/lib/useInView.ts` (IntersectionObserver, latches once seen) gates
  loading. Example: the 騎乘分身 (Doppelganger) card needs the ~1MB
  `athlete_features.json`; it only fetches once the section scrolls near.
- On deep-linked athlete pages, load the athlete's own detail immediately and
  defer the 2.6MB `athletes.json` index to `requestIdleCallback` — don't block the
  main content behind the index.

## Rules of thumb when adding a feature
- If a component only needs an aggregate/summary, add a builder that precomputes
  it (see [data pipeline](./data-pipeline.md)) — don't fetch the full dataset.
- Cache cross-view fetches with a module-level promise in `data-load.ts`.
- Below-the-fold or rarely-used heavy data → `useInView` or interaction-gated.
- Theme/host gzip is host-controlled (GitHub Pages auto-gzips text); structural
  slimming is what we actually control.
