# Phase 2b-4:/athletes 生涯稜線 — 設計 spec

**日期**:2026-07-02
**狀態**:已核可方向,待寫實作計畫
**範圍**:把選手頁的進步曲線 `AthleteProgression` 改造成**單軸生涯稜線**:勝過% 主稜線(松綠+漸層填)、出賽場次改為資料點大小編碼、生涯最佳年 markLine——並一併修掉現有的**雙 y 軸反模式**。Ridgeline 改版 Phase 2b 的第四個子項。

## 背景與動機

現況 `AthleteProgression`(`{ history: AthleteHistoryRow[] }`,經 `progression(history)` 得 `pts[{y, pct, races}]`):
- 「最佳同場勝過%」= 左軸折線(accent + 0.10 填)、「出賽場次」= **右軸** bar(secondary 0.45)。
- **雙 y 軸是 dataviz 指引點名的 #1 反模式**(兩個尺度誤導交叉/比例);且視覺是普通折線,與稜線母題不合。

2b-4 一石二鳥:單軸化 + 稜線化——「一個人的騎乘生涯 = 一條稜線」,峰 = 巔峰年。

## 已核可決策

1. **單軸**:y = 勝過%(0–100,唯一 y 軸);出賽場次**不再有第二軸**。
2. **主稜線**:松綠 `colors.accent` 2px 線 + 淡填(opacity ~0.15,同 DistributionRidge 視覺);smooth。
3. **場次 → 點大小編碼**:每個資料點 `symbolSize` 隨該年 `races` 縮放(約 6–16px;純函式可測);tooltip 保留精確場次。
4. **生涯最佳年**:markPoint/markLine 標最高 pct 的年(琴珀 `colors.secondary` 虛線 + 標籤「生涯最佳」;`MarkLineComponent` 已註冊)。
5. props(`{ history }`)與 `progression()` 純函式不動 → 呼叫端零改動;只改 `AthleteProgression.tsx` + 一個新純函式(symbolSize 縮放)。

## 元件設計

### 純函式 `careerSymbolSizes`(放 `web/src/lib/athletes.ts`,可 vitest)

```ts
export function careerSymbolSizes(races: number[], min = 6, max = 16): number[];
```
- 把各年出賽場次線性映射到 `[min, max]` px:`size = min + (r - lo) / (hi - lo) * (max - min)`;全相等(hi=lo)→ 全 `(min+max)/2`;空輸入 `[]`。
- 與既有 `progression` 同檔(athletes.ts);測試追加到既有 `web/src/lib/athletes.test.ts`。

### `AthleteProgression.tsx`(改寫 option)

- 保留:`const colors = useChartColors();`、`progression(history)`、`pts.length < 2 → ChartEmpty`。
- **yAxis 改單一**:`{ type:"value", name:"勝過%", min:0, max:100, axisLabel:{formatter:"{value}%"} }`(移除右軸)。
- **series 改單一稜線**:
  ```ts
  const sizes = careerSymbolSizes(pts.map((p) => p.races));
  const bestIdx = pts.reduce((bi, p, i) => (p.pct! > pts[bi].pct! ? i : bi), 0);
  series: [{
    name: "最佳同場勝過%", type: "line", smooth: 0.4,
    symbol: "circle", symbolSize: (_: unknown, params: { dataIndex: number }) => sizes[params.dataIndex],
    lineStyle: { color: colors.accent, width: 2 },
    itemStyle: { color: colors.accent },
    areaStyle: { color: colors.accent, opacity: 0.15 },
    data: pts.map((p) => p.pct),
    markLine: {
      symbol: "none",
      data: [{ xAxis: bestIdx,
        label: { formatter: "生涯最佳", color: colors.ink, position: "insideEndTop" },
        lineStyle: { color: colors.secondary, type: "dashed" } }],
    },
  }]
  ```
  (category 軸的 markLine 用 `xAxis: <index>` 定位;或 `xAxis: String(pts[bestIdx].y)` 用類別值——實作擇一驗證。)
- **移除**:右軸、bar series。
- **tooltip**:維持「`{y} 年` + 勝過% + 出賽 N 場」,改讀單 series + closure 的 `pts[dataIndex].races`(不再從第二 series 取)。

## 測試(照 dev-workflow)

- **vitest**:`careerSymbolSizes` — 線性映射端點(lo→min、hi→max)、全相等→中值、空→[]。
- **build**:astro build 成功。
- **瀏覽器抽查**:一位多年份選手的 /athletes 個人頁**深/淺各一輪**——單軸生涯稜線(綠線+淡填)、點大小隨場次、生涯最佳琴珀虛線、tooltip 年/勝過%/場次、切換翻色;右軸與 bar 已不在。

## 風險與緩解

- **markLine 在 category 軸定位**:`xAxis: index` 與 `xAxis: "類別值"` 皆為 ECharts 支援;實作以瀏覽器驗證擇可靠者。
- **symbolSize callback 簽名**:ECharts `symbolSize: (value, params) => number`;用 `params.dataIndex` 對 `sizes`。
- **場次資訊弱化**:第二軸移除後場次只剩點大小+tooltip——這是刻意取捨(反模式修正);點大小提供趨勢感、tooltip 給精確值。
- **pct 可能 null**:既有 `filter((p) => p.pct != null)` 已保證非 null(bestIdx 的 `p.pct!` 安全)。

## YAGNI(不做)

- 不加逐場散點/多 series;不動 `progression()`;不動選手頁其他元件(Radar/CalibratedProgress/SeasonReview…)。
- 不做「難度校正」版生涯線(CalibratedProgress 已另有)。
