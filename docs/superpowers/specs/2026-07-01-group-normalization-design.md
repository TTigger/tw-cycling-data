# 分組/距離正規化(比較單位 = 賽事 × 距離/項目)— 設計 spec

**日期**:2026-07-01
**狀態**:已核可,待寫實作計畫
**範圍**:把「winner/median/分位/benchmark」的比較單位從 `race_key` 改為 **(race_key, result_label)**,讓混多距離/項目的賽事不再把不同組拿來混比(如「冠軍 80 秒(計時賽)vs 中位 1011 秒(公路賽)」)。影響 `build_crossyear`(跨年趨勢)、`build_benchmarks`(分齡對標)、其前端頁與 MCP。加碼項 #27(三項中最大)。

## 背景與動機

實測:**125 個 race_key 中 71 個混多 result_label,其中 63 個組間時間落差 >2 倍**——半數賽事的「整場 winner/median」混了不同項目,對不上。鐵證:`桃園繞圈賽` 整場 winner=80s(個人計時賽 TT)、median=1011s(公路繞圈賽);分組後各自合理(公路繞圈 winner 970/median 1085、TT winner 80/median 94)。

正確比較單位 = **(race_key, result_label)**(距離/項目)。/race 排行榜已依分組重排(不改);問題在跨年趨勢與分齡對標的聚合。

## 已核可的決策

1. **分組鍵 = `result_label`**(距離/項目);缺值 → 群組名 `全部`。單組賽事結構退化成一組、顯示不變。
2. **完整正規化**:`build_crossyear` 與 `build_benchmarks` 都改以 (race_key, result_label) 聚合;前端 /race、/trends、/benchmark 加「距離/組別」選擇;MCP 加組別參數。
3. **不動 dataset(逐筆)、不重發 release**;只重建 `web/public/data/v1`。

## 資料形狀變更

### `race_crossyear.json`(build_crossyear)
- 舊:`{race_key: [{y,winner,median,p25,p75,n}]}`。
- 新:`{race_key: {group_label: [{y,winner,median,p25,p75,n}]}}`;每組**各自** ≥2 年才收(維持既有跨年門檻);`group_label` = result_label 或 `全部`。
- 計算來源:改以**完賽記錄**(含 `result_label`;slim viz 無此欄)分組;沿用既有 `_quantile`。

### `benchmarks.json`(build_benchmarks)
- 舊:`{race_key: {rn, years, cohorts:{all/age/age|g/cat}}}`。
- 新:`{race_key: {rn, groups: {group_label: {years, cohorts:{all/age/age|g/cat}}}}}`;cohort 在**各 result_label 群組內**計算(門檻 n≥20、101 斷點不變);`group_label` = result_label 或 `全部`。

## 元件設計

### 後端
- `scrapers/build_viz.py:build_crossyear`:改吃完賽記錄、以 (race_key, result_label) 分組;回上述巢狀結構。純函式部分可測。
- `scrapers/benchmarks.py`:`build_index` 改以 (race_key, result_label) 分層;`cohort_keys` 不變(仍算 all/age/cat,但在群組內)。輸出上述巢狀結構。`scrapers/build_benchmarks.py` 對應調整。
- 相依測試 `test_build_viz.py`/`test_benchmarks.py` 更新為分組斷言。

### 前端
- `web/src/lib/overview.ts`:`CrossYearMap` 型別改為 `Record<race_key, Record<group_label, CrossYearPoint[]>>`。
- `web/src/lib/types.ts`(或 benchmark 型別處):benchmark 型別加 `groups` 維度。
- `web/src/lib/benchmark.ts`:`availableCohorts`/`pickDefaultCohort` 仍作用在「某群組的 cohorts」;新增取群組清單/預設群組的純函式(如 `availableGroups(raceEntry)`、`pickDefaultGroup`)。
- `web/src/components/race/RaceDetailApp.tsx` + `CrossYearTrend`:多組時顯示**組別下拉**,選了畫該組 `FinishTimeBand`;單組免選直接畫。
- `web/src/components/trends/TrendsApp.tsx`:賽事選擇 → **組別選擇** → `FinishTimeBand`。
- `web/src/components/benchmark/BenchmarkTool.tsx`:選賽事 → **選距離/組別** → 選 cohort → 時間 → 百分位。
- `FinishTimeBand` 本身不變(仍吃一組 `CrossYearPoint[]`)。

### MCP
- `mcp-server/tw_cycling_data_mcp/query.py:benchmark_lookup`:加 `result_label`(或 `group`)參數;先選群組(預設單組/最大組),再選 cohort。
- `server.py:race_benchmark` tool:加 `result_label` 參數。`client.py` 不變(仍讀 benchmarks.json)。
- `docs/API.md` + `build_manifest`(benchmarks 端點說明)更新為巢狀 groups 結構。

## 重建 / 誠實

- 重跑:`build_viz`(crossyear)+ `build_benchmarks` + `build_manifest` → 重建 `web/public/data/v1`(含 race_crossyear.json、benchmarks.json、manifest)。astro build。**不動 master/dataset、不重發 release**。
- UI 標明目前看的是哪一組;群組名用 result_label(誠實呈現該賽事的距離/項目)。
- 單組賽事:退化成一組,選擇器隱藏或只有一個選項,顯示與現況一致。

## 測試(照 dev-workflow)

- 後端 pytest:`build_crossyear` 對混多 result_label 的輸入 → 各組各自的 winner/median(不再跨組混);`benchmarks.build_index` → groups 巢狀、各組 cohort 門檻;既有測試更新。
- 前端 vitest:群組選擇純函式(`availableGroups`/`pickDefaultGroup`)、benchmark cohort 在群組內選擇。
- MCP pytest:`benchmark_lookup` 帶 group 參數的挑選 + 預設群組 + 查無。
- 流程:`pytest scrapers/ mcp-server/` → 重建 → `vitest` → astro build → 瀏覽器抽查:一場多距離賽事的 /race(組別下拉、各組 winner/median 合理)、/trends(賽事→組別→帶)、/benchmark(賽事→距離→cohort);對照桃園繞圈賽等,winner/median 不再對不上。

## 風險與緩解

- **crossyear 資料來源改動**(從 slim viz 改吃完賽記錄):確認 race_key/year/result_label/finish_seconds 皆在完賽記錄;既有 viz.json 不受影響(不加欄、不變大)。
- **race_crossyear.json/benchmarks.json 變大**(多一層 group):多數賽事單組,增幅有限;build 後實測。
- **前端多處消費 CrossYearMap/benchmark**:型別改動會逐一觸發;逐處加群組維度並以 build/型別檢查兜住。
- **result_label 髒值**:直接當群組名(誠實);同一組時間本應相近,異常組別自然分開。
- **MCP 破壞性**:`race_benchmark` 新增選填 `result_label`,未給時預設單組/最大組,向後相容。

## YAGNI(不做)

- 不改 /race 排行榜(已分組)。
- 不改 dataset 逐筆結構、不重發 release。
- 不做跨賽事的距離等效換算。
- 群組鍵只用 result_label(不混用 category_raw/dist;category 仍是 cohort 維度)。

## 未來待辦

- 若 result_label 在少數賽事語意不佳,可加正規化對映;目前直接採用。
