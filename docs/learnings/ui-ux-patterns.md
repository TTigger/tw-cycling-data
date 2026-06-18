# UI/UX patterns (detail pages)

Conventions settled while reducing vertical overload and making navigation
predictable. Apply these so pages stay consistent.

## Tabs (taming long pages)
Shared component: `web/src/components/Tabs.tsx` (controlled underline bar with
accessible roles). The parent owns the active key in local `useState`.

- **Use tabs when** a page stacks several *independent* sections in one long
  column (athlete profile, race detail, insights). Group related sections under
  a few tabs; keep the count small (~3–4).
- **Do NOT tab** a *linked* multi-chart view that shares one control — e.g. the
  explore page's 4 charts all driven by one FilterBar: the value is seeing the
  distributions together while filtering, so a responsive grid beats tabs.
- **Keep the always-relevant header outside the tabs** (name, key stats, action
  buttons, back link, year pills). Only the lower content switches.
- **Local state, no URL sync.** Tab state is deliberately not pushed to history
  → the browser Back button leaves the page instead of cycling tabs. (If shareable
  tabs are ever wanted, reflect with `replaceState`, never `pushState`.)
- **Conditional tabs**: only include a tab when its data exists (e.g. the athlete
  "對手" tab appears only when `d.rivals?.length`).
- **Reset per entity**: key the detail component by id (`<AthleteProfile key={id}>`)
  so switching entity resets to the default tab and remounts cleanly.
- Lazy content (see [client data loading](./client-data-loading.md), `useInView`)
  now loads when its tab opens — a bonus: hidden tabs don't fetch.

Current groupings: athlete = 總覽 / 分析 / 對手 / 歷年成績; race = 成績 / 分析 /
賽事 DNA; insights = 紀錄牆 / 選手趨勢 / 賽事 / 工具.

## Year-switch pills (race detail)
The race header shows pills for every year of the same `rk` (from the already
loaded `races`). The current year is a non-link active chip; the others are
`<a href={raceHref(rk, y)}>` links to that year's pre-rendered SSG page — so
switching year is one click, lands on the crawlable page, and keeps the URL clean
(no `?rk=&y=` appended). See [spa-routing](./spa-routing.md) for `raceHref`.

## Back / navigation convention
- Every detail view has a **top-left** `‹ 所有賽事 / 所有選手 / 所有車隊` back
  affordance (where users expect "back"), NOT a right-side "換一場/換一位".
- Behaviour: on an **SSG path page** (deep link / `initRk`/`initId`) the back
  link **navigates to the list** (`/race`, `/athletes`); on the **SPA** it
  **deselects in place** (no reload). 
- The browser Back button works because every query-param SPA island has a
  `popstate` listener that restores state from the URL — if you add another such
  island, add the listener too (see [spa-routing](./spa-routing.md)).
