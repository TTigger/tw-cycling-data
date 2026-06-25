# Race Leaderboard Comparable-Group Ranking — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the race-page leaderboard and podium group by a comparable unit `(cat, label)` and re-rank by finish time within that group, so displayed rank always matches finish time, while keeping the source rank as a reference column.

**Architecture:** Pure-frontend fix. All logic lives in `web/src/lib/racedetail.ts` (unit-tested with vitest); the two React-island components (`Leaderboard.tsx`, `Podium.tsx`) become thin consumers. No Python pipeline, no data files, no `master.json` changes.

**Tech Stack:** Astro 6 + React islands + TypeScript + vitest. Tailwind v4 classes already present in the components.

## Global Constraints

- No changes to `master.json` / `master.public.json` / `web/public/data/**` / any `scrapers/**` Python. Frontend only.
- `DetailRow` (`web/src/lib/types.ts`) is unchanged; it already has `rank, bib, name, cat, g, ag, team, t, label`.
- `categoriesOf` in `racedetail.ts` MUST be kept — `PercentileWidget.tsx` still imports it. Do not remove it.
- Verify before claiming done (AGENTS.md): `npx astro check` (0 errors) → `npx vitest run --no-file-parallelism` (green) → `npx astro build` → browser-verify → commit per task.
- Commit footer on every commit:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Group-name separator between cat and label is ` · ` (space, U+00B7 middle dot, space).
- Work happens on branch `fix/race-leaderboard-comparable-groups` (already created; spec already committed there).
- All commands run from `web/` unless stated.

## File Structure

- `web/src/lib/racedetail.ts` — add `RankedRow`, `rerankByTime`, `ComparableGroup`, `comparableGroups`, `distinctLabels`, `largestComparableGroup`. Remove dead `PodiumEntry`, `largestCategory`, `categoryPodium`. Keep `categoriesOf`, `teamStrength`, `crossYear`.
- `web/src/lib/racedetail.test.ts` — add tests for the new functions; remove tests for the deleted ones.
- `web/src/components/race/Leaderboard.tsx` — rewrite to use `comparableGroups` + `rerankByTime` + `distinctLabels`; add `原始` column.
- `web/src/components/race/Podium.tsx` — rewrite to use `comparableGroups` + `rerankByTime`.

---

### Task 1: `rerankByTime` helper

**Files:**
- Modify: `web/src/lib/racedetail.ts`
- Test: `web/src/lib/racedetail.test.ts`

**Interfaces:**
- Consumes: `DetailRow` from `./types`.
- Produces:
  - `export interface RankedRow extends DetailRow { place: number | null; }`
  - `export function rerankByTime(rows: DetailRow[]): RankedRow[]` — rows with `t != null` sorted ascending by `t`, assigned `place = 1..N`; rows with `t == null` appended in input order with `place = null`. Source `rank` is preserved on every row.

- [ ] **Step 1: Write the failing test**

Append to `web/src/lib/racedetail.test.ts` (the `d()` helper and imports already exist at the top; add `rerankByTime` to the existing import line from `./racedetail`):

```ts
describe("rerankByTime", () => {
  it("places by finish time ascending, 1..N", () => {
    const rows = [d({ name: "丙", t: 1200 }), d({ name: "甲", t: 1000 }), d({ name: "乙", t: 1100 })];
    const r = rerankByTime(rows);
    expect(r.map((x) => x.name)).toEqual(["甲", "乙", "丙"]);
    expect(r.map((x) => x.place)).toEqual([1, 2, 3]);
  });
  it("rows without time go last with null place; preserves source rank", () => {
    const rows = [d({ name: "甲", t: 1000, rank: 5 }), d({ name: "無", t: null, rank: 9 })];
    const r = rerankByTime(rows);
    expect(r.map((x) => x.name)).toEqual(["甲", "無"]);
    expect(r.map((x) => x.place)).toEqual([1, null]);
    expect(r.map((x) => x.rank)).toEqual([5, 9]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/lib/racedetail.test.ts`
Expected: FAIL — `rerankByTime is not exported` / not defined.

- [ ] **Step 3: Write minimal implementation**

Add to `web/src/lib/racedetail.ts` (after the imports, near the top):

```ts
export interface RankedRow extends DetailRow { place: number | null; }

export function rerankByTime(rows: DetailRow[]): RankedRow[] {
  const withT = rows.filter((r) => r.t != null).sort((a, b) => (a.t as number) - (b.t as number));
  const without = rows.filter((r) => r.t == null);
  return [
    ...withT.map((r, i) => ({ ...r, place: i + 1 })),
    ...without.map((r) => ({ ...r, place: null })),
  ];
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/lib/racedetail.test.ts`
Expected: PASS (new `rerankByTime` block green; existing blocks still green).

- [ ] **Step 5: Commit**

```bash
git add src/lib/racedetail.ts src/lib/racedetail.test.ts
git commit -m "feat(race): rerankByTime helper (re-rank a group by finish time)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: comparable-group helpers

**Files:**
- Modify: `web/src/lib/racedetail.ts`
- Test: `web/src/lib/racedetail.test.ts`

**Interfaces:**
- Consumes: `DetailRow` from `./types`.
- Produces:
  - `export interface ComparableGroup { key: string; name: string; cat: string | null; label: string | null; rows: DetailRow[]; count: number; }`
  - `export function comparableGroups(rows: DetailRow[]): ComparableGroup[]` — groups by `(cat ?? "", label ?? "")`; sorted by `count` descending, then `name` ascending. Name rule: if `cat` truthy → `cat`, or `` `${cat} · ${label}` `` when that cat has >1 distinct non-empty label and this group's `label` is truthy; else if `label` truthy → `label`; else `"未分組"`.
  - `export function distinctLabels(rows: DetailRow[]): number` — count of distinct non-empty `label`.
  - `export function largestComparableGroup(rows: DetailRow[]): ComparableGroup | null` — `comparableGroups(rows)[0] ?? null`.

- [ ] **Step 1: Write the failing test**

Append to `web/src/lib/racedetail.test.ts` (add `comparableGroups, distinctLabels, largestComparableGroup` to the import line from `./racedetail`):

```ts
describe("comparableGroups", () => {
  it("splits one cat with multiple labels into cat·label groups", () => {
    const rows = [
      d({ cat: "男子菁英", label: "155公里公路賽", t: 16000 }),
      d({ cat: "男子菁英", label: "20公里計時賽", t: 1500 }),
      d({ cat: "男子菁英", label: "155公里公路賽", t: 16100 }),
    ];
    const g = comparableGroups(rows);
    expect(g.map((x) => x.name).sort()).toEqual(
      ["男子菁英 · 155公里公路賽", "男子菁英 · 20公里計時賽"].sort(),
    );
    expect(g.find((x) => x.label === "155公里公路賽")?.count).toBe(2);
  });
  it("single-label cat shows just the cat name", () => {
    const rows = [d({ cat: "107K挑戰", label: "107K挑戰" }), d({ cat: "107K挑戰", label: "107K挑戰" })];
    expect(comparableGroups(rows).map((x) => x.name)).toEqual(["107K挑戰"]);
  });
  it("empty cat falls back to label, then 未分組", () => {
    expect(comparableGroups([d({ cat: null, label: "X" })])[0].name).toBe("X");
    expect(comparableGroups([d({ cat: null, label: null })])[0].name).toBe("未分組");
  });
  it("groups sorted by count descending", () => {
    const rows = [d({ cat: "A", label: null }), d({ cat: "B", label: null }), d({ cat: "B", label: null })];
    expect(comparableGroups(rows).map((x) => x.cat)).toEqual(["B", "A"]);
  });
});

describe("distinctLabels", () => {
  it("counts distinct non-empty labels", () => {
    expect(distinctLabels([d({ label: "a" }), d({ label: "a" }), d({ label: "b" }), d({ label: null })])).toBe(2);
  });
});

describe("largestComparableGroup", () => {
  it("returns the group with the most rows", () => {
    const rows = [d({ cat: "A", label: null }), d({ cat: "B", label: null }), d({ cat: "B", label: null })];
    expect(largestComparableGroup(rows)?.cat).toBe("B");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/lib/racedetail.test.ts`
Expected: FAIL — `comparableGroups is not exported` / not defined.

- [ ] **Step 3: Write minimal implementation**

Add to `web/src/lib/racedetail.ts` (after `rerankByTime`):

```ts
export interface ComparableGroup {
  key: string; name: string; cat: string | null; label: string | null;
  rows: DetailRow[]; count: number;
}

const GROUP_SEP = " ";

export function comparableGroups(rows: DetailRow[]): ComparableGroup[] {
  const labelsByCat = new Map<string, Set<string>>();
  for (const r of rows) {
    if (!r.label) continue;
    const c = r.cat ?? "";
    if (!labelsByCat.has(c)) labelsByCat.set(c, new Set());
    labelsByCat.get(c)!.add(r.label);
  }
  const byKey = new Map<string, ComparableGroup>();
  for (const r of rows) {
    const cat = r.cat ?? null;
    const label = r.label ?? null;
    const key = `${cat ?? ""}${GROUP_SEP}${label ?? ""}`;
    let g = byKey.get(key);
    if (!g) {
      let name: string;
      if (cat) {
        const multi = (labelsByCat.get(cat)?.size ?? 0) > 1;
        name = multi && label ? `${cat} · ${label}` : cat;
      } else if (label) {
        name = label;
      } else {
        name = "未分組";
      }
      g = { key, name, cat, label, rows: [], count: 0 };
      byKey.set(key, g);
    }
    g.rows.push(r);
    g.count++;
  }
  return [...byKey.values()].sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

export function distinctLabels(rows: DetailRow[]): number {
  return new Set(rows.map((r) => r.label).filter((l): l is string => !!l)).size;
}

export function largestComparableGroup(rows: DetailRow[]): ComparableGroup | null {
  return comparableGroups(rows)[0] ?? null;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/lib/racedetail.test.ts`
Expected: PASS (all blocks green).

- [ ] **Step 5: Commit**

```bash
git add src/lib/racedetail.ts src/lib/racedetail.test.ts
git commit -m "feat(race): comparableGroups/distinctLabels/largestComparableGroup

Group race rows by (cat,label) with smart display names, so multi-event
races (road race + ITT sharing one category) split into comparable units.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Rewrite `Leaderboard.tsx`

**Files:**
- Modify (full rewrite): `web/src/components/race/Leaderboard.tsx`

**Interfaces:**
- Consumes: `comparableGroups`, `rerankByTime`, `distinctLabels` from `../../lib/racedetail`; `secondsToHMS` from `../../lib/format`; `DetailRow` from `../../lib/types`.
- Produces: the `<Leaderboard rows={detail} />` island (same props as today; consumed by `RaceDetailApp.tsx`).

Behavior: build the selector from `comparableGroups(rows)`. When there is more than one group, show the dropdown; prepend an `全部` option (and default to it) only when `distinctLabels(rows) <= 1`, otherwise default to the largest (first) group. Re-rank the selected rows with `rerankByTime`. Show `名次` = `place` (`—` when null) and a new trailing `原始` column = source `rank`. Keep `PAGE = 50` pagination, resetting to page 0 on group change.

- [ ] **Step 1: Replace the file contents**

Overwrite `web/src/components/race/Leaderboard.tsx` with:

```tsx
import { useMemo, useState } from "react";
import { comparableGroups, rerankByTime, distinctLabels } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const PAGE = 50;
const ALL = "__all__";

export default function Leaderboard({ rows }: { rows: DetailRow[] }) {
  const groups = useMemo(() => comparableGroups(rows), [rows]);
  const showAll = useMemo(() => distinctLabels(rows) <= 1, [rows]);
  const multi = groups.length > 1;
  const options = useMemo(
    () => (multi && showAll ? [{ key: ALL, name: "全部" }, ...groups] : groups),
    [groups, multi, showAll],
  );
  const [sel, setSel] = useState<string>(() => (multi && showAll ? ALL : groups[0]?.key ?? ""));
  const [page, setPage] = useState(0);

  const selectedRows = useMemo(() => {
    if (sel === ALL) return rows;
    return groups.find((g) => g.key === sel)?.rows ?? rows;
  }, [rows, groups, sel]);

  const ranked = useMemo(() => rerankByTime(selectedRows), [selectedRows]);
  const pages = Math.max(1, Math.ceil(ranked.length / PAGE));
  const p = Math.min(page, pages - 1);
  const slice = ranked.slice(p * PAGE, p * PAGE + PAGE);

  return (
    <div>
      <div className="mb-3 flex items-center gap-3 text-sm">
        {multi && (
          <select aria-label="篩選組別" className="max-w-[18rem] rounded-lg border border-border bg-surface px-3 py-2 text-ink"
            value={sel} onChange={(e) => { setSel(e.target.value); setPage(0); }}>
            {options.map((o) => <option key={o.key} value={o.key}>{o.name}</option>)}
          </select>
        )}
        <span className="text-muted">{ranked.length.toLocaleString()} 筆</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted">
              <th className="py-2 pr-3">名次</th><th className="pr-3">號碼</th><th className="pr-3">姓名</th>
              <th className="pr-3">組別</th><th className="pr-3">車隊</th><th className="pr-3">完賽</th>
              <th className="pr-3">原始</th>
            </tr>
          </thead>
          <tbody>
            {slice.map((r, i) => (
              <tr key={`${r.bib}-${i}`} className="border-b border-border/60 transition-colors hover:bg-accent/5">
                <td className="num py-1.5 pr-3">{r.place ?? "—"}</td>
                <td className="num pr-3 text-muted">{r.bib ?? ""}</td>
                <td className="pr-3 text-ink">{r.name ?? "—"}</td>
                <td className="pr-3 text-muted">{r.cat ?? ""}</td>
                <td className="pr-3 text-muted">{r.team ?? ""}</td>
                <td className="num pr-3">{secondsToHMS(r.t)}</td>
                <td className="num pr-3 text-muted">{r.rank ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="mt-3 flex items-center gap-3 text-sm">
          <button className="rounded border border-border px-2 py-1 text-muted disabled:opacity-40"
            disabled={p <= 0} onClick={() => setPage(p - 1)}>上一頁</button>
          <span className="num text-muted">{p + 1} / {pages}</span>
          <button className="rounded border border-border px-2 py-1 text-muted disabled:opacity-40"
            disabled={p >= pages - 1} onClick={() => setPage(p + 1)}>下一頁</button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

Run: `npx astro check`
Expected: 0 errors, 0 warnings (no unresolved imports; `categoriesOf` no longer imported here).

- [ ] **Step 3: Build**

Run: `npx astro build`
Expected: build succeeds, `dist/` produced.

- [ ] **Step 4: Commit**

```bash
git add src/components/race/Leaderboard.tsx
git commit -m "fix(race): leaderboard ranks by finish time within comparable group

Group by (cat,label), re-rank within the selected group by finish time so
名次 matches 完賽; add an 原始 column for the source rank. Default to the
largest group (or 全部 for single-event races).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Rewrite `Podium.tsx` and remove dead helpers

**Files:**
- Modify (full rewrite): `web/src/components/race/Podium.tsx`
- Modify: `web/src/lib/racedetail.ts` (remove `PodiumEntry`, `largestCategory`, `categoryPodium`)
- Modify: `web/src/lib/racedetail.test.ts` (remove the `largestCategory` and `categoryPodium` describe blocks and drop them from the import line)

**Interfaces:**
- Consumes: `comparableGroups`, `rerankByTime` from `../../lib/racedetail`; `secondsToHMS` from `../../lib/format`; `DetailRow` from `../../lib/types`.
- Produces: the `<Podium rows={detail} />` island (same props; consumed by `RaceDetailApp.tsx`).

Behavior: selector from `comparableGroups(rows)`, default first (largest) group, dropdown only when >1 group. Podium entries = top 3 of the selected group by `rerankByTime` (filter out `t == null`), showing `place` 1/2/3.

- [ ] **Step 1: Replace `Podium.tsx`**

Overwrite `web/src/components/race/Podium.tsx` with:

```tsx
import { useMemo, useState } from "react";
import { comparableGroups, rerankByTime } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const MEDAL = ["#D9A441", "#9FA6AD", "#B07A52"];

export default function Podium({ rows }: { rows: DetailRow[] }) {
  const groups = useMemo(() => comparableGroups(rows), [rows]);
  const [sel, setSel] = useState<string>(() => groups[0]?.key ?? "");
  const entries = useMemo(() => {
    const g = groups.find((x) => x.key === sel) ?? groups[0];
    return g ? rerankByTime(g.rows).filter((r) => r.t != null).slice(0, 3) : [];
  }, [groups, sel]);
  if (!groups.length) return <p className="text-muted">無組別名次資料</p>;
  return (
    <div>
      {groups.length > 1 && (
        <select aria-label="選擇組別" className="mb-3 max-w-[18rem] rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink"
          value={sel} onChange={(e) => setSel(e.target.value)}>
          {groups.map((g) => <option key={g.key} value={g.key}>{g.name}</option>)}
        </select>
      )}
      <div className="flex flex-wrap gap-3">
        {entries.map((p, i) => (
          <div key={i} className="min-w-[140px] flex-1 rounded-xl border border-border bg-surface p-3">
            <div className="num text-lg" style={{ color: MEDAL[i] }}>#{p.place}</div>
            <div className="text-ink">{p.name ?? "—"}</div>
            <div className="text-xs text-muted">{p.team ?? ""}</div>
            <div className="num text-sm text-muted">{secondsToHMS(p.t)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Remove dead helpers from `racedetail.ts`**

Delete these three exports from `web/src/lib/racedetail.ts` (lines currently 8, 10–16, 18–24):

```ts
export interface PodiumEntry { rank: number; name: string | null; team: string | null; t: number | null; }

export function largestCategory(rows: DetailRow[]): string | null {
  const counts = new Map<string, number>();
  for (const r of rows) { if (!r.cat) continue; counts.set(r.cat, (counts.get(r.cat) || 0) + 1); }
  let best: string | null = null; let n = -1;
  for (const [c, k] of counts) if (k > n) { n = k; best = c; }
  return best;
}

export function categoryPodium(rows: DetailRow[], cat: string, n = 3): PodiumEntry[] {
  return rows
    .filter((r) => r.cat === cat && r.t != null)
    .sort((a, b) => (a.t as number) - (b.t as number))
    .slice(0, n)
    .map((r, i) => ({ rank: i + 1, name: r.name, team: r.team, t: r.t }));
}
```

Keep `categoriesOf` (still imported by `PercentileWidget.tsx`), `teamStrength`, `crossYear`, and the new helpers.

- [ ] **Step 3: Remove dead tests from `racedetail.test.ts`**

In `web/src/lib/racedetail.test.ts`: change the import line to drop `largestCategory, categoryPodium` (keep `categoriesOf, teamStrength, crossYear` plus the new functions), and delete these two describe blocks:

```ts
describe("largestCategory", () => {
  it("returns the category with the most rows (ignoring null)", () => {
    const rows = [d({ cat: "A" }), d({ cat: "B" }), d({ cat: "B" }), d({ cat: null })];
    expect(largestCategory(rows)).toBe("B");
  });
});

describe("categoryPodium", () => {
  it("top-3 of a category by time, positioned 1-2-3", () => {
    const rows = [
      d({ cat: "M25", t: 1200, name: "丙" }), d({ cat: "M25", t: 1000, name: "甲" }),
      d({ cat: "M25", t: 1100, name: "乙" }), d({ cat: "M25", t: 1300, name: "丁" }),
      d({ cat: "其他", t: 500, name: "別組" }),
    ];
    const p = categoryPodium(rows, "M25", 3);
    expect(p.map((e) => e.name)).toEqual(["甲", "乙", "丙"]);
    expect(p.map((e) => e.rank)).toEqual([1, 2, 3]);
  });
});
```

- [ ] **Step 4: Type-check + full test suite + build**

Run: `npx astro check`
Expected: 0 errors (no references to removed `largestCategory`/`categoryPodium`/`PodiumEntry` remain).

Run: `npx vitest run --no-file-parallelism`
Expected: PASS, full suite green.

Run: `npx astro build`
Expected: build succeeds.

- [ ] **Step 5: Browser-verify**

Run: `npx astro dev` (or `npm run dev`), open `http://localhost:4321/race`.
1. Select **102年全國自由車公路錦標賽 (2013)**. On the 成績 tab:
   - The 排行榜 dropdown shows split options like `男子菁英 · 155公里個人公路賽` and `男子菁英 · 20公里個人計時賽` (no `全部` for this multi-event race); default is the largest group.
   - Within a selected group, `名次` reads 1,2,3,… in step with ascending `完賽` time; the `原始` column shows the source rank.
   - 領獎台 shows three entries whose times are the three fastest of the selected group, numbered #1 #2 #3.
2. Select a single-event citizen race (e.g. **彰化經典百K**): the dropdown offers `全部` as default; 名次 1..N matches time.

Confirm both before committing.

- [ ] **Step 6: Commit**

```bash
git add src/components/race/Podium.tsx src/lib/racedetail.ts src/lib/racedetail.test.ts
git commit -m "fix(race): podium uses comparable groups; drop dead category helpers

Podium groups by (cat,label) and ranks by finish time, so a merged ITT no
longer pollutes a road-race podium. Remove now-unused largestCategory and
categoryPodium (and their tests); categoriesOf stays for PercentileWidget.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage:**
- "純前端,master 不動" → Global Constraints; no data/Python files touched. ✓
- `comparableGroups` (cat,label) + display-name rule → Task 2. ✓
- `rerankByTime` (nulls last, place null) → Task 1. ✓
- `largestComparableGroup` / `distinctLabels` / "全部" rule + default-largest → Task 2 (helpers) + Task 3 (component assembly). ✓
- `原始` column = source rank → Task 3. ✓
- Podium uses same grouping → Task 4. ✓
- Remove unused `largestCategory`/`categoryPodium`; keep `categoriesOf` → Task 4 + Global Constraints. ✓
- Tests 1–7 from spec → Task 1 (nulls/place) + Task 2 (groups, names, distinctLabels, largest). The spec's "single-group hides selector" and "全部 only when ≤1 label" are component behaviors verified via browser in Task 4 Step 5 (no component unit-test harness in repo). ✓
- Verification chain (astro check → vitest → build → browser) → Tasks 3 & 4. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"; every code step shows full code. ✓

**Type consistency:** `RankedRow.place` used in Leaderboard (`r.place`) and Podium (`p.place`); `ComparableGroup.key/name/rows/cat/label/count` used consistently in both components and helpers; `comparableGroups`/`rerankByTime`/`distinctLabels`/`largestComparableGroup` names identical across tasks. ✓
