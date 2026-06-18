# Race-key normalization

`scrapers/normalize.py` has a curated `RACE_KEY_CANONICAL` dict (applied in
`enrich()`) that collapses the **same** annual event that source naming split by
屆次 / HTML-entity / English tail / sponsor word-order / division / heat into one
canonical `race_key` (+ `race_name_canonical`). Pure re-key — rows unchanged, each
member keeps its year — so cross-year / DNA / series / H2H views see one race.

State (2026-06): 187 raw race-years → **126 distinct races**. Two batches applied:
safe (edition variants) + a human-approved review batch (扶輪盃陽明山登山王;
桃園市運動會 分齡組→base; GravelFundo collapsed by 地點+賽別 incl. heats).

## What must NOT be merged (would corrupt cross-year)
Different events that share a name — merging breaks the "one finish-time
distribution per year" assumption:
- the 3 武嶺 by organizer (崇越 ≠ NeverStop ≠ 96聯賽)
- KOM 登山王之路 春季/夏季 (different courses)
- Day1/Day2 stage races; 崇越武嶺 2025 六月/九月 (two editions in one year)
- 瘋系列 西/東/蘇花部段 (different segments)
- 96聯賽 挑戰組 vs 競賽組 (different routes/field)
- GravelFundo 年終站 / 頂成ZIPP (distinct)

## Candidate generator (do NOT auto-apply)
`scrapers/suggest_race_merges.py` clusters the current race_keys and writes a
human-approval table (`data/processed/race_merge_candidates.{md,json}`,
gitignored) — it never edits the map. 3-tier verdict:
- **REJECT** — members differ by a corrupt marker (`Day#`/`季`/`部段`/`場次`/paired
  `六月·九月`); auto-flagged as distinct.
- **SAFE** — one core, ≥2 keys: edition/spelling variants (hint, still verify —
  different sponsors can share a generic tail like 「嘉年華」).
- **REVIEW** — genuine judgement (division splits, stage/heat structure).

To extend: add exact keys to `RACE_KEY_CANONICAL`, then rebuild
(see [data pipeline](./data-pipeline.md)) and get per-group human sign-off first.
