# 長期縱貫趨勢(Longitudinal Trends)— 設計 spec

**日期**:2026-06-30
**狀態**:已核可,待寫實作計畫
**範圍**:新增資料集的長期演變視覺化——新頁 `/trends`(女性比例逐年、分齡組成逐年、單場完賽時間分布帶逐年)+ 強化 /race 既有 `CrossYearTrend`(winner/median 兩線 → 加 P25/P75 分布帶 + 完賽人數)。路線圖 Feature 3。**不整合 API/MCP**(YAGNI;趨勢資料已在 overview.json,API 已服務)。

## 背景與動機

對標馬拉松資料專案的招牌:「完賽時間分布/參與如何隨數十年演變」。本資料集涵蓋 2009–2026,適合說這個長期故事。

**已存在(不重做)**:逐年參賽趨勢(首頁 `ParticipationTrend`)、年×月賽季熱度(`SeasonHeatmap`)、單場 winner/median 逐年(/race `CrossYearTrend`,資料 `race_crossyear.json` = 每 race_key `[{y,winner,median}]`)。

**真正的縱貫缺口(本案補)**:
1. **完賽時間分布帶**:現有只有 winner+median 兩線;缺「典型完賽者(中位)+ 場域離散度(P25–P75)」隨年變化,看選手變快/變慢、場域擴張/壓縮。
2. **女性比例逐年**:目前只有跨年快照(`overview.women`),非逐年。
3. **分齡組成逐年**:目前只有快照(`overview.composition`),非逐年。

**誠實前提**:全體完賽時間逐年會被「每年賽事組合不同」混淆,**不做**;時間趨勢只在**同一賽事內**比較(分布帶 per race_key)。

## 已核可的決策

1. **形狀**:兩者都做——新 `/trends` 頁 + 強化 /race 的 `CrossYearTrend`。
2. **共用**:分布帶邏輯做成一個 `FinishTimeBand` 元件,/race 與 /trends 共用(寫一次、用兩處)。
3. **不整合 API/MCP**。

## 資料變更(延伸既有 build,無新大型檔)

### `build_crossyear`(於 `scrapers/build_viz.py`)
- 現產 `race_crossyear.json`:`{race_key: [{y, winner, median}]}`。
- 延伸每年條目加:`p25`、`p75`(完賽秒數分位)、`n`(該年該場完賽人數)。新結構 `{y, winner, median, p25, p75, n}`。
- 分位數定義:對該 race_key 該年的完賽秒數升冪排序 `s`,`p_k = s[round(k/100*(len-1))]`(同 benchmarks 的 nearest-rank,程式碼層面共用或各自實作但定義一致)。`winner=min`、`median=p50`。
- 僅對**多年**賽事有意義(單年仍輸出,但 /trends 與 CrossYearTrend 對單年點仍可顯示一個帶)。

### `build_overview`(於 `scrapers/build_viz.py`)
- 現產 overview.json(kpi/heat/trend/women/composition/sources)。新增兩塊:
  - `genderTrend`:`{years: number[], f: number[], known: number[]}`——每年女性數 `f` 與已知性別總數 `known`(比例 = f/known);僅納入 `gender ∈ {M,F}` 的完賽者。
  - `ageTrend`:`{years: number[], bands: string[], pct: number[][]}`——每年各 `age_band` 佔「該年有分齡者」的百分比(`pct[bandIndex][yearIndex]`);`bands` 為固定排序(如 `["U19","19-29","30-39","40-49","50-59","60+"]`,排除 `MASTER` 雜訊)。
- overview.json 仍 <10KB。

## 元件設計(單一職責)

### 後端(純函式 + 測試)
- 於 `build_viz.py` 既有 `build_crossyear`/`build_overview` 內延伸;若聚合邏輯夠獨立,抽成可單測的小函式(如 `year_quantiles(seconds)`、`gender_trend(rows)`、`age_trend(rows)`),於 `scrapers/test_*.py` 測。

### 前端
- `web/src/lib/types.ts`:`CrossYearMap` 條目加 `p25,p75,n`;新增 `GenderTrend`、`AgeTrend` 型別(對齊 overview.json)。
- `web/src/components/charts/FinishTimeBand.tsx`(或 `components/trends/`):輸入一場的 `[{y,winner,median,p25,p75,n}]` → ECharts 中位線 + P25–P75 區帶(+ winner 細線 + tooltip 顯示 n)。**/race 與 /trends 共用**。
- `web/src/components/trends/GenderShareTrend.tsx`:女性比例逐年折線(年 n 過小不畫點,標註覆蓋)。
- `web/src/components/trends/AgeCompositionTrend.tsx`:分齡組成逐年堆疊面積/長條(%)。
- `web/src/components/trends/TrendsApp.tsx`:island,載入 overview.json(genderTrend/ageTrend)+ race_crossyear.json + races 索引;含一個賽事選擇器(多年賽事)驅動 `FinishTimeBand`。
- `web/src/pages/trends.astro`:掛載 `TrendsApp`(self-loading,對齊 InsightsApp/BenchmarkTool 慣例)。
- `web/src/layouts/Base.astro`:導覽加 `/trends` 連結。
- `web/src/components/race/CrossYearTrend.tsx`:改用 `FinishTimeBand`(或在既有圖加 P25–P75 帶 + n),由兩線升級為分布帶。

## 誠實 / 涵蓋 / PDPA

- 全體時間逐年不做(混淆);時間趨勢只在同一 race_key 內。
- 女性比例:僅已知性別(覆蓋 ~63%、早年偏少);年內已知性別 n 低於門檻(如 30)不畫該年點,UI 標註。
- 分齡:僅有分齡者(~36%,集中競技賽),UI 標註「僅競技/分組賽有分齡」。
- 純聚合,無任何個資。

## 測試(照 dev-workflow)

- 後端 pytest:`year_quantiles`(p25/median/p75/n 正確、單調、邊界 n=1)、`gender_trend`(逐年 f/known、跳過未知)、`age_trend`(逐年 band %、排除 MASTER、僅有分齡者)。既有 build 測試不破。
- 前端 vitest:任何純函式(若 TrendsApp 有客端衍生);型別對齊。
- 流程:`pytest scrapers/` → 重建 build_viz(產生延伸後的 race_crossyear.json + overview.json)→ `vitest` → astro build → 瀏覽器抽查 /trends(性別/分齡逐年 + 選一場看分布帶)與一場多年賽事的 /race(CrossYearTrend 已是分布帶)。

## 風險與緩解

- **早年/小樣本誤導**:年 n 門檻 + UI 覆蓋標註;分位數不外推。
- **race_crossyear.json 變大**:每年多 3 個數字;多年賽事有限,增幅小;build 後實測。
- **CrossYearTrend 既有外觀回歸**:升級時保留 winner/median 語意,只加帶 + n;瀏覽器抽查既有多年賽事頁。
- **overview.json 是首頁載入**:新增 genderTrend/ageTrend 兩塊;確認首頁(OverviewApp)不因新欄位出錯(只讀取自己用的鍵)。

## YAGNI(不做)

- API/MCP 整合(已決議不做)。
- 全體/跨賽事的完賽時間逐年(混淆)。
- 體重/功率/天候等外部因子(無資料)。
- 互動式年份刷選、預測模型。

## 未來待辦(本次不做,記錄備查)

- 把 /trends 的某張圖做成可分享卡片(對標 ShareCard)。
- 若日後 age 覆蓋提升,分齡組成逐年可更可信。
