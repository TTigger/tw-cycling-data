# Phase 2b-1:DistributionRidge + /race 完賽剖面 — 設計 spec

**日期**:2026-07-01
**狀態**:已核可方向,待寫實作計畫
**範圍**:建立可重用的「完賽時間分布密度稜線」元件 `DistributionRidge`,並用它取代 /race 的長條圖 `RaceTimeHistogram`,加上中位/冠軍參考線。Ridgeline 改版 Phase 2b 的第一個子項;之後 /benchmark(你的綠點)、/trends(堆疊)重用同一積木。

## 背景與動機

Phase 2a 已把全站配色統一成松綠 theme-aware。Phase 2b 把稜線母題落到各資料頁。/race 是最高流量詳情頁、地形隱喻最自然(一場賽事的完賽時間分布本身就是一條剖面)。現有 `RaceTimeHistogram`(吃 `DetailRow[]` 的 `r.t` 完賽秒數,`histogram(values,300)` → 長條)正是要改造的地方。

## 已核可決策

1. **`DistributionRidge` 為可重用元件**:輸入完賽秒數 + 選填 markers,畫成平滑填色密度稜線。
2. **實作取向:ECharts**(smooth line + gradient areaStyle),自帶軸/tooltip/markLine、吃現有 theme(翻色)、風險低;視覺上仍是一條稜線。(純 SVG 招牌稜線需自補軸/互動,不採。)
3. **/race**:用 `DistributionRidge` 取代 `RaceTimeHistogram`,加 **中位 + 冠軍(最速)** 兩條 marker。
4. 只動 /race 的分布呈現;排行榜/分組選擇/跨年帶不動;不改資料。

## 元件設計

### 純函式 `densityRidge`(可 vitest)
`densityRidge(values: number[], binWidth = 300): [number, number][]`
- 用既有 `histogram(values, binWidth)`(`scrapers`… 不,是 `web/src/lib/aggregate` 的 `histogram`,回 `{x0,x1,count}[]`)算分箱;回 `[binCenterSeconds, count]` 陣列(`binCenter = (x0+x1)/2`)。空輸入回 `[]`。
- 供 ECharts value 型 x 軸的 `series.data` 直接使用。

### 元件 `web/src/components/charts/DistributionRidge.tsx`
Props:
```ts
interface RidgeMarker { value: number; label: string; color?: string; }
{ values: number[]; markers?: RidgeMarker[]; height?: number; binWidth?: number; }
```
- `const colors = useChartColors();`(render body,翻色)。
- `const pts = densityRidge(values, binWidth ?? 300);` 空 → `<ChartEmpty>無時間資料</ChartEmpty>`。
- ECharts option:
  - `xAxis: { type: "value", axisLabel: { formatter: (v) => secondsToHMS(v) } }`(數值秒 → HH:MM:SS)。
  - `yAxis: { type: "value", name: "人數" }`。
  - `series: [{ type: "line", smooth: true, symbol: "none", data: pts, lineStyle: { color: colors.accent, width: 2 }, areaStyle: { color: colors.accent, opacity: 0.15 } }]`(平滑密度稜線 + 淡填)。
  - `markLine`(掛在 series):由 `markers` 產生,每條 `{ xAxis: m.value, label: { formatter: m.label, color: colors.ink }, lineStyle: { color: m.color ?? colors.secondary, type: "dashed" } }`。
  - `tooltip: { trigger: "axis", formatter }`:顯示該點時間(`secondsToHMS`)與人數。
- 回 `<EChart option={...} height={height ?? 280} />`。

### /race 套用(`RaceDetailApp.tsx`)
- import `DistributionRidge` 取代 `RaceTimeHistogram`(移除後者 import 與用處)。
- 在原本放 `<RaceTimeHistogram rows={detail} />` 之處改為:
  - 由 `detail` 取完賽秒數 `const ts = detail.map(r => r.t).filter((t): t is number => t != null);`
  - `markers = [{ value: median(ts), label: "中位", color: colors.secondary }, { value: Math.min(...ts), label: "冠軍", color: colors.ink }]`(median 用既有 `format`/`aggregate` 的分位或 `_quantile`;若無現成 helper,於元件外用簡單排序取中位)。
  - `<DistributionRidge values={ts} markers={markers} />`。
- `RaceDetailApp` 需要 `colors`(`useChartColors`)以給 marker 色;若該檔尚未引入則加(render body)。
- `RaceTimeHistogram.tsx` 檔案保留或刪除:**刪除**(YAGNI,無其他引用者)——實作時先 grep 確認無他處 import。

## 重用(後續子項,不在本 spec)

- 2b-2 /benchmark:`markers` 加 `{ value: 你的時間, label: "你", color: colors.accent }`,把使用者定位在分布上。
- 2b-3 /trends:多個 `DistributionRidge` 小倍數堆疊。

## 測試(照 dev-workflow)

- **vitest**:`densityRidge` — 已知輸入 → 正確的 `[center,count]` 節點(bin 中心、計數、空輸入 `[]`)。
- **build**:astro build 成功。
- **瀏覽器抽查**:一場賽事 /race「分布」**深/淺各一輪**——密度稜線 + 中位/冠軍 marker、tooltip 讀時間/人數、切換翻色;markers 位置合理(冠軍在最左、中位在峰附近)。

## 風險與緩解

- **marker 色與稜線同為 accent**:冠軍 marker 用 `colors.ink`(中性強)、中位用 `colors.secondary`(琴珀),避免與綠色稜線糊在一起。
- **value 型 x 軸的 markLine**:markLine 用 `xAxis: <秒數>` 定位(數值軸可直接放),不需 category index。
- **smooth line 過衝**:ECharts `smooth: true` 可能在密度谷底輕微負向;`yAxis` 不設 min 讓其自然,人數不會顯示負(視覺極小)。必要時 `smooth: 0.4`。
- **RaceTimeHistogram 刪除**:先 grep 全 repo 確認除 RaceDetailApp 外無引用再刪。

## YAGNI(不做)

- 不加分組(result_label)過濾到分布(維持現有「整場 rows」輸入;分組是排行榜/跨年帶的既有職責);若日後要,DistributionRidge 已能吃過濾後的 values。
- 不做純 SVG 招牌稜線版。
- 不動其他 /race 分頁與資料。
