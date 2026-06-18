# AGENTS.md

Taiwan road-cycling results platform: Python builders (`scrapers/`) turn scraped
results into de-identified JSON consumed by a static Astro 6 + React-islands site
(`web/`, root). Data 2009–2026.

## Before non-trivial work, read `docs/learnings/`
A curated knowledge base of non-obvious decisions and gotchas (build pipeline,
dark-mode build trap, client data-loading rules, routing, PDPA, race-key merges).
Start at [docs/learnings/README.md](./docs/learnings/README.md). Add to it when you
learn something that cost time to discover.

## Hard constraints
- **PDPA**: only masked names (`王○明`) are ever committed/shipped; real names stay
  client-side and transient. See [docs/learnings/pdpa-deidentification.md](./docs/learnings/pdpa-deidentification.md).
- **Verify before claiming done**: `npx astro check` (0 errors) → vitest
  (`--no-file-parallelism`) / `pytest scrapers/` → `npx astro build` →
  browser-verify → commit per feature. Commit footer:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **Data changes** go through `python scrapers/merge.py` then the builders — see
  [docs/learnings/data-pipeline.md](./docs/learnings/data-pipeline.md).
