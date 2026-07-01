# Phase 2a 配色統一 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 換 accent 為松綠、次色琴珀,並讓所有內頁圖表與分享卡改由「隨主題回色」的 JS 來源驅動,使整站配色一致且深/淺可翻。

**Architecture:** 新增 `chart-colors.ts`(共用 `useDark` + `useChartColors` + 純函式 `chartColors(dark)`);18 個圖表元件把寫死 hex 換成 hook 回傳的色;`tokens.css --accent`、`echarts-theme.ts color[]`、`share-card.ts` 基礎 palette 換新色。ECharts 元件的 option 於 render body 計算,故加 hook 後 themechange 會自動重繪翻色。

**Tech Stack:** Astro + React islands + Tailwind v4 + ECharts + vitest。

## Global Constraints

- **調色盤(深 / 淺)**:accent `#3DBB7A`/`#1E8A56`;secondary `#F2B84B`/`#B8791C`;muted `#84908A`/`#5A6560`;grid `#2A3538`/`#D2D8D3`;ink `#ECEFEC`/`#12181A`。
- **series[](≥3 類別)**:深 `["#3DBB7A","#F2B84B","#7FA9B6","#9BB089","#B597BA","#C2766A"]`;淺 `["#1E8A56","#B8791C","#3F6B78","#5C7355","#8A6D9C","#A0564B"]`。
- **heat[](序列熱圖)**:深 `["#12201A","#256B48","#3DBB7A","#7FE0AE"]`;淺 `["#EAF3EC","#8FCDA9","#3DBB7A","#1E8A56"]`。
- ECharts canvas 不可用 CSS 變數;顏色由 `useChartColors()` 提供,取色須在 render/重繪路徑上(themechange 時重算)。
- **不動**資料管線、不改頁面版面(那是 Phase 2b)。share-card 的獎牌 tier 色(platinum/gold/silver/bronze)**保留不動**。
- 回歸:build 成功;dist CSS 仍同含深底 `#0E1315` 與淺底 `#EFF1EE`。CSS 註解不得含撇號。

## 執行順序
Task 1(chart-colors 基礎)→ 2(token/theme 換色)→ 3、4、5(三組元件遷移)→ 6(share-card)→ controller 收尾。

---

## Task 1: `chart-colors.ts`(共用 useDark + useChartColors + 純函式)

**Files:** Create `web/src/lib/chart-colors.ts`, `web/src/lib/chart-colors.test.ts`; Modify `web/src/components/charts/EChart.tsx`

**Interfaces:** Produces
```ts
export interface ChartColors { accent:string; secondary:string; muted:string; grid:string; ink:string; series:string[]; heat:string[]; }
export function chartColors(dark: boolean): ChartColors;
export function useDark(): boolean;
export function useChartColors(): ChartColors;
```

- [ ] **Step 1: 寫失敗測試 `web/src/lib/chart-colors.test.ts`**

```ts
import { describe, it, expect } from "vitest";
import { chartColors } from "./chart-colors";

describe("chartColors", () => {
  it("dark mode = terrain green accent + amber secondary", () => {
    const c = chartColors(true);
    expect(c.accent).toBe("#3DBB7A");
    expect(c.secondary).toBe("#F2B84B");
    expect(c.series[0]).toBe("#3DBB7A");
    expect(c.heat[0]).toBe("#12201A");
    expect(c.heat.at(-1)).toBe("#7FE0AE");
  });
  it("light mode = deeper green + deep amber", () => {
    const c = chartColors(false);
    expect(c.accent).toBe("#1E8A56");
    expect(c.secondary).toBe("#B8791C");
    expect(c.ink).toBe("#12181A");
    expect(c.series[0]).toBe("#1E8A56");
    expect(c.heat.at(-1)).toBe("#1E8A56");
  });
  it("series has 6 categorical colors both modes", () => {
    expect(chartColors(true).series).toHaveLength(6);
    expect(chartColors(false).series).toHaveLength(6);
  });
});
```

Run: `cd web && npx vitest run src/lib/chart-colors.test.ts` → FAIL。

- [ ] **Step 2: 實作 `web/src/lib/chart-colors.ts`**

```ts
import { useEffect, useState } from "react";

export interface ChartColors {
  accent: string; secondary: string; muted: string; grid: string; ink: string;
  series: string[]; heat: string[];
}

const DARK: ChartColors = {
  accent: "#3DBB7A", secondary: "#F2B84B", muted: "#84908A", grid: "#2A3538", ink: "#ECEFEC",
  series: ["#3DBB7A", "#F2B84B", "#7FA9B6", "#9BB089", "#B597BA", "#C2766A"],
  heat: ["#12201A", "#256B48", "#3DBB7A", "#7FE0AE"],
};
const LIGHT: ChartColors = {
  accent: "#1E8A56", secondary: "#B8791C", muted: "#5A6560", grid: "#D2D8D3", ink: "#12181A",
  series: ["#1E8A56", "#B8791C", "#3F6B78", "#5C7355", "#8A6D9C", "#A0564B"],
  heat: ["#EAF3EC", "#8FCDA9", "#3DBB7A", "#1E8A56"],
};

/** Terrain palette for canvas charts (which cannot read CSS vars). */
export function chartColors(dark: boolean): ChartColors { return dark ? DARK : LIGHT; }

/** Tracks the site theme by listening for the themechange event the toggle fires. */
export function useDark(): boolean {
  const [dark, setDark] = useState(
    () => typeof document !== "undefined" && document.documentElement.classList.contains("dark"),
  );
  useEffect(() => {
    const on = () => setDark(document.documentElement.classList.contains("dark"));
    window.addEventListener("themechange", on);
    return () => window.removeEventListener("themechange", on);
  }, []);
  return dark;
}

export function useChartColors(): ChartColors { return chartColors(useDark()); }
```

- [ ] **Step 3: `EChart.tsx` 改用共用 `useDark`(移除私有複本)**

在 `web/src/components/charts/EChart.tsx`:刪除檔內私有 `function useDark() {...}`,改在頂部 `import { useDark } from "../../lib/chart-colors";`。其餘(`const theme = useDark() ? "claude-dark" : CLAUDE_THEME;`、`key={theme}`)不動。

- [ ] **Step 4: 測試 + build + commit**

Run: `cd web && npx vitest run src/lib/chart-colors.test.ts`(PASS);`npm --prefix web run build 2>&1 | tail -2`(成功)。
```bash
git add web/src/lib/chart-colors.ts web/src/lib/chart-colors.test.ts web/src/components/charts/EChart.tsx
git commit -m "feat(palette): chart-colors module (shared useDark + useChartColors)"
```

---

## Task 2: token accent + ECharts theme 換綠

**Files:** Modify `web/src/styles/tokens.css`, `web/src/lib/echarts-theme.ts`

- [ ] **Step 1: `tokens.css` 的 `--accent` 換松綠**

把 `html { … --accent: #D23120; … }` 改為 `--accent: #1E8A56;`;把 `html.dark { … --accent: #EC3A2B; … }` 改為 `--accent: #3DBB7A;`;把 `@theme inline { … --color-accent: var(--accent, #D23120); … }` 改為 `--color-accent: var(--accent, #1E8A56);`。其餘 token 不動。

- [ ] **Step 2: `echarts-theme.ts` 的 `color[]` 領頭換綠/琴珀**

把 `registerTheme("claude", …)` 的 `color:` 改為 `["#1E8A56", "#B8791C", "#3F6B78", "#5C7355", "#8A6D9C", "#A0564B"]`;把 `registerTheme("claude-dark", …)` 的 `color:` 改為 `["#3DBB7A", "#F2B84B", "#7FA9B6", "#9BB089", "#B597BA", "#C2766A"]`。其餘(軸/格線/文字/tooltip)不動。

- [ ] **Step 3: build + 雙色回歸 + commit**

Run:
```bash
npm --prefix web run build 2>&1 | tail -2
grep -ril "0E1315" web/dist/_astro/*.css && echo "DARK ok"; grep -ril "EFF1EE" web/dist/_astro/*.css && echo "LIGHT ok"
```
Expected: build 成功;DARK ok + LIGHT ok(minified CSS 為小寫 hex,故用 `-i`)。
```bash
git add web/src/styles/tokens.css web/src/lib/echarts-theme.ts
git commit -m "feat(palette): pine-green accent token + green/amber ECharts palette"
```

---

## Task 3: 遷移 charts/ + overview/ 元件(7 檔)

**Files:** Modify `web/src/components/charts/AgeBoxplot.tsx`, `CompetitivenessSpread.tsx`, `FinishTimeBand.tsx`, `FinishTimeHistogram.tsx`; `web/src/components/overview/CompositionByClass.tsx`, `SeasonHeatmap.tsx`, `WomenParticipation.tsx`

**Interfaces:** Consumes `useChartColors`(Task 1)。

- [ ] **Step 1: 各檔頂部加 hook,並依表換色**

對每個元件:在元件函式體最上方(算 `option` 之前)加 `const colors = useChartColors();`,並 `import { useChartColors } from "../../lib/chart-colors";`(charts/ 與 overview/ 皆為 `../../lib/chart-colors`)。然後套下表:

| 檔案:行 | 舊 | 新 |
|---|---|---|
| charts/AgeBoxplot.tsx:29 | `itemStyle: { color: "#FBEFE9", borderColor: "#D97757" }` | `itemStyle: { color: "transparent", borderColor: colors.accent }` |
| charts/CompetitivenessSpread.tsx:25 | `itemStyle: { color: "#5B7B8A" }` | `itemStyle: { color: colors.secondary }` |
| charts/FinishTimeBand.tsx:32 | `areaStyle: { color: "#5B7B8A", opacity: 0.18 }` | `areaStyle: { color: colors.secondary, opacity: 0.18 }` |
| charts/FinishTimeBand.tsx:35 | `itemStyle: { color: "#5B7B8A" }`(median) | `itemStyle: { color: colors.secondary }` |
| charts/FinishTimeBand.tsx:37 | `itemStyle: { color: "#D97757" }`(winner) | `itemStyle: { color: colors.accent }` |
| charts/FinishTimeHistogram.tsx:32 | `itemStyle: { color: "#D97757" }` | `itemStyle: { color: colors.accent }` |
| overview/CompositionByClass.tsx:15 | 男 `itemStyle: { color: "#5B7B8A" }` | `itemStyle: { color: colors.secondary }` |
| overview/CompositionByClass.tsx:16 | 女 `itemStyle: { color: "#D97757" }` | `itemStyle: { color: colors.accent }` |
| overview/SeasonHeatmap.tsx:20 | `inRange: { color: ["#FAF1EC","#E7A98C","#D97757","#A0564B"] }` | `inRange: { color: colors.heat }` |
| overview/SeasonHeatmap.tsx:23 | `borderColor: "#1F1E1D"` | `borderColor: colors.ink` |
| overview/WomenParticipation.tsx:18 | `itemStyle: { color: "#9A7AA0" }` | `itemStyle: { color: colors.accent }` |

> 確認每個 `option` 是在元件 render body 內計算(非模組層級 const);若某檔把 option 包在 `useMemo`,把 `colors` 加入其 deps。

- [ ] **Step 2: build + 瀏覽器抽查**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。瀏覽器抽查 / (季節熱圖)、/race(FinishTimeBand)**深/淺各一輪**——主色綠、次色琴珀、熱圖綠系,切換翻色。

- [ ] **Step 3: Commit**

```bash
git add web/src/components/charts/ web/src/components/overview/
git commit -m "feat(palette): charts/ + overview/ charts use theme-aware colors"
```

---

## Task 4: 遷移 athletes/ + race/ 元件(7 檔)

**Files:** Modify `web/src/components/athletes/AthleteCompare.tsx`, `AthleteProgression.tsx`, `AthleteRadar.tsx`, `CalibratedProgress.tsx`; `web/src/components/race/RaceDna.tsx`, `RaceTimeHistogram.tsx`, `TeamStrength.tsx`

**Interfaces:** Consumes `useChartColors`。import 路徑皆 `../../lib/chart-colors`。

- [ ] **Step 1: 各檔加 hook 並換色**

在各元件函式體最上方加 `const colors = useChartColors();`(AthleteCompare 見下特例)。套下表:

| 檔案:行 | 舊 | 新 |
|---|---|---|
| athletes/AthleteProgression.tsx:32 | `itemStyle: { color: "#D97757" }` | `itemStyle: { color: colors.accent }` |
| athletes/AthleteRadar.tsx:39 | `itemStyle: { color: "#D97757" }, areaStyle: { color: "rgba(217,119,87,0.18)" }` | `itemStyle: { color: colors.accent }, areaStyle: { color: colors.accent, opacity: 0.18 }` |
| athletes/CalibratedProgress.tsx:57 | `itemStyle: { color: "#D97757" }, areaStyle: { color: "rgba(217,119,87,0.10)" }` | `itemStyle: { color: colors.accent }, areaStyle: { color: colors.accent, opacity: 0.10 }` |
| race/RaceDna.tsx:57 | `color: ["#D97757", "#5B7B8A"]` | `color: [colors.accent, colors.secondary]` |
| race/RaceTimeHistogram.tsx:21 | `itemStyle: { color: "#D97757" }` | `itemStyle: { color: colors.accent }` |
| race/TeamStrength.tsx:17 | `itemStyle: { color: "#7C8C6B" }` | `itemStyle: { color: colors.accent }` |

**AthleteCompare.tsx 特例**(顏色為模組層級 const + 用於 ECharts 與 UI 文字):
- 刪除模組層級 `const A_COLOR = "#D97757";` / `const B_COLOR = "#5B7B8A";`。
- 在 `AthleteCompare` 元件函式體最上方加 `const colors = useChartColors();`,並以 `colors.accent`(原 A_COLOR)、`colors.secondary`(原 B_COLOR)取代所有引用;line 71 的 `"#6B6760"` 改 `colors.muted`。
- 若 `A_COLOR`/`B_COLOR` 也被 `StatRow` 等子元件用到,改為由 props 傳入 `colors.accent`/`colors.secondary`(讀該檔實際引用處,逐一替換)。

> `areaStyle` 的 rgba 改為 `color: colors.accent, opacity: …`——避免寫死舊色 rgba;綠色帶透明由 opacity 控制。

- [ ] **Step 2: build + 瀏覽器抽查**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。瀏覽器抽查 /athletes(AthleteCompare/Radar)、/race(RaceDna/RaceTimeHistogram)**深/淺各一輪**——綠/琴珀,切換翻色。

- [ ] **Step 3: Commit**

```bash
git add web/src/components/athletes/ web/src/components/race/
git commit -m "feat(palette): athletes/ + race/ charts use theme-aware colors"
```

---

## Task 5: 遷移 insights/ + trends/ 元件(4 檔)

**Files:** Modify `web/src/components/insights/AgeCurve.tsx`, `GeoHotspots.tsx`; `web/src/components/trends/AgeCompositionTrend.tsx`, `GenderShareTrend.tsx`

**Interfaces:** Consumes `useChartColors`。import 路徑皆 `../../lib/chart-colors`。

- [ ] **Step 1: 各檔加 hook 並換色**

在各元件函式體最上方加 `const colors = useChartColors();`。套下表:

| 檔案:行 | 舊 | 新 |
|---|---|---|
| insights/AgeCurve.tsx:37 | `areaStyle: { color: "rgba(217,119,87,0.12)" }` | `areaStyle: { color: colors.accent, opacity: 0.12 }` |
| insights/AgeCurve.tsx:40 | `itemStyle: { color: "#D97757" }` | `itemStyle: { color: colors.accent }` |
| insights/GeoHotspots.tsx:21 | `itemStyle: { color: "#D97757" }` | `itemStyle: { color: colors.accent }` |
| trends/GenderShareTrend.tsx:25 | `itemStyle: { color: "#D97757" }` | `itemStyle: { color: colors.accent }` |

**AgeCompositionTrend.tsx 特例**(模組層級 6 色類別陣列 line 6):
- 刪除模組層級 `const COLORS = ["#9CC3D5","#5B7B8A","#7FB069","#E6B05E","#D97757","#8E6C88"];`。
- 在元件函式體最上方加 `const colors = useChartColors();`,以 `colors.series` 取代所有 `COLORS` 引用(`colors.series` 為 6 色類別陣列)。

- [ ] **Step 2: build + 瀏覽器抽查**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。瀏覽器抽查 /trends(GenderShareTrend/AgeCompositionTrend)、/insights(AgeCurve)**深/淺各一輪**——切換翻色。

- [ ] **Step 3: Commit**

```bash
git add web/src/components/insights/ web/src/components/trends/
git commit -m "feat(palette): insights/ + trends/ charts use theme-aware colors"
```

---

## Task 5b: rgba 形式舊色掃除 + DistanceSpeedScatter

> 原盤點只 grep hex,漏了 rgba() 形式與 `DistanceSpeedScatter`。本 task 掃掉所有殘留 rgba 舊色。

**Files:** Modify `web/src/components/charts/DistanceSpeedScatter.tsx`; `web/src/components/athletes/AthleteCompare.tsx`, `AthleteRadar.tsx`, `AthleteProgression.tsx`, `CalibratedProgress.tsx`; `web/src/components/race/RaceDna.tsx`

**Interfaces:** Consumes `useChartColors`。

- [ ] **Step 1: 依表換色**

| 檔案:行 | 舊 | 新 |
|---|---|---|
| charts/DistanceSpeedScatter.tsx:20 | `itemStyle: { color: "rgba(217,119,87,0.5)" }` | `itemStyle: { color: colors.accent, opacity: 0.5 }`(需先加 `const colors = useChartColors();` + import) |
| athletes/AthleteProgression.tsx:37 | `itemStyle: { color: "rgba(91,123,138,0.45)" }` | `itemStyle: { color: colors.secondary, opacity: 0.45 }` |
| athletes/CalibratedProgress.tsx:57 | `itemStyle: { color: "rgba(91,123,138,0.7)" }` | `itemStyle: { color: colors.secondary, opacity: 0.7 }` |
| athletes/AthleteCompare.tsx:38 | `splitArea: { areaStyle: { color: ["rgba(0,0,0,0)", "rgba(217,119,87,0.04)"] } }` | `splitArea: { areaStyle: { color: ["rgba(0,0,0,0)", "rgba(128,128,128,0.05)"] } }` |
| athletes/AthleteRadar.tsx:35 | 同上 splitArea rgba(217…) | `["rgba(0,0,0,0)", "rgba(128,128,128,0.05)"]` |
| race/RaceDna.tsx:50 | 同上 splitArea rgba(217…) | `["rgba(0,0,0,0)", "rgba(128,128,128,0.05)"]` |

> `splitArea` 只是交替淡帶,改中性灰(兩模式皆適用、不需 accent)。translucent 數列填色改 `colors.accent/secondary` + `opacity`。AthleteProgression/CalibratedProgress/AthleteCompare/AthleteRadar/RaceDna 這些檔已有 `const colors = useChartColors();`(Task 4);DistanceSpeedScatter 需新加 hook + import。

- [ ] **Step 2: build + 驗證無殘留 + commit**

Run:
```bash
npm --prefix web run build 2>&1 | tail -2
grep -rnE "rgba\(217,\s*119,\s*87|rgba\(91,\s*123,\s*138" web/src/components
```
Expected:build 成功;grep 為空(元件內無殘留舊 rgba)。瀏覽器抽查 /explore 或含散點的頁深/淺翻色。
```bash
git add web/src/components/charts/DistanceSpeedScatter.tsx web/src/components/athletes/ web/src/components/race/
git commit -m "feat(palette): sweep remaining rgba old-orange/blue + DistanceSpeedScatter"
```

---

## Task 6: `share-card.ts` 基礎 palette 換色

**Files:** Modify `web/src/lib/share-card.ts`

- [ ] **Step 1: 換 `C` 基礎 palette(line 208)**

把 `const C = { paper: "#FAF9F5", accent: "#D97757", ink: "#2A2722", muted: "#7A7367", border: "#E7E2DA" };` 改為:
```ts
const C = { paper: "#EFF1EE", accent: "#1E8A56", ink: "#12181A", muted: "#5A6560", border: "#D2D8D3" };
```
並把同檔另兩處寫死的舊橘 canvas 填色換成新綠(OG 卡為淺底,直接用淺綠 rgba):
- line 246:`ctx.fillStyle = "rgba(217,119,87,0.12)"` → `ctx.fillStyle = "rgba(30,138,86,0.12)"`
- line 277:`ctx.fillStyle = "rgba(217,119,87,0.12)"` → `ctx.fillStyle = "rgba(30,138,86,0.12)"`

(OG/分享卡維持淺底,只換為新冷紙 + 松綠 accent;`rgba(30,138,86)` = 淺綠 `#1E8A56`。**不動** platinum/gold/silver/bronze 的 tier 色。)

- [ ] **Step 2: build + 抽查 + commit**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。若專案有分享卡產生腳本則重產一張抽查;否則確認 `C` 值正確且 tier 區塊未動。
```bash
git add web/src/lib/share-card.ts
git commit -m "feat(palette): share-card base palette to paper/green (tiers unchanged)"
```

---

## Controller 收尾(合併前)

- [ ] `cd web && npx vitest run`(chart-colors + 既有全綠)。
- [ ] `npm --prefix web run build`;`grep -ril 0E1315 web/dist/_astro/*.css && grep -ril EFF1EE web/dist/_astro/*.css`(雙色都在)。
- [ ] `grep -rnE "#(D97757|5B7B8A|7C8C6B|9A7AA0|E8916F)" web/src/components web/src/lib | grep -v echarts-theme`(應為空——確認無殘留舊 accent/次色寫死)。
- [ ] 瀏覽器:首頁(hero/CTA 綠)+ race/trends/athletes/insights/overview 各一含圖表頁,**深/淺各一輪**,切換翻色正常。

## Self-Review

**1. Spec coverage:** accent 換綠 → T2 ✅;次色琴珀/heat ramp → T1(chartColors)✅;chart-colors(useDark 抽出/useChartColors/純函式)→ T1 ✅;18 元件去寫死 → T3(7)+T4(7)+T5(4)✅;echarts color[] → T2 ✅;share-card C → T6 ✅;tier 保留 → T6 明列不動 ✅;不動資料/版面 → 各 task 僅碰色 ✅;雙色回歸 → T2/收尾 ✅。18 檔清單與 spec 一致(7+7+4=18)。

**2. Placeholder scan:** 無 TBD;chart-colors 全碼;每檔精確 file:line 舊→新映射;特例(AthleteCompare/AgeCompositionTrend)明列處理。

**3. Type consistency:** `ChartColors { accent,secondary,muted,grid,ink,series[],heat[] }`(T1)被 T3–T5 各元件與收尾一致引用;`series` 6 色與 `echarts-theme color[]`(T2)同值(themed 與 hook 色一致);`chartColors(dark)` 簽名一致;`useDark` 單一來源(T1)被 EChart 與 useChartColors 共用。
