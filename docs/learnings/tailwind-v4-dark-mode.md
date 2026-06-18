# Tailwind v4 dark mode (token override gets stripped)

**Symptom found 2026-06:** class-based dark mode was silently dead in the
production build — the toggle added `html.dark` but nothing changed.

**Cause:** Tailwind v4's build **strips author custom-property declarations** that
sit on `:root` / bare `html`, and any `--color-*` (theme-namespaced) override
declared outside `@theme`. So `html.dark { --color-bg: … }` (and even a plain
`html { --color-bg }`) never reached the bundle. Verified by grepping the built
CSS: the dark token values (`#18171A` …) were absent while the light `@theme`
`:root` block was present.

## Working pattern (`web/src/styles/tokens.css` + `global.css`)
- `global.css`, after `@import "tailwindcss"`:
  `@custom-variant dark (&:where(.dark, .dark *));`
  so `dark:` utilities follow the `.dark` class (default is prefers-color-scheme).
- `tokens.css`:
  - `@theme inline { --color-bg: var(--bg, #FAF9F5); … }` — light value lives as
    the `var()` **fallback**, so utilities emit `var(--bg, #FAF9F5)`.
  - a `html { --bg: #FAF9F5; … }` light block — its output is stripped, but its
    presence keeps the dark override "alive" (a lone `html.dark` block also gets
    tree-shaken).
  - `html.dark { --bg: #18171A; … }` — the one selector that survives and does
    the flip.
  - Fonts stay in a normal `@theme` (they never flip; emits `--font-*` to `:root`
    so `var(--font-*)` still resolves in bare rules).

## Verify after any token change
Build, then grep the dist CSS — **both** must appear:
`grep -c "FAF9F5\|faf9f5" dist/_astro/*.css` and `grep -c "18171A\|18171a" …`.

## Other traps
- An **apostrophe in a CSS comment** (e.g. `Tailwind's`) makes the v4 parser throw
  `Unterminated string`. Keep CSS comments apostrophe-free.
- ECharts: theme colors live in `lib/echarts-theme.ts` (`claude` / `claude-dark`,
  incl. a `radar` block). `EChart.tsx` re-mounts on the `themechange` event via
  `key={theme}`. **Don't hard-code colors inline in chart options** (legend / axis
  / label / radar) — let the theme drive them or they won't flip.
