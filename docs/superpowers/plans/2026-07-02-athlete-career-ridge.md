# Phase 2b-4:/athletes 生涯稜線 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `AthleteProgression` 改成單軸生涯稜線(勝過% 松綠稜線 + 場次點大小 + 生涯最佳 markLine),並移除雙 y 軸反模式。

**Architecture:** 新純函式 `careerSymbolSizes(races, min=6, max=16)`(athletes.ts,線性映射場次→點徑,可 vitest);`AthleteProgression` 改單 series/單 y 軸:accent 稜線 + `symbolSize` callback + markLine 生涯最佳;右軸與 bar series 移除;tooltip 改讀 closure 的 `pts`。

**Tech Stack:** Astro + React islands + ECharts + vitest。

## Global Constraints

- **單 y 軸**(勝過% 0–100);出賽場次無第二軸(改點大小 + tooltip)。
- 主稜線 = `colors.accent` 2px + areaStyle 0.15 + `smooth: 0.4`;點 `symbolSize` 由 `careerSymbolSizes(pts.map(p=>p.races))` 提供(6–16px)。
- 生涯最佳 = markLine 於最高 pct 的年(`xAxis: String(pts[bestIdx].y)` 類別值定位),`colors.secondary` 虛線 + 標籤「生涯最佳」(`colors.ink`)。
- `careerSymbolSizes`:lo→min、hi→max 線性;hi===lo → 全 `(min+max)/2`;空 `[]`。
- props(`{ history }`)、`progression()`、`ChartEmpty` 門檻(`pts.length < 2`)不動;顏色 `useChartColors()` render body。
- 只動 `web/src/lib/athletes.ts`、`web/src/lib/athletes.test.ts`、`web/src/components/athletes/AthleteProgression.tsx`。
- build 成功;既有 vitest 綠。

## 執行順序
Task 1(careerSymbolSizes + vitest)→ Task 2(元件改寫)→ controller 收尾。

---

## Task 1: `careerSymbolSizes` 純函式

**Files:** Modify `web/src/lib/athletes.ts`(追加函式)、`web/src/lib/athletes.test.ts`(追加測試)

**Interfaces:** Produces `export function careerSymbolSizes(races: number[], min = 6, max = 16): number[];`

- [ ] **Step 1: 追加失敗測試(athletes.test.ts 末尾)**

```ts
import { careerSymbolSizes } from "./athletes";

describe("careerSymbolSizes", () => {
  it("maps race counts linearly to [min, max] px", () => {
    expect(careerSymbolSizes([1, 3, 5], 6, 16)).toEqual([6, 11, 16]);
  });
  it("all-equal counts -> midpoint size", () => {
    expect(careerSymbolSizes([4, 4, 4], 6, 16)).toEqual([11, 11, 11]);
  });
  it("empty -> []", () => {
    expect(careerSymbolSizes([], 6, 16)).toEqual([]);
  });
});
```
(若該檔既有測試未用 `describe` 包裹亦可照其風格;`import { describe, it, expect } from "vitest";` 若檔頭已有就不重複。)

- [ ] **Step 2: RED**

Run: `cd web && npx vitest run src/lib/athletes.test.ts`
Expected: FAIL(careerSymbolSizes 未匯出)。

- [ ] **Step 3: 實作(athletes.ts 末尾)**

```ts
/** Career ridge marker sizes: races-per-year mapped linearly to [min, max] px.
 * Equal counts collapse to the midpoint; empty input stays empty. */
export function careerSymbolSizes(races: number[], min = 6, max = 16): number[] {
  if (!races.length) return [];
  const lo = Math.min(...races), hi = Math.max(...races);
  if (hi === lo) return races.map(() => (min + max) / 2);
  return races.map((r) => min + ((r - lo) / (hi - lo)) * (max - min));
}
```

- [ ] **Step 4: GREEN**

Run: `cd web && npx vitest run src/lib/athletes.test.ts`
Expected: PASS(3 新 + 既有)。

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/athletes.ts web/src/lib/athletes.test.ts
git commit -m "feat(ridge): careerSymbolSizes race-count point sizing"
```

---

## Task 2: `AthleteProgression` 改單軸生涯稜線

**Files:** Modify `web/src/components/athletes/AthleteProgression.tsx`(改寫 option)

**Interfaces:** Consumes `careerSymbolSizes`(Task 1,from `../../lib/athletes` — 該檔已 import `progression`,同處追加)、`useChartColors`。Props 不變。

- [ ] **Step 1: 改寫元件 option(保留外殼)**

保留:import 區(athletes import 追加 `careerSymbolSizes`)、`const colors = useChartColors();`、`const pts = progression(history).filter((p) => p.pct != null);`、`pts.length < 2 → ChartEmpty`。把 `option` 整段換成:

```tsx
  const sizes = careerSymbolSizes(pts.map((p) => p.races));
  const bestIdx = pts.reduce((bi, p, i) => ((p.pct as number) > (pts[bi].pct as number) ? i : bi), 0);

  const option: EChartsOption = {
    grid: { left: 48, right: 48, top: 32, bottom: 36 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const first = Array.isArray(p) ? p[0] : p;
        const idx = first?.dataIndex;
        if (idx == null || !pts[idx]) return "";
        return `${pts[idx].y} 年<br/>最佳場次贏過 ${pts[idx].pct}%<br/>出賽 ${pts[idx].races} 場`;
      },
    },
    xAxis: { type: "category", data: pts.map((p) => String(p.y)) },
    yAxis: { type: "value", name: "勝過%", min: 0, max: 100, axisLabel: { formatter: "{value}%" } },
    series: [{
      name: "最佳同場勝過%", type: "line", smooth: 0.4,
      symbol: "circle",
      symbolSize: (_: unknown, params: { dataIndex: number }) => sizes[params.dataIndex],
      lineStyle: { color: colors.accent, width: 2 },
      itemStyle: { color: colors.accent },
      areaStyle: { color: colors.accent, opacity: 0.15 },
      data: pts.map((p) => p.pct),
      markLine: {
        symbol: "none",
        data: [{ xAxis: String(pts[bestIdx].y),
          label: { formatter: "生涯最佳", color: colors.ink, position: "insideEndTop" as const },
          lineStyle: { color: colors.secondary, type: "dashed" as const } }],
      },
    }],
  };
```
(移除:`yAxis` 陣列的右軸、`出賽場次` bar series、舊 tooltip 的雙 series 查找。)

- [ ] **Step 2: build**

Run: `npm --prefix web run build 2>&1 | tail -2`
Expected: 成功。

- [ ] **Step 3: 瀏覽器抽查**

/athletes 選一位**多年份**選手個人頁,**深/淺各一輪**:
- 單軸生涯稜線(綠線 + 淡填),點大小隨該年場次(多場年點較大)。
- 「生涯最佳」琴珀虛線落在最高 pct 的年;tooltip 顯示 年/勝過%/場次。
- 右軸與 bar 已不在;切換 🌙/☀️ 翻色;個人頁其他卡(Radar、CalibratedProgress…)不受影響。

- [ ] **Step 4: Commit**

```bash
git add web/src/components/athletes/AthleteProgression.tsx
git commit -m "feat(ridge): athlete career ridge — single-axis, race-count point size, best-year mark"
```

---

## Controller 收尾(合併前)

- [ ] `cd web && npx vitest run`(3 新 + 既有全綠)。
- [ ] `npm --prefix web run build`(成功)。
- [ ] `grep -n "yAxisIndex\|出賽場次.*bar" web/src/components/athletes/AthleteProgression.tsx`(應空——右軸/bar 已移除)。
- [ ] 瀏覽器:/athletes 深/淺一輪(稜線/點大小/最佳線/翻色)。

## Self-Review

**1. Spec coverage:** 單軸(右軸移除)→ T2 ✅;稜線視覺(accent 2px + 0.15 填 + smooth)→ T2 ✅;場次點大小(careerSymbolSizes 6–16、等值中點、空防護)→ T1+T2 ✅;生涯最佳 markLine(類別值定位、secondary 虛線、ink 標籤)→ T2 ✅;tooltip 年/勝過%/場次(closure 讀 pts)→ T2 ✅;props/progression/ChartEmpty 不動 → T2 保留外殼 ✅;只動 3 檔 ✅。

**2. Placeholder scan:** 無 TBD;函式與 option 全碼;抽查有具體檢查點。

**3. Type consistency:** `careerSymbolSizes(races:number[], min=6, max=16): number[]`(T1)= T2 `sizes` 用法;`pts[{y,pct,races}]` 為既有 `progression` 輸出(pct 經 filter 非 null,`as number` 安全);markLine `xAxis: String(pts[bestIdx].y)` 與 xAxis category `data: pts.map(p=>String(p.y))` 同值域。
