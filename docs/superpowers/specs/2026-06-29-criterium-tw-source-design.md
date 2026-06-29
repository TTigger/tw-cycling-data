# criterium.tw 資料源(含 DNF / 完賽率)— 設計 spec

**日期**:2026-06-29
**狀態**:已核可,待實作
**範圍**:新增 criterium.tw 為第 6 個資料源,首次引入 DNF/DNS 狀態與圈數,並在 /race 頁顯示完賽率。

## 背景與動機

criterium.tw(正規 host `events.seh.com.tw`,SportSplits 計時)是 TCU 繞圈賽的官方成績平台。實地探勘確認:

- 完整公開逐筆成績:排名 · BIB · 姓名 · 分組 · 車隊 · 完賽時間 · **圈數 · FIN/DNF/DNS 狀態**(+ 每圈速度,本案不取)。
- 成績表為 server-rendered HTML(curl 200,免 JS),`/api/` 被 robots 擋,改爬 `/races/{id}/events/{n}` 頁。Cloudflare 不挑戰、robots 允許 ClaudeBot、無需登入。
- 目前 5 場、全為 TCU 繞圈賽:

| race id | 賽事 | 日期 |
|---|---|---|
| 19554 | TCU 苗栗繞圈賽 第七屆 | 2026-06-28 |
| 19267 | TCU 台中冬季繞圈賽 第六屆 | 2025-12-07 |
| 18931 | TCU 台中春季繞圈賽 第五屆 | 2025-04-20 |
| 18772 | TCU 台中冬季繞圈賽 第四屆 | 2024-12-22 |
| 18571 | TCU 台中城市繞圈賽 2024 | 2024-07-14 |

**獨家價值**:這是全資料集**唯一**帶 DNF/DNS 與圈數的來源。現有 `master.json` 完全沒有 DNF(`data-limitations` 記憶記載「NO DNF」),所有來源的成績頁只列完賽者。criterium.tw 直接補上這個缺口。

同一場 2026 苗栗繞圈賽也出現在 tsu.com.tw(縣長盃圓樓繞圈賽),但 tsu 結果頁目前 0 人、空表;criterium.tw 才是計時源頭且已公布。故直接收 criterium.tw,不等 tsu。

## 已核可的決策

1. **DNF/DNS/圈數**:完整收進資料 **並**上前端(完賽率/DNF 分析)。
2. **賽事範圍**:全 5 場都收。
3. **前端位置**:只在賽事頁 `/race` 顯示完賽率;選手頁本次不做。

## 取徑

`requests` + HTML 解析,免 headless、免 JS。種子 5 個 race id,逐場讀 overview 頁取得各分組 `/events/{n}` 子頁連結,再解析每個 event 的成績表。不抓每圈速度(RSC stream,YAGNI)。

## 元件設計

### 1. 爬蟲 `scrapers/criterium_crawl.py`

- 種子常數 `SEED_RACE_IDS = [19554, 19267, 18931, 18772, 18571]`。
- 對每個 race id:
  - GET `https://events.criterium.tw/races/{id}` → 取賽事名稱、日期(→ year)、各分組 `/events/{n}` 子頁連結(從頁面連結發現,不寫死 4–10)。
  - 對每個 event 子頁 GET `https://events.criterium.tw/races/{id}/events/{n}` → 解析成績 `<table>`,8 欄:排名 · BIB · 姓名 · 分組 · 車隊 · 完賽時間 · 圈數 · 狀態。
- 每列 → `common.make_record(...)`:
  - `source_platform="criterium.tw"`(pin 此標籤,實際抓 events.criterium.tw,避免 host 別名造成重複 race_key)。
  - `source_url` = 該 event 頁 URL;`source_format="html"`。
  - `race_name_raw`(例:「TCU 苗栗繞圈賽 第七屆」),`year` 由賽事日期明確帶入,`date` = 賽事日期。
  - `category_raw` = 分組原字串;`gender`/`age_group` 用既有 `common.parse_division` 盡量解出(解不出則 None)。
  - `rank_overall`(整體名次)、`bib`、`team`。
  - **`status`** ∈ {FIN, DNF, DNS}(由狀態欄正規化)。
  - **`laps`** = 圈數(int;DNS 可能為 0/None)。
  - `finish_time`/`finish_seconds`:**只有 FIN 有**;DNF/DNS 為 None。
  - 身分錨:criterium 不暴露 TCU/UCI id → `tsu_rider_id`/`uci_id` 留 None,以姓名為錨(與既有無 id 者一致)。
- 輸出 `data/processed/criterium_2024_2026.json`(JSON 陣列)。
- 用 `common.polite_get`(禮貌間隔);小站(5 場、~35 子頁),全量直爬即可,可選 per-race 快取但非必要。

### 2. Schema:`common.make_record`

- 在 record dict 新增兩欄,預設 None:
  - `status`(None | "FIN" | "DNF" | "DNS")
  - `laps`(None | int)
- 既有所有來源維持 None(它們只有完賽者)。`status=None` 代表「無此資訊」;完賽率只在「有 status 的賽事」計算。
- 欄位放在 record 的合理位置(緊鄰 `finish_*` / 結果相關欄)。

### 3. `merge.py`

- `SOURCE_PREFIXES` 加 `"criterium_"`。
- 修改丟棄邏輯(現為 `if fs is not None and fs <= 0: drop`):
  - `status in ("DNF", "DNS")` 的列**即使無 finish_seconds 也保留**。
  - 其餘無 status 的 zero-time/未計時雜訊仍丟棄(維持現有行為)。
- `status`/`laps` 隨 record dict 自動寫入 `master.json` 與 `master.public.json`(make_record 已含這兩欄,json.dump 自然帶出)。
- 去重:DNF/DNS 列無 fs → 跳過 `(year, name_raw, finish_seconds)` 去重(criterium 為唯一 DNF 源,無雙計)。完賽者仍照常跨源去重;sorted-glob 下 `criterium_` 在 `cycling_tsu` 之前載入,故未來 tsu 苗栗若補上、同名同完賽時間會被去重掉,criterium 版勝出。
- summary 加 `by_status` 計數。
- **不**在 `normalize.py` 加 criterium↔tsu 的 RACE_KEY_CANONICAL 映射(YAGNI;tsu 苗栗目前無資料,真出現再處理)。

### 4. `build_viz.py` + 前端 `/race`

- build_viz 在產生每場 `web/public/data/race/*.json` 時,對「該場有任何列帶 status」者加:
  - `completion: { fin: int, dnf: int, dns: int, rate: float }`(rate = fin / (fin+dnf+dns))。
  - 無 status 的賽事**不輸出** `completion` 欄。
- 前端:`web/src/components/race/` 新增「完賽率」區塊(顯示 FIN/DNF/DNS 人數 + 完賽率 %),與現有賽事 DNA / 嚴苛度同區;`race.completion` 存在才渲染,否則優雅隱藏。
- 純函式與型別放 `web/src/lib/`(types.ts 加 `completion` 型別;若需顯示用格式化函式則 co-located vitest)。

### 5. `race_type.py`

- 確認 criterium 賽名(含「繞圈賽」)被分類為繞圈/criterium 類型;若未涵蓋則補規則 + pytest。

## 測試(照 dev-workflow 全套)

- `scrapers/test_criterium_crawl.py`:存一份真實 event 頁 sample HTML 為 fixture(如 `data/processed/sample_criterium_*.html`),測解析出正確 records,涵蓋 FIN / DNF / DNS / laps / 分組解析。
- merge 丟棄邏輯測試:DNF/DNS 列存活、無 status 的 zero-time 列被丟。
- build_viz completion 測試:有 status → 輸出正確 completion;無 status → 不輸出該欄。
- 前端 lib vitest(若有格式化函式)。
- 流程:`python -m pytest scrapers/` → build → 前端 → `npm test` → `npx astro check` → 瀏覽器驗證 → 各自 commit、分別 push。

## PDPA

維持去識別化:criterium 列同樣只輸出 `name_masked`、加鹽 athlete_id 等;`name_raw` 僅存內部 master.json。新欄 status/laps 非個資,可公開。

## 記憶更新

- `data-limitations`:把「NO DNF, NO registration/starter counts」修正為「除 criterium.tw 的 5 場 TCU 繞圈賽提供真實 FIN/DNF/DNS + 圈數外,其餘來源仍只有完賽者」。
- 視情況新增一則 criterium 來源參考記憶(host、結構、種子、scrapeability)。

## 不做(YAGNI)

- 每圈速度圖(RSC stream 解析)。
- 選手頁 `/athletes` 個人 DNF 標註(本次只 /race)。
- tsu↔criterium 的 canonical race_key 映射(等 tsu 真有資料)。
- sitemap 自動發現(5 場種子即可;未來擴充再加)。

## 風險與緩解

- **跨源雙計**:靠既有 `(year, name_raw, finish_seconds)` 去重 + criterium 先載入;若 tsu 補資料且時間有微差可能漏去重 → 屆時加 canonical 映射。
- **DNF 列污染既有統計**:build_athletes/insights/difficulty/race_dna 多以 finish_seconds 為基礎;DNF 列 finish_seconds=None,需確認這些 build 對 None 安全(多數已 filter)。實作時逐一驗證 None 不致出錯。
- **平台改版**:Next.js 站結構可能變;解析以表頭/欄位語意為主、容錯,失敗時記錄並跳過該場。
