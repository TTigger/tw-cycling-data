# Phase 2b-3:/trends 分齡組成 Joy Plot 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 /trends 的分齡組成從 100% 堆疊面積圖改成單色 joy plot 稜線圖(每年齡帶一條 lane,峰高=占比)。

**Architecture:** 純函式 `joyRidges(pct, laneGap, peak)` 算各 lane 的基線與縮放值(可 vitest);`AgeCompositionTrend` 改用 stacked-pair 技巧(隱形基線 + 堆疊稜線,本 repo `FinishTimeBand` 已驗證)逐 band 畫 lane,單一 accent 色 + 右端 band 名 endLabel,tooltip 讀原始 `at.pct` 顯示真實 %。

**Tech Stack:** Astro + React islands + ECharts + vitest。

## Global Constraints

- **單一 accent 色**(松綠):線 2px、填 opacity 0.18;識別由 lane 位置 + 右端 band 名直接標籤承載(標籤 `colors.muted`,不用 series 色)。
- **joyRidges**:第一個 band 在最上 lane(`base(bi) = (nBands-1-bi) * laneGap`);全域最大 pct 縮放到 `peak * laneGap`(預設 `laneGap=1, peak=1.6`);maxPct=0 不除零(全 0);空輸入 `[]`。
- **tooltip 一律顯示原始 `at.pct` 百分比**(非合成偏移);隱形基線 series `tooltip:{show:false}` + `silent:true`。
- y 軸隱藏;x=年份 category;顏色由 `useChartColors()` 於 render body 取用(翻色)。
- 只動 `web/src/lib/joyplot.ts`(新)、`web/src/lib/joyplot.test.ts`(新)、`web/src/components/trends/AgeCompositionTrend.tsx`;不動資料/loadOverview//trends 其他區塊。
- build 成功;既有 vitest 綠。

## 執行順序
Task 1(joyRidges + vitest)→ Task 2(元件改寫)→ controller 收尾。

---

## Task 1: `joyRidges` 純函式

**Files:** Create `web/src/lib/joyplot.ts`, `web/src/lib/joyplot.test.ts`

**Interfaces:** Produces
```ts
export interface JoyLane { base: number; scaled: number[]; }
export function joyRidges(pct: number[][], laneGap = 1, peak = 1.6): JoyLane[];
```

- [ ] **Step 1: 寫失敗測試 `web/src/lib/joyplot.test.ts`**

```ts
import { describe, it, expect } from "vitest";
import { joyRidges } from "./joyplot";

describe("joyRidges", () => {
  it("first band gets the TOP lane (highest base); bases descend by laneGap", () => {
    const lanes = joyRidges([[10], [20], [30]], 1, 1.6);
    expect(lanes.map((l) => l.base)).toEqual([2, 1, 0]);
  });
  it("scales the global max pct to peak * laneGap", () => {
    const lanes = joyRidges([[10, 40], [20, 5]], 1, 1.6);
    // global max = 40 -> 1.6; others proportional
    expect(lanes[0].scaled[1]).toBeCloseTo(1.6);
    expect(lanes[0].scaled[0]).toBeCloseTo(0.4);
    expect(lanes[1].scaled[0]).toBeCloseTo(0.8);
  });
  it("all-zero pct does not divide by zero (scaled stays 0)", () => {
    const lanes = joyRidges([[0, 0]], 1, 1.6);
    expect(lanes[0].scaled).toEqual([0, 0]);
  });
  it("empty input -> []", () => {
    expect(joyRidges([], 1, 1.6)).toEqual([]);
  });
});
```

- [ ] **Step 2: 跑測試(RED)**

Run: `cd web && npx vitest run src/lib/joyplot.test.ts`
Expected: FAIL(module 不存在)。

- [ ] **Step 3: 實作 `web/src/lib/joyplot.ts`**

```ts
export interface JoyLane { base: number; scaled: number[]; }

/** Joy-plot geometry: one lane per band, first band on TOP. The global max pct
 * scales to peak * laneGap so tall peaks slightly overlap the lane above. */
export function joyRidges(pct: number[][], laneGap = 1, peak = 1.6): JoyLane[] {
  const n = pct.length;
  if (!n) return [];
  const maxPct = Math.max(...pct.flat(), 0);
  const scale = maxPct > 0 ? (peak * laneGap) / maxPct : 0;
  return pct.map((row, bi) => ({
    base: (n - 1 - bi) * laneGap,
    scaled: row.map((v) => v * scale),
  }));
}
```

- [ ] **Step 4: 跑測試(GREEN)**

Run: `cd web && npx vitest run src/lib/joyplot.test.ts`
Expected: PASS(4 tests)。

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/joyplot.ts web/src/lib/joyplot.test.ts
git commit -m "feat(ridge): joyRidges lane geometry for the age joy plot"
```

---

## Task 2: `AgeCompositionTrend` 改寫為 joy plot

**Files:** Modify `web/src/components/trends/AgeCompositionTrend.tsx`(整檔改寫)

**Interfaces:** Consumes `joyRidges`/`JoyLane`(Task 1)、`useChartColors`、`AgeTrend { years, bands, pct }`、`EChart`/`ChartEmpty`。Props 不變(`{ at: AgeTrend }`)——`TrendsApp` 呼叫端零改動。

- [ ] **Step 1: 整檔改寫 `AgeCompositionTrend.tsx`**

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import type { AgeTrend } from "../../lib/overview";
import { joyRidges } from "../../lib/joyplot";
import { useChartColors } from "../../lib/chart-colors";

/** Age composition as a joy plot: one ridgeline lane per age band (first band
 * on top), peak height = that year's share. Single accent hue — identity is
 * carried by lane position + the band name end-label, not color. Tooltip
 * always reports the REAL percentages from at.pct, never the lane offsets. */
export default function AgeCompositionTrend({ at }: { at: AgeTrend }) {
  const colors = useChartColors();
  if (!at.years.length) return <ChartEmpty height={260}>無分齡資料</ChartEmpty>;
  const lanes = joyRidges(at.pct);
  const height = 60 * at.bands.length + 60;

  const series = lanes.flatMap((lane, bi) => [
    // invisible lane baseline (constant), stacked so the ridge fill sits on it
    { name: `_base${bi}`, type: "line" as const, stack: `joy${bi}`, symbol: "none" as const,
      lineStyle: { opacity: 0 }, data: at.years.map(() => lane.base),
      tooltip: { show: false }, silent: true },
    // the ridge itself (drawn in bi order: lower lanes render later, on top)
    { name: at.bands[bi], type: "line" as const, stack: `joy${bi}`, smooth: 0.4,
      symbol: "none" as const, lineStyle: { color: colors.accent, width: 2 },
      areaStyle: { color: colors.accent, opacity: 0.18 }, data: lane.scaled,
      endLabel: { show: true, formatter: at.bands[bi], color: colors.muted, fontSize: 11 } },
  ]);

  const option: EChartsOption = {
    grid: { left: 16, right: 64, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        const idx = Array.isArray(params) && params.length ? params[0].dataIndex : null;
        if (idx == null) return "";
        const rows = at.bands
          .map((b, bi) => ({ b, v: at.pct[bi]?.[idx] }))
          .filter((r) => r.v != null)
          .map((r) => `${r.b}:${(r.v as number).toFixed(1)}%`);
        return `${at.years[idx]}<br/>${rows.join("<br/>")}`;
      },
    },
    xAxis: { type: "category", data: at.years.map(String) },
    yAxis: { type: "value", show: false },
    series,
  };
  return <EChart option={option} height={height} />;
}
```

> 註:舊版的 `legend`、100% 堆疊、6 色 `colors.series` 全部移除;props 介面不變,`TrendsApp` 不需改。

- [ ] **Step 2: build**

Run: `npm --prefix web run build 2>&1 | tail -2`
Expected: 成功。

- [ ] **Step 3: 瀏覽器抽查**

/trends「分齡組成(逐年)」**深/淺各一輪**:
- 每 band 一條 lane、第一個 band(最年輕)在最上;右端 band 名(muted)。
- 峰形合理(有資料的年份起伏);峰微越入上方 lane 不糊(若糊,把 `joyRidges(at.pct)` 改 `joyRidges(at.pct, 1, 1.3)`——僅呼叫端調參,不改函式)。
- tooltip 顯示「年份 + 各 band 真實 %」;切換 🌙/☀️ 翻色。
- 女性參與、完賽時間演變兩區塊不受影響。

- [ ] **Step 4: Commit**

```bash
git add web/src/components/trends/AgeCompositionTrend.tsx
git commit -m "feat(ridge): /trends age composition as single-hue joy plot"
```

---

## Controller 收尾(合併前)

- [ ] `cd web && npx vitest run`(joyRidges 4 + 既有全綠)。
- [ ] `npm --prefix web run build`(成功)。
- [ ] 瀏覽器:/trends 三區塊深/淺一輪(joy plot 翻色、其餘兩圖不變)。

## Self-Review

**1. Spec coverage:** joyRidges 幾何(top-first base、peak 縮放、不除零、空輸入)→ Task 1 ✅;單 accent + endLabel 識別 → Task 2 series/endLabel ✅;stacked-pair → Task 2(`stack: joy${bi}` 隱形基線+稜線)✅;tooltip 真實 % → Task 2 formatter 讀 `at.pct` ✅;y 軸隱藏/x 年份 ✅;高度隨 band 數 ✅;props 不變、TrendsApp 零改動 ✅;peak 調參備援 → Task 2 Step 3 ✅;只動 3 檔 ✅。

**2. Placeholder scan:** 無 TBD;兩個檔案皆全碼;瀏覽器抽查有具體檢查點。

**3. Type consistency:** `joyRidges(pct, laneGap=1, peak=1.6): JoyLane[] {base, scaled}`(Task 1)與 Task 2 的 `lanes[bi].base/scaled` 一致;`AgeTrend {years, bands, pct}` 為既有型別;每 band 的兩 series 用同一 `stack: joy${bi}`(彼此堆疊、band 間互不堆疊)。
