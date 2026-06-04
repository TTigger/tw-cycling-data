# 公路車儀表板 — Plan 2:探索頁(全域篩選 + 連動圖)實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 做出「探索頁」`/explore`:全域篩選器(年/系列/賽事/組別類型/性別/分齡組)+ 4 張 ECharts 連動圖(完賽時間分布、分齡組 vs 完賽時間箱型、賽事競爭強度離散度、距離 vs 平均速度),在瀏覽器記憶體即時篩選與重算,點圖可交叉篩選。

**Architecture:** Astro 頁 `explore.astro` 掛一個 `client:only="react"` 的 `ExploreApp` island。ExploreApp 載入一次 `viz.json`+`races.json`,訂閱既有的 `$filters` nanostore,套用 `applyFilters` 後把資料丟給 4 個圖元件。圖的資料轉換是純函式(`aggregate.ts`,TDD);圖元件用共用 `EChart` 包裝(註冊 Claude ECharts 主題)。交叉篩選:點箱型圖的組別→設 `ageGroup`;點競爭強度的賽事→設 `race`。

**Tech Stack:** Astro 6 · React 19 islands(client:only)· ECharts 6 + echarts-for-react · nanostores · TypeScript · Vitest。沿用 Plan 1 的 `web/src/lib/{types,data-load,format,filter-store}.ts` 與 Claude design tokens。

設計依據:`docs/superpowers/specs/2026-06-04-cycling-dashboard-design.md` 頁 B。

---

## 檔案結構(本 plan 建立)

```
web/src/
  lib/
    aggregate.ts        純函式:quantile / histogram / boxByGroup / raceSpread / distSpeedPoints / facetOptions
    aggregate.test.ts   Vitest
    echarts-theme.ts    註冊 "claude" ECharts 主題(暖色/字體)
  components/
    charts/
      EChart.tsx              echarts-for-react 包裝(套 claude 主題)
      FinishTimeHistogram.tsx 完賽時間分布(直方圖)
      AgeBoxplot.tsx          分齡組 vs 完賽時間(箱型,點擊設 ageGroup)
      CompetitivenessSpread.tsx 競爭強度離散度(點擊設 race)
      DistanceSpeedScatter.tsx  距離 vs 平均速度(散點)
    explore/
      FilterBar.tsx     下拉篩選器(綁 $filters)
      ExploreApp.tsx    orchestrator(載資料、訂閱 store、版面、空狀態)
  pages/
    explore.astro       /explore 頁(Base 版型 + ExploreApp island)
```

---

## Task 1:聚合純函式 + 篩選選項(TDD)

**Files:**
- Create: `web/src/lib/aggregate.ts`, `web/src/lib/aggregate.test.ts`

- [ ] **Step 1: 寫失敗測試** — `web/src/lib/aggregate.test.ts`

```ts
import { describe, it, expect } from "vitest";
import { quantile, histogram, boxByGroup, raceSpread, distSpeedPoints, facetOptions } from "./aggregate";

describe("quantile", () => {
  it("odd/even/edges", () => {
    expect(quantile([1, 2, 3, 4, 5], 0.5)).toBe(3);
    expect(quantile([1, 2, 3, 4], 0.5)).toBe(2.5);
    expect(quantile([1, 2, 3, 4, 5], 0)).toBe(1);
    expect(quantile([1, 2, 3, 4, 5], 1)).toBe(5);
    expect(Number.isNaN(quantile([], 0.5))).toBe(true);
  });
});

describe("histogram", () => {
  it("buckets values by bin size", () => {
    const bins = histogram([10, 20, 30, 40], 10);
    expect(bins.length).toBe(4);
    expect(bins[0]).toEqual({ x0: 10, x1: 20, count: 1 });
    expect(bins.every((b) => b.count === 1)).toBe(true);
  });
  it("empty / bad bin -> []", () => {
    expect(histogram([], 10)).toEqual([]);
    expect(histogram([1, 2], 0)).toEqual([]);
  });
});

describe("boxByGroup", () => {
  it("computes 5-number summary per group, drops small groups", () => {
    const rows = [
      ...Array.from({ length: 8 }, (_, i) => ({ ag: "M30", t: (i + 1) * 100 })),
      { ag: "M40", t: 500 }, // only 1 -> dropped at minN=8
      { ag: null, t: 999 },  // null ag -> ignored
    ];
    const boxes = boxByGroup(rows, 8);
    expect(boxes.length).toBe(1);
    expect(boxes[0].group).toBe("M30");
    expect(boxes[0].n).toBe(8);
    expect(boxes[0].min).toBe(100);
    expect(boxes[0].max).toBe(800);
    expect(boxes[0].median).toBe(450);
  });
});

describe("raceSpread", () => {
  it("winner/median/ratio per race; excludes 認證 and small fields", () => {
    const rows = [
      ...Array.from({ length: 10 }, (_, i) => ({ rk: "A", y: 2025, t: 100 + i * 10, rc: "競賽" })),
      { rk: "B", y: 2025, t: 200, rc: "認證" }, // excluded by rc
    ];
    const s = raceSpread(rows, 10);
    expect(s.length).toBe(1);
    expect(s[0].rk).toBe("A");
    expect(s[0].winner).toBe(100);
    expect(s[0].n).toBe(10);
    expect(s[0].ratio).toBeGreaterThan(1);
  });
});

describe("distSpeedPoints", () => {
  it("keeps only rows with both dist and spd", () => {
    const pts = distSpeedPoints([
      { dist: 100, spd: 30, rc: "競賽" },
      { dist: null, spd: 30, rc: "競賽" },
      { dist: 50, spd: null, rc: "市民" },
    ]);
    expect(pts).toEqual([{ dist: 100, spd: 30, rc: "競賽" }]);
  });
});

describe("facetOptions", () => {
  it("distinct sorted values per facet", () => {
    const rows = [
      { y: 2025, s: "96聯賽", rc: "競賽", g: "M", ag: "M30" },
      { y: 2024, s: "96聯賽", rc: "挑戰", g: "F", ag: null },
    ] as any;
    const f = facetOptions(rows);
    expect(f.years).toEqual([2024, 2025]);
    expect(f.series).toEqual(["96聯賽"]);
    expect(f.raceClasses.sort()).toEqual(["挑戰", "競賽"]);
    expect(f.genders).toEqual(["F", "M"]);
    expect(f.ageGroups).toEqual(["M30"]);
  });
});
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd web && npm test`
Expected: FAIL(找不到 `./aggregate` 匯出)

- [ ] **Step 3: 實作** — `web/src/lib/aggregate.ts`

```ts
import type { SlimRecord } from "./types";

export function quantile(sorted: number[], q: number): number {
  if (sorted.length === 0) return NaN;
  if (sorted.length === 1) return sorted[0];
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  const next = sorted[base + 1];
  return next !== undefined ? sorted[base] + rest * (next - sorted[base]) : sorted[base];
}

export interface Bin { x0: number; x1: number; count: number; }
export function histogram(values: number[], binSeconds: number): Bin[] {
  const v = values.filter((x) => Number.isFinite(x));
  if (!v.length || binSeconds <= 0) return [];
  const min = Math.min(...v);
  const max = Math.max(...v);
  const start = Math.floor(min / binSeconds) * binSeconds;
  const bins: Bin[] = [];
  for (let x = start; x <= max; x += binSeconds) bins.push({ x0: x, x1: x + binSeconds, count: 0 });
  for (const x of v) {
    const i = Math.min(bins.length - 1, Math.floor((x - start) / binSeconds));
    bins[i].count++;
  }
  return bins;
}

export interface Box { group: string; min: number; q1: number; median: number; q3: number; max: number; n: number; }
export function boxByGroup(rows: { ag: string | null; t: number | null }[], minN = 8): Box[] {
  const groups = new Map<string, number[]>();
  for (const r of rows) {
    if (r.ag == null || r.t == null) continue;
    const a = groups.get(r.ag) || [];
    a.push(r.t);
    groups.set(r.ag, a);
  }
  const out: Box[] = [];
  for (const [g, arr] of groups) {
    if (arr.length < minN) continue;
    arr.sort((a, b) => a - b);
    out.push({
      group: g, n: arr.length, min: arr[0], max: arr[arr.length - 1],
      q1: quantile(arr, 0.25), median: quantile(arr, 0.5), q3: quantile(arr, 0.75),
    });
  }
  return out.sort((a, b) => a.group.localeCompare(b.group));
}

export interface Spread { key: string; rk: string; y: number | null; winner: number; median: number; ratio: number; n: number; }
export function raceSpread(
  rows: { rk: string; y: number | null; t: number | null; rc: string | null }[],
  minN = 10,
): Spread[] {
  const g = new Map<string, { rk: string; y: number | null; ts: number[] }>();
  for (const r of rows) {
    if (r.t == null || r.rc === "認證") continue;
    const k = `${r.rk}__${r.y}`;
    const e = g.get(k) || { rk: r.rk, y: r.y, ts: [] };
    e.ts.push(r.t);
    g.set(k, e);
  }
  const out: Spread[] = [];
  for (const [k, e] of g) {
    if (e.ts.length < minN) continue;
    e.ts.sort((a, b) => a - b);
    const winner = e.ts[0];
    const median = quantile(e.ts, 0.5);
    out.push({ key: k, rk: e.rk, y: e.y, winner, median, ratio: winner > 0 ? median / winner : 0, n: e.ts.length });
  }
  return out.sort((a, b) => b.ratio - a.ratio);
}

export interface ScatterPt { dist: number; spd: number; rc: string | null; }
export function distSpeedPoints(rows: { dist: number | null; spd: number | null; rc: string | null }[]): ScatterPt[] {
  const out: ScatterPt[] = [];
  for (const r of rows) if (r.dist != null && r.spd != null) out.push({ dist: r.dist, spd: r.spd, rc: r.rc });
  return out;
}

export interface Facets { years: number[]; series: string[]; raceClasses: string[]; genders: string[]; ageGroups: string[]; }
export function facetOptions(rows: SlimRecord[]): Facets {
  const years = new Set<number>(), series = new Set<string>(), rc = new Set<string>(),
        g = new Set<string>(), ag = new Set<string>();
  for (const r of rows) {
    if (r.y != null) years.add(r.y);
    if (r.s) series.add(r.s);
    if (r.rc) rc.add(r.rc);
    if (r.g) g.add(r.g);
    if (r.ag) ag.add(r.ag);
  }
  return {
    years: [...years].sort((a, b) => a - b),
    series: [...series].sort(),
    raceClasses: [...rc].sort(),
    genders: [...g].sort(),
    ageGroups: [...ag].sort(),
  };
}
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd web && npm test`
Expected: PASS(原 format 測試 + 新 aggregate 測試全綠)

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/lib/aggregate.ts web/src/lib/aggregate.test.ts
git commit -m "feat(web): explore-page aggregation functions (tested)"
```

---

## Task 2:ECharts Claude 主題 + EChart 包裝元件

**Files:**
- Create: `web/src/lib/echarts-theme.ts`, `web/src/components/charts/EChart.tsx`

- [ ] **Step 1: 註冊主題** — `web/src/lib/echarts-theme.ts`

```ts
import * as echarts from "echarts";

// Claude warm palette, registered once and referenced by name "claude".
echarts.registerTheme("claude", {
  color: ["#D97757", "#5B7B8A", "#7C8C6B", "#C99A6B", "#9A7AA0", "#A0564B"],
  backgroundColor: "transparent",
  textStyle: { fontFamily: "Hanken Grotesk, Noto Sans TC, system-ui, sans-serif", color: "#1F1E1D" },
  title: { textStyle: { color: "#1F1E1D", fontFamily: "Fraunces, Noto Serif TC, serif" } },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#E8E3D9" } }, axisTick: { lineStyle: { color: "#E8E3D9" } },
    axisLabel: { color: "#6B6760" }, splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: "#6B6760" },
    splitLine: { lineStyle: { color: "#E8E3D9", type: "dashed" } },
  },
  legend: { textStyle: { color: "#6B6760" } },
  tooltip: {
    backgroundColor: "#FFFFFF", borderColor: "#E8E3D9",
    textStyle: { color: "#1F1E1D", fontFamily: "Hanken Grotesk, Noto Sans TC, sans-serif" },
  },
});

export const CLAUDE_THEME = "claude";
```

- [ ] **Step 2: 包裝元件** — `web/src/components/charts/EChart.tsx`

```tsx
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { CLAUDE_THEME } from "../../lib/echarts-theme";

interface Props {
  option: EChartsOption;
  height?: number;
  onEvents?: Record<string, (params: any) => void>;
}

export default function EChart({ option, height = 320, onEvents }: Props) {
  return (
    <ReactECharts
      option={option}
      theme={CLAUDE_THEME}
      notMerge
      lazyUpdate
      style={{ height, width: "100%" }}
      onEvents={onEvents}
    />
  );
}
```

- [ ] **Step 3: 型別檢查**

Run: `cd web && npx astro check`
Expected: 0 errors(若 `echarts-for-react` 無型別,於檔頂加 `// @ts-expect-error no types` 於 import 上方,或在 web/src/ 新增 `declarations.d.ts` 內容 `declare module "echarts-for-react";`,擇一,並回報採用哪種)。

- [ ] **Step 4: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/lib/echarts-theme.ts web/src/components/charts/EChart.tsx web/src/declarations.d.ts 2>/dev/null
git commit -m "feat(web): claude echarts theme + chart wrapper"
```

---

## Task 3:篩選器列 FilterBar

**Files:**
- Create: `web/src/components/explore/FilterBar.tsx`

- [ ] **Step 1: 實作** — `web/src/components/explore/FilterBar.tsx`

```tsx
import { useStore } from "@nanostores/react";
import { $filters, setFilter, EMPTY } from "../../lib/filter-store";
import type { Facets } from "../../lib/aggregate";
import type { RaceIndex } from "../../lib/types";

interface Props { facets: Facets; races: RaceIndex[]; }

function Select({ label, value, options, onChange }: {
  label: string; value: string; options: { v: string; t: string }[]; onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-muted">{label}</span>
      <select
        className="rounded-lg border border-border bg-surface px-3 py-2 text-ink"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">全部</option>
        {options.map((o) => <option key={o.v} value={o.v}>{o.t}</option>)}
      </select>
    </label>
  );
}

export default function FilterBar({ facets, races }: Props) {
  const f = useStore($filters);
  // race options follow the selected series (if any)
  const raceOpts = races
    .filter((r) => !f.series || r.s === f.series)
    .map((r) => ({ v: r.rk, t: `${r.y ?? ""} ${r.rn}`.trim() }));
  // de-dup race keys (a race spans years -> one option per rk)
  const seen = new Set<string>();
  const uniqRaceOpts = raceOpts.filter((o) => (seen.has(o.v) ? false : seen.add(o.v)));

  return (
    <div className="flex flex-wrap items-end gap-3">
      <Select label="年份" value={f.year != null ? String(f.year) : ""}
        options={facets.years.map((y) => ({ v: String(y), t: String(y) }))}
        onChange={(v) => setFilter("year", v ? Number(v) : null)} />
      <Select label="系列" value={f.series ?? ""}
        options={facets.series.map((s) => ({ v: s, t: s }))}
        onChange={(v) => { setFilter("series", v || null); setFilter("race", null); }} />
      <Select label="賽事" value={f.race ?? ""}
        options={uniqRaceOpts}
        onChange={(v) => setFilter("race", v || null)} />
      <Select label="組別類型" value={f.raceClass ?? ""}
        options={facets.raceClasses.map((c) => ({ v: c, t: c }))}
        onChange={(v) => setFilter("raceClass", v || null)} />
      <Select label="性別" value={f.gender ?? ""}
        options={[{ v: "M", t: "男" }, { v: "F", t: "女" }]}
        onChange={(v) => setFilter("gender", (v as "M" | "F") || null)} />
      <Select label="分齡組" value={f.ageGroup ?? ""}
        options={facets.ageGroups.map((a) => ({ v: a, t: a }))}
        onChange={(v) => setFilter("ageGroup", v || null)} />
      <button
        className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent"
        onClick={() => $filters.set({ ...EMPTY })}
      >清除</button>
    </div>
  );
}
```

- [ ] **Step 2: 型別檢查**

Run: `cd web && npx astro check`
Expected: 0 errors。

- [ ] **Step 3: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/explore/FilterBar.tsx
git commit -m "feat(web): explore filter bar bound to store"
```

---

## Task 4:完賽時間分布 + 分齡箱型圖

**Files:**
- Create: `web/src/components/charts/FinishTimeHistogram.tsx`, `web/src/components/charts/AgeBoxplot.tsx`

- [ ] **Step 1: 直方圖** — `web/src/components/charts/FinishTimeHistogram.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import { histogram } from "../../lib/aggregate";
import { secondsToHMS } from "../../lib/format";
import type { SlimRecord } from "../../lib/types";

const BIN = 600; // 10-minute buckets

export default function FinishTimeHistogram({ rows }: { rows: SlimRecord[] }) {
  const values = rows.map((r) => r.t).filter((t): t is number => t != null);
  const bins = histogram(values, BIN);
  const option: EChartsOption = {
    grid: { left: 48, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const b = bins[p[0].dataIndex];
        return `${secondsToHMS(b.x0)}–${secondsToHMS(b.x1)}<br/>${p[0].value} 人`;
      },
    },
    xAxis: {
      type: "category",
      data: bins.map((b) => secondsToHMS(b.x0)),
      axisLabel: { interval: Math.max(0, Math.floor(bins.length / 8)) },
    },
    yAxis: { type: "value", name: "人數" },
    series: [{ type: "bar", data: bins.map((b) => b.count), itemStyle: { color: "#D97757" }, barWidth: "90%" }],
  };
  if (!bins.length) return <Empty />;
  return <EChart option={option} />;
}

function Empty() {
  return <div className="flex h-[320px] items-center justify-center text-muted">此條件下無資料</div>;
}
```

- [ ] **Step 2: 箱型圖(點擊設 ageGroup)** — `web/src/components/charts/AgeBoxplot.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import { boxByGroup } from "../../lib/aggregate";
import { secondsToHMS } from "../../lib/format";
import { setFilter } from "../../lib/filter-store";
import type { SlimRecord } from "../../lib/types";

export default function AgeBoxplot({ rows }: { rows: SlimRecord[] }) {
  const boxes = boxByGroup(rows.map((r) => ({ ag: r.ag, t: r.t })), 8);
  if (!boxes.length) {
    return <div className="flex h-[320px] items-center justify-center text-muted">此條件下無分齡資料(僅競技型賽事有分齡組)</div>;
  }
  const option: EChartsOption = {
    grid: { left: 64, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "item",
      formatter: (p: any) => {
        const b = boxes[p.dataIndex];
        if (!b) return "";
        return `${b.group}(${b.n} 人)<br/>中位 ${secondsToHMS(b.median)}<br/>Q1 ${secondsToHMS(b.q1)} / Q3 ${secondsToHMS(b.q3)}`;
      },
    },
    xAxis: { type: "category", data: boxes.map((b) => b.group), axisLabel: { rotate: 45 } },
    yAxis: { type: "value", name: "完賽時間", axisLabel: { formatter: (v: number) => secondsToHMS(v) } },
    series: [{
      type: "boxplot",
      data: boxes.map((b) => [b.min, b.q1, b.median, b.q3, b.max]),
      itemStyle: { color: "#FBEFE9", borderColor: "#D97757" },
    }],
  };
  const onEvents = {
    click: (p: any) => { const b = boxes[p.dataIndex]; if (b) setFilter("ageGroup", b.group); },
  };
  return <EChart option={option} onEvents={onEvents} />;
}
```

- [ ] **Step 3: 型別檢查**

Run: `cd web && npx astro check`
Expected: 0 errors。

- [ ] **Step 4: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/charts/FinishTimeHistogram.tsx web/src/components/charts/AgeBoxplot.tsx
git commit -m "feat(web): finish-time histogram + age boxplot charts"
```

---

## Task 5:競爭強度離散度 + 距離vs均速散點

**Files:**
- Create: `web/src/components/charts/CompetitivenessSpread.tsx`, `web/src/components/charts/DistanceSpeedScatter.tsx`

- [ ] **Step 1: 競爭強度(點擊設 race)** — `web/src/components/charts/CompetitivenessSpread.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import { raceSpread } from "../../lib/aggregate";
import { setFilter } from "../../lib/filter-store";
import type { SlimRecord, RaceIndex } from "../../lib/types";

export default function CompetitivenessSpread(
  { rows, nameMap }: { rows: SlimRecord[]; nameMap: Map<string, string> },
) {
  const spreads = raceSpread(rows.map((r) => ({ rk: r.rk, y: r.y, t: r.t, rc: r.rc })), 10).slice(0, 15);
  if (!spreads.length) return <div className="flex h-[360px] items-center justify-center text-muted">此條件下無足夠資料</div>;
  const labels = spreads.map((s) => `${nameMap.get(s.rk) ?? s.rk} ${s.y ?? ""}`.trim());
  const option: EChartsOption = {
    grid: { left: 200, right: 24, top: 24, bottom: 40 },
    tooltip: {
      trigger: "item",
      formatter: (p: any) => {
        const s = spreads[p.dataIndex];
        return `${labels[p.dataIndex]}<br/>離散倍數 ${s.ratio.toFixed(2)}×(中位/冠軍)<br/>${s.n} 人`;
      },
    },
    xAxis: { type: "value", name: "中位/冠軍 倍數" },
    yAxis: { type: "category", data: labels, inverse: true, axisLabel: { width: 190, overflow: "truncate" } },
    series: [{ type: "bar", data: spreads.map((s) => Number(s.ratio.toFixed(2))), itemStyle: { color: "#5B7B8A" }, barWidth: "70%" }],
  };
  const onEvents = { click: (p: any) => { const s = spreads[p.dataIndex]; if (s) setFilter("race", s.rk); } };
  return <EChart option={option} height={360} onEvents={onEvents} />;
}
```

- [ ] **Step 2: 距離vs均速散點** — `web/src/components/charts/DistanceSpeedScatter.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import { distSpeedPoints } from "../../lib/aggregate";
import type { SlimRecord } from "../../lib/types";

export default function DistanceSpeedScatter({ rows }: { rows: SlimRecord[] }) {
  const pts = distSpeedPoints(rows.map((r) => ({ dist: r.dist, spd: r.spd, rc: r.rc })));
  if (!pts.length) {
    return <div className="flex h-[320px] items-center justify-center text-muted">此條件下無距離/速度資料(約涵蓋 48% 賽事)</div>;
  }
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 24, bottom: 44 },
    tooltip: { trigger: "item", formatter: (p: any) => `${p.value[0]} km · ${p.value[1]} km/h` },
    xAxis: { type: "value", name: "距離 (km)", nameLocation: "middle", nameGap: 28 },
    yAxis: { type: "value", name: "平均速度 (km/h)" },
    series: [{
      type: "scatter", symbolSize: 6,
      data: pts.map((p) => [p.dist, p.spd]),
      itemStyle: { color: "rgba(217,119,87,0.5)" },
    }],
  };
  return <EChart option={option} />;
}
```

- [ ] **Step 3: 型別檢查**

Run: `cd web && npx astro check`
Expected: 0 errors。

- [ ] **Step 4: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/charts/CompetitivenessSpread.tsx web/src/components/charts/DistanceSpeedScatter.tsx
git commit -m "feat(web): competitiveness spread + distance-speed scatter charts"
```

---

## Task 6:ExploreApp orchestrator

**Files:**
- Create: `web/src/components/explore/ExploreApp.tsx`

- [ ] **Step 1: 實作** — `web/src/components/explore/ExploreApp.tsx`

```tsx
import { useEffect, useMemo, useState } from "react";
import { useStore } from "@nanostores/react";
import "../../lib/echarts-theme";
import { loadViz, loadRaces } from "../../lib/data-load";
import { $filters, applyFilters, hydrateFromUrl } from "../../lib/filter-store";
import { facetOptions } from "../../lib/aggregate";
import type { SlimRecord, RaceIndex } from "../../lib/types";
import FilterBar from "./FilterBar";
import FinishTimeHistogram from "../charts/FinishTimeHistogram";
import AgeBoxplot from "../charts/AgeBoxplot";
import CompetitivenessSpread from "../charts/CompetitivenessSpread";
import DistanceSpeedScatter from "../charts/DistanceSpeedScatter";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

export default function ExploreApp() {
  const [viz, setViz] = useState<SlimRecord[] | null>(null);
  const [races, setRaces] = useState<RaceIndex[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const f = useStore($filters);

  useEffect(() => {
    hydrateFromUrl();
    Promise.all([loadViz(), loadRaces()])
      .then(([v, r]) => { setViz(v); setRaces(r); })
      .catch((e) => setErr(String(e)));
  }, []);

  const facets = useMemo(() => (viz ? facetOptions(viz) : null), [viz]);
  const filtered = useMemo(() => (viz ? applyFilters(viz, f) : []), [viz, f]);
  const nameMap = useMemo(() => new Map(races.map((r) => [r.rk, r.rn])), [races]);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!viz || !facets) return <p className="text-muted">載入中…</p>;

  return (
    <div className="space-y-6">
      <FilterBar facets={facets} races={races} />
      <p className="text-sm text-muted">
        符合條件:<span className="num text-ink">{filtered.length.toLocaleString()}</span> 筆
      </p>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="完賽時間分布" hint="每 10 分鐘一桶"><FinishTimeHistogram rows={filtered} /></Card>
        <Card title="分齡組 vs 完賽時間" hint="點組別可篩選 · 僅競技型賽事有分齡"><AgeBoxplot rows={filtered} /></Card>
        <Card title="賽事競爭強度(中位/冠軍 倍數)" hint="點賽事可篩選 · 已排除認證型"><CompetitivenessSpread rows={filtered} nameMap={nameMap} /></Card>
        <Card title="距離 vs 平均速度" hint="距離可解析者約 48%"><DistanceSpeedScatter rows={filtered} /></Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 型別檢查**

Run: `cd web && npx astro check`
Expected: 0 errors。

- [ ] **Step 3: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/explore/ExploreApp.tsx
git commit -m "feat(web): explore app orchestrator (load, filter, linked charts)"
```

---

## Task 7:/explore 頁 + 端到端驗證

**Files:**
- Create: `web/src/pages/explore.astro`

- [ ] **Step 1: 頁面** — `web/src/pages/explore.astro`

```astro
---
import Base from "../layouts/Base.astro";
import ExploreApp from "../components/explore/ExploreApp.tsx";
---
<Base title="探索 | 台灣公路車賽事成績儀表板">
  <h1 class="font-display text-3xl">探索</h1>
  <p class="mt-2 mb-6 text-muted">篩選年份、系列、賽事、組別、性別、分齡組,即時觀察成績分布與賽事特性。</p>
  <ExploreApp client:only="react" />
</Base>
```

- [ ] **Step 2: build 驗證(靜態產出成功)**

Run: `cd web && npm run build`
Expected: 成功;`web/dist/explore/index.html` 產出(client:only island 由瀏覽器水合)。

- [ ] **Step 3: 型別檢查 + 測試**

Run: `cd web && npx astro check && npm test`
Expected: astro check 0 errors;vitest 全綠(format + aggregate)。

- [ ] **Step 4: 端到端瀏覽器驗證(控制端執行)**

啟動 `cd web && npm run preview`(背景),用瀏覽器開 `http://localhost:4321/explore`:
- 確認 4 張圖都繪出(直方圖、箱型、橫條離散度、散點)。
- 操作「系列」選 96聯賽 → 圖即時更新;「符合條件 N 筆」數字改變。
- 點箱型圖某組別 → 分齡組篩選器跟著設定、其他圖連動;URL 出現 `?ageGroup=...`。
- 點離散度某賽事 → 賽事被選取。
驗證後關閉 preview。

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/pages/explore.astro
git commit -m "feat(web): explore page wired with filters + linked charts"
```

---

## 完成標準(Plan 2)

- `npm test` 全綠(format + aggregate);`npm run build` 與 `npx astro check` 通過。
- `/explore` 顯示 4 張 Claude 風格 ECharts 圖,套用全域篩選即時重算。
- 點箱型圖組別、點離散度賽事可交叉篩選,URL 同步。
- 低涵蓋條件(無分齡/無距離)顯示友善空狀態而非空白。

---

## Self-Review(對照 spec 頁 B)

- 完賽時間分布(核心1)→ Task 4 FinishTimeHistogram ✓
- 分齡組 vs 完賽時間 箱型(核心2)→ Task 4 AgeBoxplot ✓(標註涵蓋)
- 競爭強度/離散度(C7)→ Task 5 CompetitivenessSpread ✓(排除認證,點擊設 race)
- 距離 vs 均速(C11)→ Task 5 DistanceSpeedScatter ✓(標註 48%)
- 全域篩選 + 聯動 → Task 3 FilterBar(綁 $filters)+ Task 6 ExploreApp(applyFilters、URL hydrate)+ 圖點擊 setFilter ✓
- Placeholder 掃描:每步皆含完整程式;無 TBD。
- 型別一致:`SlimRecord` 短鍵(t/ag/rk/y/rc/dist/spd/s/g)在 aggregate 函式、圖元件、filter-store 一致;`Facets`/`Box`/`Spread`/`Bin`/`ScatterPt` 由 aggregate 匯出並於元件使用;`secondsToHMS` 來自既有 format.ts。
- 沿用既有檔(data-load/filter-store/format/types/tokens),無重複造輪子(DRY)。
- 風險:`client:only="react"` 避免 ECharts SSR;echarts-for-react 若缺型別以 declarations.d.ts 處理(Task 2 Step 3)。
