# Phase 2b-1:DistributionRidge + /race 完賽剖面 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建可重用的密度稜線元件 `DistributionRidge` 並用它把 /race 的完賽時間長條圖改成密度剖面 + 中位/冠軍參考線。

**Architecture:** 純函式 `densityRidge`(以既有 `histogram` 算 `[binCenter,count]`)+ `DistributionRidge.tsx`(ECharts smooth line + gradient area,theme-aware,markLine)。/race 的 `RaceDetailApp` 把 `<RaceTimeHistogram>` 換成 `<DistributionRidge>`(**保留** RaceTimeHistogram 檔——ClimbsApp 仍用)。

**Tech Stack:** Astro + React islands + ECharts + vitest。

## Global Constraints

- ECharts canvas 顏色由 `useChartColors()`(Phase 2a)提供、於 render body 取用,`themechange` 翻色。
- **不得刪除** `web/src/components/race/RaceTimeHistogram.tsx`(`ClimbsApp.tsx` 仍 import 它);只在 `RaceDetailApp` 改用 DistributionRidge。
- 稜線線+填 = `colors.accent`;marker:中位 = `colors.secondary`(琴珀,虛線)、冠軍 = `colors.ink`(中性,虛線)。
- 不改資料、不動 /race 其他分頁與排行榜/分組/跨年帶。
- build 成功;既有 vitest 綠。

## 執行順序
Task 1(DistributionRidge + densityRidge + vitest)→ Task 2(/race 套用)→ controller 收尾。

---

## Task 1: `DistributionRidge` 元件 + `densityRidge` 純函式

**Files:** Modify `web/src/lib/aggregate.ts`; Create `web/src/components/charts/DistributionRidge.tsx`, `web/src/lib/aggregate.test.ts`(若已存在則追加)

**Interfaces:** Produces
```ts
export function densityRidge(values: number[], binSeconds: number): [number, number][];
export interface RidgeMarker { value: number; label: string; color?: string; }
// default export DistributionRidge({ values, markers?, height?, binWidth? })
```

- [ ] **Step 1: 寫失敗測試**

在 `web/src/lib/aggregate.test.ts`(若無則新建,含 `import { describe, it, expect } from "vitest";`)追加:

```ts
import { densityRidge } from "./aggregate";

describe("densityRidge", () => {
  it("returns [binCenter, count] pairs from the histogram (300s bins)", () => {
    // 3 values in bin [0,300) center 150; 2 values in bin [300,600) center 450
    expect(densityRidge([10, 20, 30, 350, 360], 300)).toEqual([[150, 3], [450, 2]]);
  });
  it("empty input -> []", () => {
    expect(densityRidge([], 300)).toEqual([]);
  });
});
```

Run: `cd web && npx vitest run src/lib/aggregate.test.ts -t densityRidge` → FAIL(densityRidge 未定義)。

- [ ] **Step 2: 實作 `densityRidge`(加到 `web/src/lib/aggregate.ts` 末尾)**

```ts
/** Histogram reshaped for a density ridgeline: [binCenterSeconds, count] pairs. */
export function densityRidge(values: number[], binSeconds: number): [number, number][] {
  return histogram(values, binSeconds).map((b) => [(b.x0 + b.x1) / 2, b.count]);
}
```
(`histogram` 與 `Bin {x0,x1,count}` 已在同檔;`densityRidge` 置於 `histogram` 之後即可引用。)

- [ ] **Step 3: 跑測試**

Run: `cd web && npx vitest run src/lib/aggregate.test.ts -t densityRidge` → PASS(2 tests)。

- [ ] **Step 4: 建 `web/src/components/charts/DistributionRidge.tsx`**

```tsx
import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import ChartEmpty from "./ChartEmpty";
import { densityRidge } from "../../lib/aggregate";
import { secondsToHMS } from "../../lib/format";
import { useChartColors } from "../../lib/chart-colors";

export interface RidgeMarker { value: number; label: string; color?: string; }

/** Finish-time distribution as a smooth density ridge (accent line + faint fill),
 * with optional vertical markers (median / winner / your time). Theme-aware. */
export default function DistributionRidge({
  values, markers = [], height = 280, binWidth = 300,
}: { values: number[]; markers?: RidgeMarker[]; height?: number; binWidth?: number }) {
  const colors = useChartColors();
  const pts = densityRidge(values, binWidth);
  if (!pts.length) return <ChartEmpty height={height}>無時間資料</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 48, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const pt = Array.isArray(p) ? p[0] : p;
        if (!pt || !pt.value) return "";
        return `${secondsToHMS(pt.value[0])}<br/>${pt.value[1]} 人`;
      },
    },
    xAxis: { type: "value", axisLabel: { formatter: (v: number) => secondsToHMS(v) } },
    yAxis: { type: "value", name: "人數" },
    series: [{
      type: "line", smooth: 0.4, symbol: "none", data: pts,
      lineStyle: { color: colors.accent, width: 2 },
      areaStyle: { color: colors.accent, opacity: 0.15 },
      markLine: markers.length ? {
        symbol: "none",
        data: markers.map((m) => ({
          xAxis: m.value,
          label: { formatter: m.label, color: colors.ink, position: "insideEndTop" as const },
          lineStyle: { color: m.color ?? colors.secondary, type: "dashed" as const },
        })),
      } : undefined,
    }],
  };
  return <EChart option={option} height={height} />;
}
```

- [ ] **Step 5: build + commit**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。
```bash
git add web/src/lib/aggregate.ts web/src/lib/aggregate.test.ts web/src/components/charts/DistributionRidge.tsx
git commit -m "feat(ridge): DistributionRidge component + densityRidge helper"
```

---

## Task 2: /race 用 DistributionRidge 取代長條圖

**Files:** Modify `web/src/components/race/RaceDetailApp.tsx`

**Interfaces:** Consumes `DistributionRidge`(Task 1)、`quantile`(既有 `aggregate.ts`)、`useChartColors`。

- [ ] **Step 1: 換 import + 加 hooks/helpers**

在 `RaceDetailApp.tsx`:
- 移除 `import RaceTimeHistogram from "./RaceTimeHistogram";`(**只移這行 import**;不刪該檔)。
- 新增:
  ```ts
  import DistributionRidge from "../charts/DistributionRidge";
  import { quantile } from "../../lib/aggregate";
  import { useChartColors } from "../../lib/chart-colors";
  ```
- 在元件函式體、**所有 early return 之前**(與其他 `useState`/`useMemo` 同區),加 `const colors = useChartColors();`。

- [ ] **Step 2: 換 line 130 的用處**

把:
```tsx
<Card title="完賽時間分布" hint="每 5 分鐘一桶"><RaceTimeHistogram rows={detail} /></Card>
```
換成:
```tsx
<Card title="完賽時間分布" hint="每 5 分鐘一桶 · 中位與冠軍標於稜線">
  {(() => {
    const ts = detail.map((r) => r.t).filter((t): t is number => t != null);
    const sorted = [...ts].sort((a, b) => a - b);
    const markers = sorted.length ? [
      { value: quantile(sorted, 0.5), label: "中位", color: colors.secondary },
      { value: sorted[0], label: "冠軍", color: colors.ink },
    ] : [];
    return <DistributionRidge values={ts} markers={markers} />;
  })()}
</Card>
```
(`detail` 在此處非 null;`quantile(sorted, 0.5)` 取中位、`sorted[0]` 為最速冠軍。)

- [ ] **Step 3: build + 瀏覽器抽查 + commit**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。瀏覽器開一場賽事 /race「總覽/分布」卡**深/淺各一輪**:密度稜線(綠線+淡填)、中位(琴珀虛線)、冠軍(中性虛線)、hover 讀時間/人數、切換翻色;冠軍在最左、中位在峰附近。
```bash
git add web/src/components/race/RaceDetailApp.tsx
git commit -m "feat(ridge): /race finish-time distribution as density ridge with median/winner"
```

---

## Controller 收尾(合併前)

- [ ] `cd web && npx vitest run`(densityRidge + 既有全綠)。
- [ ] `npm --prefix web run build`(成功)。
- [ ] `grep -rn "RaceTimeHistogram" web/src`(應仍存在於 ClimbsApp + 自身檔;RaceDetailApp 不再引用)。
- [ ] 瀏覽器:/race 分布深/淺翻色 + markers 合理;/climbs 的 RaceTimeHistogram 未受影響(仍正常、綠色)。

## Self-Review

**1. Spec coverage:** DistributionRidge 可重用元件 → Task 1 ✅;densityRidge 純函式 → Task 1 ✅;ECharts smooth+area+markLine+tooltip → Task 1 ✅;/race 取代 histogram + 中位/冠軍 marker → Task 2 ✅;不刪 RaceTimeHistogram(ClimbsApp 用)→ Global Constraints + Task 2 只移 import ✅;marker 色錯開(median 琴珀/winner ink)→ Task 2 ✅;theme-aware 翻色 → useChartColors render body ✅;不動資料/其他分頁 → 僅碰 line 130 + imports ✅。

**2. Placeholder scan:** 無 TBD;densityRidge/DistributionRidge 全碼;/race 換法給完整 JSX + import 清單;median 用既有 `quantile`。

**3. Type consistency:** `densityRidge(values,binSeconds): [number,number][]`(Task 1)被 DistributionRidge 的 `series.data` 使用;`RidgeMarker {value,label,color?}`(Task 1)被 /race markers 陣列(Task 2)一致建構;`quantile(sorted,q)`、`secondsToHMS`、`useChartColors` 皆既有匯出。
