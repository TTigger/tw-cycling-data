# 分齡/性別對標工具(Age/Gender Benchmark)— 設計 spec

**日期**:2026-06-30
**狀態**:已核可,待寫實作計畫
**範圍**:新增一個「對標工具」——使用者選賽事 + cohort(分齡/性別)+ 輸入完賽時間,回傳在該 cohort 的百分位與分布位置。含預運算資料 `benchmarks.json`、新頁 `/benchmark`,並**完整整合** Feature 1 的公開 API(manifest + docs/API.md)與 MCP server(新 tool)。路線圖 Feature 2。

## 背景與動機

對標對象(業餘車圈)流行「同齡同重對標,看自己在族群的位置」。本資料集有去識別化的完賽時間 + 分齡/性別/分組標籤,可做「這場/這距離,你的時間在分齡組第幾百分位」。

**資料現實(已量測 2026-06-30)**:全體 race rows 中 `age_group` 僅 **~20%**(集中在競技/聯賽分組賽;市民/挑戰賽多為 0%)、`gender` ~63%。因此純分齡若綁每一列只覆蓋 ~20%。故採**互動對標工具**形式 + **混合 cohort**(分齡優先,否則用賽事分組),並全程誠實標示 cohort 類型與樣本數。

**與既有功能區隔**:`ResultConverter`(跨場 rank 平移)、`AgeBoxplot`(分齡時間箱型分布)、`percentileInField/progression`(選手逐年最佳全場百分位)。本工具是「**輸入時間 → 分齡/性別 cohort 百分位**」的個人對標,三者互補不重疊。

## 已核可的決策

1. **Cohort**:混合——分齡優先,否則用賽事分組(category/division);誠實標示用的是哪種 + 樣本數。
2. **呈現**:互動對標工具(新頁 `/benchmark`):選賽事 → 選 cohort → 輸入完賽時間 → 回百分位 + 分布位置 + n。
3. **彙整單位**:同一 **race_key 跨所有年份**(同場地/同距離最穩),工具可選單一年份。**不跨 series**(避免不同路線混合)。
4. **整合範圍**:完整做——`benchmarks.json` 掛上 manifest + `docs/API.md`,並新增 MCP tool `race_benchmark`。

## 資料模型(`web/public/data/v1/benchmarks.json`)

對每個 race_key(其 `all` cohort 樣本 n ≥ `MIN_COHORT_N`=20 才收錄):

```jsonc
{
  "<race_key>": {
    "rn": "雙塔520",
    "years": [2022, 2023, 2024, 2025],
    "cohorts": {
      "all":            { "n": 831, "type": "all",  "label": "全部完賽者",   "bp": [t0, …, t100] },
      "age:40-49":      { "n": 240, "type": "age",  "label": "40-49 歲",     "bp": [...] },
      "age:40-49|g:M":  { "n": 205, "type": "age",  "label": "40-49 歲 男",  "bp": [...] },
      "cat:男子菁英":    { "n": 88,  "type": "cat",  "label": "男子菁英",      "bp": [...] }
    }
  }
}
```

- `bp` = **101 個完賽秒數斷點**(各百分位的時間),不論 n 多大每 cohort 固定 ≤101 數字 → 檔案有界。
- 每個 cohort 僅在 **n ≥ 20** 時收錄;`all` 必收(若 race 本身 ≥20)。
- cohort key:`all`、`age:<band>`、`age:<band>|g:<M|F>`、`cat:<division>`;`type` ∈ {all, age, cat};`label` 為 UI 顯示字串。
- 來源 row:`master.public.json` 的**完賽者**(`finish_seconds` 存在且為 finisher;沿用 `build_viz.is_finisher`)。分齡欄位用該記錄的 age band 欄位(實作時於計畫確認確切欄名,如 `age_band`/`age_group`),gender 用 `gender`,分組用 `category_raw`/`result_label`。

### 斷點與百分位定義(精確)

- `percentile_breakpoints(sorted_seconds: list[int]) -> list[int]`(長度 101):輸入升冪排序(快→慢)的完賽秒數;`bp[p] = sorted[ round(p/100 * (n-1)) ]`,p ∈ 0..100。故 `bp[0]`=最快、`bp[50]`=中位、`bp[100]`=最慢;單調非遞減。
- 前端查詢 `percentileBeat(bp, t) -> number`(0..100):回「你贏過(比你慢的)% 」。在 `bp`(升冪)中以線性內插找出 t 對應的百分位位置 `p`(t ≤ bp[0] → p=0;t ≥ bp[100] → p=100),回 `100 - p`。直覺:時間越快、贏過越多。

## 元件設計(單一職責)

### 後端
- `scrapers/benchmarks.py`(純函式,可測):
  - `cohort_keys(row) -> list[(key, type, label)]`:由一筆 row 算出它所屬的 cohort keys(`all` + age + age|gender + cat,缺資料的略過)。
  - `percentile_breakpoints(sorted_seconds) -> list[101]`(上述定義)。
  - `build_index(rows, min_n=20) -> dict`:分組蒐集完賽秒數 → 過濾 n≥min_n → 產生上述 JSON 結構。
- `scrapers/build_benchmarks.py`:`common.iter_records(master.public.json)` → 篩 finisher → `benchmarks.build_index` → 寫 `common.PUBLIC_DATA_DIR/benchmarks.json`。需在其他 build 之後或獨立執行皆可(只讀 master,不依賴其他產物)。

### 前端
- `web/src/lib/benchmark.ts`(純函式,可測):`percentileBeat(bp, t)`;`availableCohorts(raceEntry)`(回可選 cohort 清單,排序:age|gender → age → cat → all);`pickDefaultCohort(...)`(預設選最精確 age,否則 cat,否則 all);`hmsToSeconds(s)`(解析 `HH:MM:SS`/`MM:SS`/秒;若 lib 已有則沿用)。
- `web/src/components/benchmark/BenchmarkTool.tsx`:選賽事(可搜尋,沿用 races 索引)→ 選 cohort(下拉,顯示 type 與 n)→ 輸入完賽時間 → 顯示「你贏過該 cohort X%」+ 在分布上的位置(以 bp 畫一條分布/標記點,或簡單的百分位條)+ 樣本數 + 誠實註記。
- `web/src/pages/benchmark.astro`:載入 `benchmarks.json` + races 索引,掛載 `BenchmarkTool`。加入站台導覽。

### 誠實 / 涵蓋 / PDPA
- 僅用去識別化的完賽時間 + cohort 標籤聚合,**不暴露任何個資**(連 name_masked 都不需要)。
- UI 標示:cohort 是「真實分齡」或「賽事分組」;樣本數 n;n 介於 20–50 顯示「樣本少,僅供參考」。
- 沒有任何 cohort 達標的賽事不出現在工具的可選清單(誠實:不假裝有對標基準)。

## Feature 1 整合(完整做)

- **manifest**:`build_manifest.ENDPOINTS` 加一筆 `{"path": "benchmarks.json", "kind": "index", "description": "Per-race finish-time percentile breakpoints by age/gender/category cohort."}`。(manifest 由 `build_manifest.py` 產生,benchmarks 須在其前完成;於計畫安排執行順序。)
- **docs/API.md**:端點表 + schema 增 `benchmarks.json` 一段(含 cohort key 格式與 bp 定義)。
- **MCP**:
  - `client.py` 加 `benchmarks()` → `benchmarks.json`。
  - `query.py` 加純函式 `benchmark_lookup(benchmarks, race_key, seconds, age_band=None, gender=None) -> dict`:挑 cohort(同前端優先序)、用 `percentile_breakpoints` 邏輯的對應查詢回 `{race, cohort_label, cohort_type, n, percentile_beat, years}`;查無回清楚訊息。
  - `server.py` 加 tool `race_benchmark(race_key: str, finish_time: str, age_band: str = None, gender: str = None) -> dict`(`finish_time` 接受 HH:MM:SS 或秒)。

> 註:`percentileBeat` 的內插邏輯在前端(TS)與 MCP(Python)各一份——刻意各自實作於各自語言的純函式並各自單測(語言邊界,非可共用模組);兩邊以相同定義(本 spec)為準。

## 測試(照 dev-workflow)

- 後端 `scrapers/test_benchmarks.py`:`cohort_keys`(分齡/性別/cat/缺資料略過)、`percentile_breakpoints`(長度 101、單調、邊界 n=1/n 大)、`build_index`(n<20 過濾、結構正確)。
- 前端 `web/src/lib/benchmark.test.ts`(vitest):`percentileBeat`(比最快快→0 贏過 100%?方向正確、比最慢慢、中間內插、單點 cohort)、`availableCohorts`/`pickDefaultCohort` 排序與預設。
- MCP `mcp-server/tests/`:`benchmark_lookup`(cohort 優先序、查無、百分位值)。
- 流程:`pytest scrapers/ mcp-server/` → build_benchmarks + build_manifest → `vitest` → astro build → 瀏覽器抽查 `/benchmark`(一場有分齡競技賽 + 一場只有分組);各自 commit。

## 風險與緩解

- **分齡欄位名/格式**:master.public.json 的 age band 欄名與值格式(如 "30-39" vs "30")須於計畫確認;`cohort_keys` 對非標準值穩健略過。
- **小樣本誤導**:n≥20 門檻 + UI「樣本少」標記;百分位內插不外推超出 [0,100]。
- **檔案大小**:每 cohort ≤101 int;race_key×cohort 數量有限,預估數百 KB;build 後實測,過大則提高 MIN_COHORT_N 或減斷點數。
- **時間輸入解析**:容錯 HH:MM:SS / MM:SS / 純秒;非法輸入給提示不崩。

## YAGNI(不做)

- 跨 series 彙整、跨賽事的「等效時間」換算(那是 ResultConverter 的領域)。
- W/kg / 功率(無功率資料源)。
- 在 /race 或 /athletes 每列加百分位(已決議走獨立工具;覆蓋與雜訊考量)。
- 體重/年齡的連續迴歸模型;僅做分組百分位。

## 未來待辦(本次不做,記錄備查)

- 把對標也嵌入 /athletes 個人頁(「你這場在分齡組 top X%」)——待 age 覆蓋提升後。
- Node/TS MCP 對等工具(沿用 Feature 1 的未來待辦)。
