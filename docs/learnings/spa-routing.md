# SPA routing & SSG hybrid

The site mixes two URL schemes; know which a page uses before touching links.

## Two schemes
- **Query-param SPA** (works for everything): `/race?rk=&y=`, `/athletes?id=`
  (+`&vs=` compare), `/teams?id=`, `/climbs?rk=&y=`. The React island reads the
  query in a mount effect and `history.pushState`es on select.
- **Path SSG** (crawlable, real per-entity `<head>` meta + OG): `/race/<file>` for
  **all** races; `/athletes/<id>` for **only the top-300** most-raced riders
  (`getStaticPaths`). These mount the same island preselected via props
  (`initRk`/`initY`, `initId`).

Internal link policy: **races link to the SSG path** `/race/<file>` everywhere
(all races are pre-rendered → crawlable, per-race meta/OG, self-canonical). Use
the helper `lib/race-url.ts` `raceHref(rk, y)` — its slug must match
`build_viz.race_file_name` exactly (validated against races.json). **Athletes
stay on `/athletes?id=`** because only the top-300 are pre-rendered AND names are
masked (PDPA), so per-athlete SEO has little value — generating 21k pages isn't
worth it. See [PDPA](./pdpa-deidentification.md).

## popstate is required (was a real bug)
The SPA islands `pushState` on select but originally had **no `popstate`
listener**, so the browser Back button changed the URL while the view stayed put
("can't get back"). Every SPA island (race/athletes/teams/climbs) now has a
`popstate` effect that restores state from the URL: id/rk+y present → re-pick;
absent → back to the list; on an SSG path page fall back to `initRk`/`initId`.
**If you add another query-param SPA island, add the popstate effect too.**

## Base URL
`base = import.meta.env.BASE_URL.replace(/\/$/, "")` — the site is served at root
(`BASE_URL` is `/`). `astro.config.mjs` sets `site` for absolute canonical/OG
URLs; override it if the deploy domain changes.

Related: [client data loading](./client-data-loading.md).
