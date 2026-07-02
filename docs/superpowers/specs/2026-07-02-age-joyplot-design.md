# Phase 2b-3:/trends 分齡組成 Joy Plot 稜線圖 — 設計 spec

**日期**:2026-07-02
**狀態**:已核可方向,待寫實作計畫
**範圍**:把 /trends 的「分齡組成(逐年)」從 100% 堆疊面積圖改成經典 **ridgeline/joy plot**——每個年齡帶一條稜線一條 lane,x=年份、峰高=該年占比,垂直堆疊微重疊。全站唯一真正的多類別稜線圖,招牌感最強。Ridgeline 改版 Phase 2b 的第三個子項。

## 背景與動機

原 2b-3 構想「堆疊多個 DistributionRidge」**不可行**:/trends 的完賽時間只有 crossyear 分位摘要(無逐年逐筆分布),且 `FinishTimeBand` 已是填色帶、稜線感足夠。據實改為方案 A:`AgeCompositionTrend` 的資料(`AgeTrend { years, bands, pct[band][year] }`)剛好支撐 joy plot——ridgeline 圖表的原型正是 joy plot。

**取捨(已知會接受)**:joy plot 以美感/形狀閱讀換一點精確度(重疊時讀確切 % 較難);tooltip 提供精確值補償。

## 已核可決策

1. `AgeCompositionTrend` 改為 joy plot:每 band 一條 lane,x=年份,峰高=占比,垂直堆疊,峰可微越入上方 lane(`peak≈1.6`)。
2. **單一 accent 色**(松綠,線 2px + 填 0.18):識別由 **lane 位置 + 每條稜線右端直接標籤(band 名)** 承載(dataviz 原則:非 color-alone;文字用 ink/muted 不用 series 色)。
3. **純函式 `joyRidges`** 負責幾何(可 vitest);元件用本 repo 已驗證的 **stacked-pair** 技巧(隱形基線 + 堆疊填色,同 `FinishTimeBand`)。
4. **tooltip 顯示真實 %**(closure 讀原始 `at.pct`,非合成偏移值)。
5. 只改 `AgeCompositionTrend.tsx` + 新純函式;資料、loadOverview、/trends 其他區塊不動。

## 元件設計

### 純函式 `joyRidges`(`web/src/lib/joyplot.ts`,新檔,可 vitest)

```ts
export interface JoyLane { base: number; scaled: number[]; }
export function joyRidges(pct: number[][], laneGap = 1, peak = 1.6): JoyLane[];
```
- `pct[bi][yi]` = 第 bi 個 band 在第 yi 年的 %。
- 第一個 band 在**最上層** lane:`base(bi) = (nBands - 1 - bi) * laneGap`。
- 全域最大 pct 映射到 `peak * laneGap`:`scale = (peak * laneGap) / maxPct`(maxPct=0 → 全 0,不除零);`scaled[bi][yi] = pct[bi][yi] * scale`。
- 空輸入回 `[]`。

### `AgeCompositionTrend.tsx`(改寫)

- `const colors = useChartColors();`(render body);`const lanes = joyRidges(at.pct);`
- 每 band 兩個 series(**下方 lane 後畫**,即依 bi 遞增順序 push——bi 越大 base 越低、越晚畫、蓋上方):
  - 隱形基線:`{ type:"line", stack:"joy"+bi, symbol:"none", lineStyle:{opacity:0}, data: years.map(()=>lanes[bi].base), tooltip:{show:false}, silent:true }`
  - 稜線:`{ type:"line", stack:"joy"+bi, smooth:0.4, symbol:"none", lineStyle:{ color: colors.accent, width:2 }, areaStyle:{ color: colors.accent, opacity:0.18 }, data: lanes[bi].scaled, endLabel:{ show:true, formatter: bands[bi], color: colors.muted, fontSize:11 } }`
- **y 軸隱藏**(`yAxis: { type:"value", show:false }`,合成偏移無意義);x=年份 category;grid 右側留 endLabel 空間(如 `right: 56`)。
- **tooltip**:`trigger:"axis"`,formatter 用 closure 讀 `at.pct[bi][dataIndex]` 顯示「年份 + 各 band 真實 %」(略過 0% 或全部列出擇一,實作定;不顯示合成值)。
- 空資料 → 既有 `<ChartEmpty>` 保留。
- 高度隨 band 數放大(如 `height = 60 * bands.length + 60`),lane 不擠。

## 測試(照 dev-workflow)

- **vitest**(`web/src/lib/joyplot.test.ts`):`joyRidges` — 已知 pct 矩陣 → base 順序(第一 band 最高 base)、全域最大值縮放到 `peak*laneGap`、maxPct=0 不除零、空輸入 `[]`。
- **build**:astro build 成功。
- **瀏覽器抽查**:/trends「分齡組成」**深/淺各一輪**——每 band 一條 lane、右端 band 名標籤、峰形合理(如 40-49 近年隆起)、tooltip 顯示真實 %、切換翻色;女性參與/完賽時間演變兩區塊不受影響。

## 風險與緩解

- **stacked-pair 與 endLabel 相容性**:endLabel 掛在「稜線」series(堆疊的第二段),顯示值為堆疊頂 y——僅用它放 band 名文字(formatter 固定字串),不顯數值,無誤導。
- **重疊蓋字**:峰越入上方 lane 可能貼近上方 endLabel;`peak=1.6` 保守,實作時視覺不佳可降至 1.3–1.4(不改介面)。
- **tooltip 對合成值**:一律用 formatter 覆蓋,讀原始 `at.pct`;隱形基線 series `tooltip:{show:false}` + `silent`。
- **band 順序**:沿用 `at.bands` 既有順序(年輕→年長),第一個在最上 lane。

## YAGNI(不做)

- 不做 6 色 joy plot(單 accent + 直接標籤已足,並更招牌)。
- 不加互動選 band/年份;不加表格檢視(tooltip 已給精確值;全站慣例一致)。
- 不動 GenderShareTrend、FinishTimeBand、資料管線。
