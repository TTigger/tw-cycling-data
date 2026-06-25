# Race leaderboard ranking & grouping

The per-race leaderboard/podium must NOT trust the source `rank` field or group
by `category_raw` alone. Two non-obvious data realities force re-ranking on the
frontend:

1. **`category_raw` collapses distinct events.** Competitive meets put several
   sub-events under one category name. e.g. 2013 全國公路錦標賽 → `男子菁英`
   contains BOTH `155公里個人公路賽` (≈4.5h) and `20公里個人計時賽` (≈26min).
   The field that actually separates them is `label` (= `result_label`), not
   `cat`. So the comparable unit is **`(cat, label)`**, never `cat`.
2. **`rank` (`rank_overall`) is not a true overall rank.** For single-group
   citizen races it equals 1..N by time; for competitive meets it's the
   source's *within-sub-event* placement (so one `cat` shows repeated 1/2/3).
   Even inside a correct `(cat,label)` group, ~13.7% of groups had source-rank
   order inconsistent with finish time (認證/檢定, some league classes) — and a
   few groups (e.g. a `U15` with two time clusters) can't be separated at all
   because `cat`/`label`/`gender` are all identical in the source.

## The rule the UI applies (`web/src/lib/racedetail.ts`)
- `comparableGroups(rows)` groups by `(cat, label)`; display name shows the
  分項 (`組別 · 分項`) only when a cat spans >1 label, else just the cat.
- `rerankByTime(rows)` re-ranks **within the shown group** by `finish_seconds`
  (nulls last → `place=null`). This is the only thing that guarantees 名次
  matches 完賽; the source `rank` is shown beside it as a read-only `原始`
  column for transparency.
- Selector default: single-`label` races offer 「全部」(same distance = a real
  overall list) as default; multi-`label` races omit 「全部」(mixing distances
  is meaningless) and default to the largest group. One group → hide the
  selector. Podium uses the same grouping so a merged ITT can't pollute a road
  podium.

## Why frontend, not the data pipeline
`master` is correct — it faithfully stores `category_raw`, `result_label`, and
the source `rank`. The bug was purely *presentation*, so the fix lives in the
web layer (no rebuild, no PDPA surface). If you ever bake a comparable-group
key or a recomputed place into `build_viz.py`, keep the source `rank` too.

Re-ranking by time intentionally overrides any official placement (penalties,
points races) — acceptable because the site is 參考-only ("以主辦公告為準"),
and the `原始` column keeps the source result visible.
