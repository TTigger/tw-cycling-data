# Learnings — tw-cycling-data

A committed knowledge base of **non-obvious, project-specific** decisions and
gotchas — the things that are NOT derivable from reading the code, and that cost
real time to (re)discover. Aimed at future contributors and coding agents.

## How to use / extend
- One file per topic. Keep each focused on **why** and **how to apply**, not a
  restatement of the code.
- Cross-reference with relative links, e.g. `[data pipeline](./data-pipeline.md)`.
- Add a one-line pointer to the index below when you add a file.
- If a learning becomes stale (file/flag renamed, decision reversed), fix or
  delete it — a wrong note is worse than none.

## Index
- [Data pipeline & rebuild](./data-pipeline.md) — sources → `merge.py` → master → builders → `web/public/data`; how to regenerate; the `build_viz` OOM retry.
- [PDPA de-identification](./pdpa-deidentification.md) — only masked names are ever committed; real names are composited client-side only. Hard constraint.
- [Client data loading & performance](./client-data-loading.md) — precompute aggregates, lazy-load below-the-fold, never ship raw row dumps (the 24.5MB `viz.json` lesson).
- [SPA routing & SSG hybrid](./spa-routing.md) — query-param SPA + path SSG pages, the `popstate` requirement, base-URL handling.
- [Tailwind v4 dark mode](./tailwind-v4-dark-mode.md) — class-based dark mode tokens get stripped at build; the `@theme inline` + fallback pattern that works.
- [Race-key normalization](./race-key-normalization.md) — curated canonical merge map + candidate generator + what must NOT be merged.
