# 公路車儀表板 — Plan 3:總覽頁(KPI + 頭條圖)實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把首頁 `/` 從占位骨架升級為真正的總覽頁:動態 KPI(取代寫死的 47/20)+ 賽季行事曆熱力圖 + 逐年參賽趨勢(堆疊系列)+ 女子參與度 + 組別/性別組成。

**Architecture:** 首頁掛 `client:only="react"` 的 `OverviewApp` island,載入一次 `viz.json`,以純函式(`overview.ts`,TDD)算出 KPI 與 4 張圖的資料,丟給圖元件(沿用 Plan 2 的 `EChart` 包裝與 Claude 主題)。總覽頁不含全域篩選(它是頭條頁),用完整資料集。`DataSmoke.tsx`(Plan 1 煙霧測試元件)由 `OverviewApp` 取代並刪除。

**Tech Stack:** Astro 6 · React 19 islands(client:only)· ECharts 6 + echarts-for-react · TypeScript · Vitest。沿用 `web/src/lib/{types,data-load,format,echarts-theme}.ts` 與 `components/charts/EChart.tsx`、Claude tokens。

設計依據:`docs/superpowers/specs/2026-06-04-cycling-dashboard-design.md` 頁 A。

---

## 檔案結構(本 plan 建立/修改)

```
web/src/
  lib/
    overview.ts        純函式:kpiStats / monthYearHeat / trendByYearSeries / womenShareBySeries / compositionByClass
    overview.test.ts   Vitest
  components/
    overview/
      KpiCards.tsx           4 張動態 KPI 卡
      SeasonHeatmap.tsx      月份×年 人次熱力圖
      ParticipationTrend.tsx 逐年×系列 堆疊長條
      WomenParticipation.tsx 各系列女子佔比 橫條
      CompositionByClass.tsx 組別×性別 堆疊長條
      OverviewApp.tsx        orchestrator(載資料、算聚合、版面)
  pages/
    index.astro        改用 OverviewApp(移除 DataSmoke 與寫死卡片)
  components/DataSmoke.tsx   刪除(由 OverviewApp 取代)
```

---

## Task 1:總覽聚合純函式(TDD)

**Files:**
- Create: `web/src/lib/overview.ts`, `web/src/lib/overview.test.ts`

- [ ] **Step 1: 寫失敗測試** — `web/src/lib/overview.test.ts`

```ts
import { describe, it, expect } from "vitest";
import { kpiStats, monthYearHeat, trendByYearSeries, womenShareBySeries, compositionByClass } from "./overview";
import type { SlimRecord } from "./types";

function rec(p: Partial<SlimRecord>): SlimRecord {
  return { rk: "r", y: 2025, mon: 1, s: "S", rc: "競賽", cat: null, g: null, ag: null,
    t: 1000, rank: 1, dist: null, spd: null, plat: "x", reg: null, ...p };
}

describe("kpiStats", () => {
  it("counts records, distinct races (rk), series, year range", () => {
    const k = kpiStats([
      rec({ rk: "a", s: "S1", y: 2024 }), rec({ rk: "a", s: "S1", y: 2025 }),
      rec({ rk: "b", s: "S2", y: 2025 }),
    ]);
    expect(k.records).toBe(3);
    expect(k.races).toBe(2);   // distinct rk = a,b
    expect(k.series).toBe(2);
    expect(k.minYear).toBe(2024);
    expect(k.maxYear).toBe(2025);
  });
});

describe("monthYearHeat", () => {
  it("counts 人次 per (month, year) and exposes years + max", () => {
    const h = monthYearHeat([
      rec({ mon: 9, y: 2025 }), rec({ mon: 9, y: 2025 }), rec({ mon: 3, y: 2024 }),
    ]);
    expect(h.years).toEqual([2024, 2025]);
    expect(h.max).toBe(2);
    // cell = [monthIndex(0-11), yearIndex, count]
    expect(h.cells).toContainEqual([8, 1, 2]); // Sep 2025 -> 2
    expect(h.cells).toContainEqual([2, 0, 1]); // Mar 2024 -> 1
  });
});

describe("trendByYearSeries", () => {
  it("stacks counts per year by top series", () => {
    const t = trendByYearSeries([
      rec({ y: 2024, s: "A" }), rec({ y: 2025, s: "A" }), rec({ y: 2025, s: "B" }),
    ], 8);
    expect(t.years).toEqual([2024, 2025]);
    expect(t.series.sort()).toEqual(["A", "B"]);
    expect(t.counts["A"]).toEqual([1, 1]);
    expect(t.counts["B"]).toEqual([0, 1]);
  });
});

describe("womenShareBySeries", () => {
  it("female share per series above minN, sorted by total desc", () => {
    const rows = [
      ...Array.from({ length: 3 }, () => rec({ s: "X", g: "F" })),
      ...Array.from({ length: 7 }, () => rec({ s: "X", g: "M" })),
      rec({ s: "Y", g: "F" }), // total 1 -> dropped at minN=2
    ];
    const w = womenShareBySeries(rows, 2);
    expect(w.length).toBe(1);
    expect(w[0].series).toBe("X");
    expect(w[0].f).toBe(3);
    expect(w[0].total).toBe(10);
    expect(w[0].pct).toBe(30);
  });
});

describe("compositionByClass", () => {
  it("counts M/F/unknown per race_class, sorted by total desc", () => {
    const c = compositionByClass([
      rec({ rc: "競賽", g: "M" }), rec({ rc: "競賽", g: "F" }), rec({ rc: "挑戰", g: null }),
    ]);
    expect(c.classes[0]).toBe("競賽"); // 2 > 1
    expect(c.male[0]).toBe(1);
    expect(c.female[0]).toBe(1);
    expect(c.unknown[c.classes.indexOf("挑戰")]).toBe(1);
  });
});
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd web && npm test`
Expected: FAIL(找不到 `./overview` 匯出)

- [ ] **Step 3: 實作** — `web/src/lib/overview.ts`

```ts
import type { SlimRecord } from "./types";

export interface Kpi { records: number; races: number; series: number; minYear: number | null; maxYear: number | null; }
export function kpiStats(rows: SlimRecord[]): Kpi {
  const races = new Set<string>(), series = new Set<string>();
  let mn = Infinity, mx = -Infinity;
  for (const r of rows) {
    if (r.rk) races.add(r.rk);
    if (r.s) series.add(r.s);
    if (r.y != null) { mn = Math.min(mn, r.y); mx = Math.max(mx, r.y); }
  }
  return {
    records: rows.length, races: races.size, series: series.size,
    minYear: mn === Infinity ? null : mn, maxYear: mx === -Infinity ? null : mx,
  };
}

export interface Heat { years: number[]; cells: [number, number, number][]; max: number; }
export function monthYearHeat(rows: SlimRecord[]): Heat {
  const years = [...new Set(rows.filter((r) => r.y != null).map((r) => r.y as number))].sort((a, b) => a - b);
  const yi = new Map(years.map((y, i) => [y, i]));
  const grid = new Map<string, number>();
  for (const r of rows) {
    if (r.mon == null || r.y == null) continue;
    const k = `${r.mon}-${r.y}`;
    grid.set(k, (grid.get(k) || 0) + 1);
  }
  const cells: [number, number, number][] = [];
  let max = 0;
  for (const [k, c] of grid) {
    const [m, y] = k.split("-").map(Number);
    cells.push([m - 1, yi.get(y)!, c]);
    max = Math.max(max, c);
  }
  return { years, cells, max };
}

export interface Trend { years: number[]; series: string[]; counts: Record<string, number[]>; }
export function trendByYearSeries(rows: SlimRecord[], topN = 8): Trend {
  const years = [...new Set(rows.filter((r) => r.y != null).map((r) => r.y as number))].sort((a, b) => a - b);
  const yi = new Map(years.map((y, i) => [y, i]));
  const totals = new Map<string, number>();
  for (const r of rows) { const s = r.s || "其他"; totals.set(s, (totals.get(s) || 0) + 1); }
  const top = [...totals.entries()].sort((a, b) => b[1] - a[1]).slice(0, topN).map((e) => e[0]);
  const topSet = new Set(top);
  const counts: Record<string, number[]> = {};
  for (const s of [...top, "其他"]) counts[s] = years.map(() => 0);
  for (const r of rows) {
    if (r.y == null) continue;
    const s = r.s || "其他";
    const key = topSet.has(s) ? s : "其他";
    counts[key][yi.get(r.y)!]++;
  }
  if (counts["其他"].every((c) => c === 0)) delete counts["其他"];
  return { years, series: Object.keys(counts), counts };
}

export interface WomenShare { series: string; f: number; total: number; pct: number; }
export function womenShareBySeries(rows: SlimRecord[], minN = 50): WomenShare[] {
  const g = new Map<string, { f: number; t: number }>();
  for (const r of rows) {
    if (r.g !== "M" && r.g !== "F") continue;
    const s = r.s || "其他";
    const e = g.get(s) || { f: 0, t: 0 };
    if (r.g === "F") e.f++;
    e.t++;
    g.set(s, e);
  }
  return [...g.entries()]
    .filter(([, e]) => e.t >= minN)
    .map(([s, e]) => ({ series: s, f: e.f, total: e.t, pct: Math.round((100 * e.f) / e.t) }))
    .sort((a, b) => b.total - a.total);
}

export interface Composition { classes: string[]; male: number[]; female: number[]; unknown: number[]; }
export function compositionByClass(rows: SlimRecord[]): Composition {
  const g = new Map<string, { m: number; f: number; u: number }>();
  for (const r of rows) {
    const c = r.rc || "未分類";
    const e = g.get(c) || { m: 0, f: 0, u: 0 };
    if (r.g === "M") e.m++;
    else if (r.g === "F") e.f++;
    else e.u++;
    g.set(c, e);
  }
  const total = (c: string) => { const e = g.get(c)!; return e.m + e.f + e.u; };
  const classes = [...g.keys()].sort((a, b) => total(b) - total(a));
  return {
    classes,
    male: classes.map((c) => g.get(c)!.m),
    female: classes.map((c) => g.get(c)!.f),
    unknown: classes.map((c) => g.get(c)!.u),
  };
}
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd web && npm test`
Expected: PASS(format + aggregate + overview 全綠)

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/lib/overview.ts web/src/lib/overview.test.ts
git commit -m "feat(web): overview-page aggregation functions (tested)"
```

---

## Task 2:KPI 卡 + 賽季熱力圖

**Files:**
- Create: `web/src/components/overview/KpiCards.tsx`, `web/src/components/overview/SeasonHeatmap.tsx`

- [ ] **Step 1: KPI 卡** — `web/src/components/overview/KpiCards.tsx`

```tsx
import type { Kpi } from "../../lib/overview";

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="text-sm text-muted">{label}</div>
      <div className="num text-3xl text-ink">{value}</div>
    </div>
  );
}

export default function KpiCards({ kpi }: { kpi: Kpi }) {
  const years = kpi.minYear != null && kpi.maxYear != null
    ? (kpi.minYear === kpi.maxYear ? String(kpi.minYear) : `${kpi.minYear}–${String(kpi.maxYear).slice(2)}`)
    : "—";
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <Card label="成績筆數" value={kpi.records.toLocaleString()} />
      <Card label="賽事" value={String(kpi.races)} />
      <Card label="系列" value={String(kpi.series)} />
      <Card label="年份" value={years} />
    </div>
  );
}
```

- [ ] **Step 2: 賽季熱力圖** — `web/src/components/overview/SeasonHeatmap.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { monthYearHeat } from "../../lib/overview";
import type { SlimRecord } from "../../lib/types";

const MONTHS = Array.from({ length: 12 }, (_, i) => `${i + 1}月`);

export default function SeasonHeatmap({ rows }: { rows: SlimRecord[] }) {
  const heat = monthYearHeat(rows);
  if (!heat.cells.length) return <div className="flex h-[260px] items-center justify-center text-muted">無資料</div>;
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 16, bottom: 64 },
    tooltip: {
      position: "top",
      formatter: (p: any) => `${MONTHS[p.value[0]]} ${heat.years[p.value[1]]}<br/>${p.value[2].toLocaleString()} 人次`,
    },
    xAxis: { type: "category", data: MONTHS, splitArea: { show: true } },
    yAxis: { type: "category", data: heat.years.map(String), splitArea: { show: true } },
    visualMap: {
      min: 0, max: heat.max, calculable: true, orient: "horizontal", left: "center", bottom: 8,
      inRange: { color: ["#FAF1EC", "#E7A98C", "#D97757", "#A0564B"] }, textStyle: { color: "#6B6760" },
    },
    series: [{ type: "heatmap", data: heat.cells, label: { show: false },
      emphasis: { itemStyle: { borderColor: "#1F1E1D", borderWidth: 1 } } }],
  };
  return <EChart option={option} height={260} />;
}
```

- [ ] **Step 3: 型別檢查**

Run: `cd web && npx astro check`
Expected: 0 errors。

- [ ] **Step 4: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/overview/KpiCards.tsx web/src/components/overview/SeasonHeatmap.tsx
git commit -m "feat(web): dynamic KPI cards + season heatmap"
```

---

## Task 3:參賽趨勢 + 女子參與度 + 組別/性別組成

**Files:**
- Create: `web/src/components/overview/ParticipationTrend.tsx`, `web/src/components/overview/WomenParticipation.tsx`, `web/src/components/overview/CompositionByClass.tsx`

- [ ] **Step 1: 參賽趨勢** — `web/src/components/overview/ParticipationTrend.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { trendByYearSeries } from "../../lib/overview";
import type { SlimRecord } from "../../lib/types";

export default function ParticipationTrend({ rows }: { rows: SlimRecord[] }) {
  const t = trendByYearSeries(rows, 8);
  if (!t.years.length) return <div className="flex h-[300px] items-center justify-center text-muted">無資料</div>;
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 16, bottom: 64 },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { type: "scroll", bottom: 0, textStyle: { color: "#6B6760" } },
    xAxis: { type: "category", data: t.years.map(String) },
    yAxis: { type: "value", name: "人次" },
    series: t.series.map((s) => ({ name: s, type: "bar", stack: "total", data: t.counts[s] })),
  };
  return <EChart option={option} height={300} />;
}
```

- [ ] **Step 2: 女子參與度** — `web/src/components/overview/WomenParticipation.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { womenShareBySeries } from "../../lib/overview";
import type { SlimRecord } from "../../lib/types";

export default function WomenParticipation({ rows }: { rows: SlimRecord[] }) {
  const shares = womenShareBySeries(rows, 50).slice(0, 12);
  if (!shares.length) return <div className="flex h-[320px] items-center justify-center text-muted">無足夠性別資料</div>;
  const option: EChartsOption = {
    grid: { left: 170, right: 32, top: 16, bottom: 32 },
    tooltip: {
      trigger: "item",
      formatter: (p: any) => { const w = shares[p.dataIndex]; return `${w.series}<br/>女子 ${w.f}/${w.total}(${w.pct}%)`; },
    },
    xAxis: { type: "value", name: "女子 %" },
    yAxis: { type: "category", inverse: true, data: shares.map((w) => w.series),
      axisLabel: { width: 160, overflow: "truncate" } },
    series: [{ type: "bar", data: shares.map((w) => w.pct), itemStyle: { color: "#9A7AA0" }, barWidth: "70%",
      label: { show: true, position: "right", formatter: "{c}%", color: "#6B6760" } }],
  };
  return <EChart option={option} height={320} />;
}
```

- [ ] **Step 3: 組別/性別組成** — `web/src/components/overview/CompositionByClass.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { compositionByClass } from "../../lib/overview";
import type { SlimRecord } from "../../lib/types";

export default function CompositionByClass({ rows }: { rows: SlimRecord[] }) {
  const c = compositionByClass(rows);
  if (!c.classes.length) return <div className="flex h-[300px] items-center justify-center text-muted">無資料</div>;
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 16, bottom: 64 },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { bottom: 0, textStyle: { color: "#6B6760" } },
    xAxis: { type: "category", data: c.classes, axisLabel: { rotate: 30 } },
    yAxis: { type: "value", name: "人次" },
    series: [
      { name: "男", type: "bar", stack: "g", data: c.male, itemStyle: { color: "#5B7B8A" } },
      { name: "女", type: "bar", stack: "g", data: c.female, itemStyle: { color: "#D97757" } },
      { name: "未標示", type: "bar", stack: "g", data: c.unknown, itemStyle: { color: "#C9C2B5" } },
    ],
  };
  return <EChart option={option} height={300} />;
}
```

- [ ] **Step 4: 型別檢查**

Run: `cd web && npx astro check`
Expected: 0 errors。

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/overview/ParticipationTrend.tsx web/src/components/overview/WomenParticipation.tsx web/src/components/overview/CompositionByClass.tsx
git commit -m "feat(web): participation trend, women share, class composition charts"
```

---

## Task 4:OverviewApp + 改寫首頁 + 端到端驗證

**Files:**
- Create: `web/src/components/overview/OverviewApp.tsx`
- Modify: `web/src/pages/index.astro`
- Delete: `web/src/components/DataSmoke.tsx`

- [ ] **Step 1: OverviewApp** — `web/src/components/overview/OverviewApp.tsx`

```tsx
import { useEffect, useMemo, useState } from "react";
import "../../lib/echarts-theme";
import { loadViz } from "../../lib/data-load";
import { kpiStats } from "../../lib/overview";
import type { SlimRecord } from "../../lib/types";
import KpiCards from "./KpiCards";
import SeasonHeatmap from "./SeasonHeatmap";
import ParticipationTrend from "./ParticipationTrend";
import WomenParticipation from "./WomenParticipation";
import CompositionByClass from "./CompositionByClass";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

export default function OverviewApp() {
  const [viz, setViz] = useState<SlimRecord[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadViz().then(setViz).catch((e) => setErr(String(e)));
  }, []);

  const kpi = useMemo(() => (viz ? kpiStats(viz) : null), [viz]);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!viz || !kpi) return <p className="text-muted">載入中…</p>;

  return (
    <div className="space-y-6">
      <KpiCards kpi={kpi} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="賽季行事曆" hint="各月份人次(date 100% 完整)"><SeasonHeatmap rows={viz} /></Card>
        <Card title="逐年參賽趨勢" hint="依系列堆疊(前 8 大)"><ParticipationTrend rows={viz} /></Card>
        <Card title="女子參與度" hint="各系列女子佔比 · 樣本≥50"><WomenParticipation rows={viz} /></Card>
        <Card title="組別 / 性別組成" hint="「未標示」多為市民賽不分組"><CompositionByClass rows={viz} /></Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 改寫首頁** — 覆寫 `web/src/pages/index.astro`

```astro
---
import Base from "../layouts/Base.astro";
import OverviewApp from "../components/overview/OverviewApp.tsx";
---
<Base>
  <h1 class="font-display text-3xl">總覽</h1>
  <p class="mt-2 mb-6 text-muted">台灣公路車賽事成績資料探索 · 2024–2026</p>
  <OverviewApp client:only="react" />
</Base>
```

- [ ] **Step 3: 刪除已被取代的煙霧測試元件**

Run:
```bash
cd C:/Users/user/Desktop/tw-cycling-data
git rm web/src/components/DataSmoke.tsx
```

- [ ] **Step 4: build + 型別 + 測試**

Run:
```bash
cd web && npm run build && npx astro check && npm test
```
Expected: build 成功(首頁 `dist/index.html` 產出);astro check 0 errors;vitest 全綠(format + aggregate + overview)。確認沒有殘留 import 指向已刪除的 DataSmoke。

- [ ] **Step 5: 端到端瀏覽器驗證(控制端執行)**

啟 `cd web && npm run preview`(背景),開 `http://localhost:4321/`:
- KPI 顯示動態值:成績筆數 33,051、賽事 47、系列 20、年份 2024–26(不再是寫死)。
- 4 張圖繪出:熱力圖(9/11 月較深)、逐年堆疊趨勢、女子佔比(L'Étape 最高約 24%)、組別/性別堆疊。
驗證後關閉 preview。

- [ ] **Step 6: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/overview/OverviewApp.tsx web/src/pages/index.astro
git commit -m "feat(web): overview page (dynamic KPI + 4 headline charts), retire DataSmoke"
```

---

## 完成標準(Plan 3)

- `npm test` 全綠(format + aggregate + overview);`npm run build` 與 `npx astro check` 通過。
- 首頁 KPI 為**動態**(由 viz.json 算出,修掉寫死的 47/20)。
- 4 張頭條圖(賽季熱力、參賽趨勢、女子參與度、組別/性別組成)正確繪出。
- `DataSmoke.tsx` 已移除且無殘留引用。

---

## Self-Review(對照 spec 頁 A)

- 動態 KPI(成績/賽事/系列/年份)→ Task 1 kpiStats + Task 2 KpiCards ✓(修掉 index.astro 寫死值)
- C9 賽季行事曆熱力圖 → Task 1 monthYearHeat + Task 2 SeasonHeatmap ✓(date 100%)
- 參賽人數趨勢(核心3)→ Task 1 trendByYearSeries + Task 3 ParticipationTrend ✓
- C10 女子參與度 → Task 1 womenShareBySeries + Task 3 WomenParticipation ✓
- 組別/性別組成(核心4)→ Task 1 compositionByClass + Task 3 CompositionByClass ✓
- Placeholder 掃描:每步含完整程式;無 TBD。
- 型別一致:`SlimRecord` 短鍵(rk/y/mon/s/rc/g)於 overview 函式與圖元件一致;`Kpi/Heat/Trend/WomenShare/Composition` 由 overview.ts 匯出並於元件使用;沿用既有 EChart/data-load/echarts-theme。
- DRY:沿用 Plan 1/2 既有元件與工具,未重複造輪;`DataSmoke` 移除避免死碼。
- 範圍:總覽頁不含全域篩選(頭條頁,完整資料);篩選互動屬探索頁(Plan 2)。
