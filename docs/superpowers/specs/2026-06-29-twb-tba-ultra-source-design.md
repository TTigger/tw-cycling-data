# 協會超長距離認證賽資料源(TWB focusline + TBA Sheets)— 設計 spec

**日期**:2026-06-29
**狀態**:已核可,待實作
**範圍**:新增第 7、8 個資料源 —— `twbike.org`(TWB 台灣自行車協會,經 score.focusline JSON API)與 `taiwanbike.org`(TBA 中華民國自行車協會,Google Sheets)的超長距離認證賽(東/西三塔、雙塔、北高360、四極620、環大苗栗)。

## 背景與動機

PoC 探勘(2026-06-29)確認台灣兩大自行車協會的超長距離認證賽都有公開逐筆成績,但在我們尚未支援的平台(discover.py 標為 `BLOCKED`):

- **TWB(台灣自行車協會)**:成績在 `score.focusline.com.tw`,有**未授權 JSON API**(curl 200、免登入、免 headless):
  - `GET /api/Activity?urlPath=focusline` → 全部賽事目錄(actCode/actName/year/categories)。
  - `GET /api/Member/focusline?code={actCode}&categoryName={categoryNumber}&nameOrNumber=&page={n}` → 逐筆 JSON,30 筆/頁。
  - 塔賽 5 場(2023–2026):東三塔系列(東三塔550/東雙塔470)、西三塔600/雙塔520/北高360(×3 年)、東雙塔系列。
- **TBA(中華民國自行車協會)**:`taiwanbike.org` 一頁列 2010–2026 共 ~143 連結;**2022–2026 認證系列(雙塔520/北高360/四極620/環大苗栗)為公開 Google Sheets**,可用 `…/export?format=xlsx` 抓全分頁(逐筆在「選手總表」、名次在「總排序」分頁)。

**獨家價值**:台灣特色**超長距離(300–600km)認證賽**完賽時間,大規模(西三塔 590、雙塔520 831、北高360 1200 人…),是資料集目前缺的距離級距。

## 已核可的決策

1. **範圍**:focusline(TWB)+ taiwanbike Sheets(TBA)**兩個都做**。
2. **名次**:**不信任來源的 `totalSort`/名次**(認證賽名次非按時間排;東三塔550 rank1=19h、rank16=45min)。`rank_overall` 存 None,讓前端既有的「依(分組,完賽時間)重排」機制產生正確名次。

## 資料品質發現(PoC 實測)

- `gunTime`(focusline)/`成績`(Sheets)**就是完賽時間**(東三塔550 rank1=19:06:58、北高360 rank1=10:20:32,皆符合 300–600km 合理範圍)。
- **placeholder/DNF**:focusline 有 sub-分鐘佔位(00:00:07、00:00:50…;雙塔520 18 筆、西三塔 3 筆)。這些非真實完賽 → 過濾。
- `totalSort`(名次)不可靠 → 不採用(見決策 2)。
- focusline **無車隊欄**;TBA Sheets **有 `隊名`**。

## 取徑

兩個獨立 source adapter,皆 HTTP、免 headless,各自輸出 `data/processed/<source>_*.json` → 餵進**既有**統一 schema 與 merge/build。**不需新 schema 欄位、不動 merge 邏輯(除加 prefix)、不動 build、不動前端。**

## 元件設計

### 1. `scrapers/focusline_crawl.py`(TWB)
- `GET /api/Activity?urlPath=focusline` → 篩塔賽(actName 含 `塔|北高|360|四極`)。
- 對每個 (actCode, category)(category 用 `categories[].number`,非 name):分頁 `GET /api/Member/focusline?code={actCode}&categoryName={number}&nameOrNumber=&page={n}`,30 筆/頁,直到不足 30 筆或空。
- `build_records(rows, race_meta)`(純函式,可測)→ `common.make_record(...)`:
  - `source_platform="twbike.org"`、`source_url`=該 API URL、`source_format="json"`。
  - `race_name_raw = f"{category} {year}"`(每個距離=一場,如「東三塔550 2026」);`year` 由 actDate/year 帶入;`date` 由 actDate。
  - `category_raw = group`(男40/M30…);`gender`(男→M/女→F,或由 group 首字);`age_group`/`age_band` 用既有 `common.parse_division`/`age_band` 從 group 解。
  - `result_label = category`(東三塔550/雙塔…,即該距離項目);`bib = number`;`name_raw = name`。
  - `finish_time = gunTime`;`rank_overall = None`(決策 2);`team = None`。
  - **placeholder 過濾**:`common.time_to_seconds(gunTime) < 3600`(1 小時;這些是 300km+ 賽,最快也 10h+)→ 跳過該列。
- 輸出 `data/processed/focusline_2023_2026.json`。

### 2. `scrapers/taiwanbike_crawl.py`(TBA)
- 抓清單頁 `https://taiwanbike.org/index.php/2009-07-18-17-11-16` → 正則抽出 `<a>` 列:(賽事標題/年份, URL)。
- 只取 host = `docs.google.com/spreadsheets/d/{id}` 且年份 2022–2026 的連結(認證系列)。
- 每個 sheet:`GET https://docs.google.com/spreadsheets/d/{id}/export?format=xlsx` → openpyxl 讀**全分頁**;優先讀「選手總表」類逐筆分頁(名次分頁僅供參考,不採名次)。
- `taiwanbike_parse.py`(純函式,可測)寬鬆欄位對映(同義詞表,容忍各場結構漂移):
  - `參加編號/選手編號/號碼布 → bib`;`姓名 → name`;`隊名/車隊/隊伍 → team`;`組別/分組/性別組 → category_raw + age_group`;`性別 → gender`;`成績/大會成績/晶片成績/總成績 → finish_time`;`名次 → 不採用`。
  - 不認得的欄位略過;缺 `成績` 的列跳過。
- `race_name_raw = f"{事件標題去年份} {year}"`(如「雙塔520 2025」);`source_platform="taiwanbike.org"`;`source_format="xlsx"`;`rank_overall=None`。
- 同 placeholder 過濾(完賽時間 < 1 小時 → 跳過)。
- 輸出 `data/processed/taiwanbike_2022_2026.json`。
- 新增依賴:`openpyxl`(寫進 `requirements.txt`)。

### 3. 共用管線(改動極小)
- `scrapers/merge.py`:`SOURCE_PREFIXES` 加 `"focusline_"`、`"taiwanbike_"`。**無其他邏輯改動**(placeholder 已在爬蟲端濾掉)。
- **無 `common.make_record` 改動**(用既有欄位)。
- **無 build_* 改動、無前端改動**:這些是正常完賽賽事,/race 既有「依(分組,完賽時間)重排」處理 rank=None;/athletes/teams 等自動納入(TBA 有 team 故車隊頁也會涵蓋)。
- **race_type**:超長距離公路,`race_type.classify` 給 "road"(無繞圈/KOM/TT 標記)——可接受。

## 跨源去重

- 既有去重鍵 `(year, name_raw, int(finish_seconds))`。
- 2026 東塔賽同時在 twbike Apps Script 與 focusline → 我們只爬 focusline,無重複。
- TWB(twbike) vs TBA(taiwanbike)是**不同組織**的同名賽(雙塔520/北高360)→ 不同 `race_key`,各自獨立(正確,別硬合);若同一車友同年參加兩家同名賽、時間恰巧相同才會誤去重,機率極低。

## 測試(照 dev-workflow 全套)

- `scrapers/test_focusline_crawl.py`:存一份真實 `/api/Member` JSON sample(含正常完賽 + sub-分鐘 placeholder)→ 測 `build_records` 對映(finish_time/gender/age_group/result_label、placeholder 過濾、rank=None)。
- `scrapers/test_taiwanbike_parse.py`:存 2–3 種真實 header 的 sample 列 → 測寬鬆欄位對映(雙塔520 / 北高360 / 環大苗栗 不同 schema、隊名擷取、缺成績跳過、rank 不採用)。
- `scrapers/test_merge.py`:加 `focusline_`/`taiwanbike_` 在 `SOURCE_PREFIXES` 的斷言。
- 流程:`python -m pytest scrapers/` → 實爬 → `merge.py` → 全套 `build_*` → `validate.py` → astro check → 瀏覽器驗證(挑一場塔賽看 /race 排行榜依時間正確排序、TBA 場有車隊)→ 各自 commit。

## PDPA

維持去識別化:輸出僅 `name_masked`;`name_raw` 僅存內部 master.json(per-source `focusline_*/taiwanbike_*.json` 為 gitignored 內部檔,如其他來源)。

## 實作順序(降風險)

1. **focusline(TWB)先做**——最乾淨(JSON API),快速見效。
2. **taiwanbike(TBA)後做**——xlsx + 欄位漂移較複雜。
兩者共用的 merge prefix 一次加。

## 記憶更新

- 更新 `data-freshness-routine`:TWB/TBA BLOCKED 線索已實作為 focusline/taiwanbike 來源。
- 更新 `data-limitations`/來源清單:新增 6 來源 → 8 來源;超長距離級距補上。

## YAGNI(不做)

- taiwanbike 2010–2021 的舊 local xls / Drive PDF / OneDrive(長尾、格式雜)——只收 2022–2026 Google Sheets。
- 輪霸西濱(查無結構化成績,只剩 2012–2015 舊檔)。
- focusline 團體接力組(team relay,結構不同)。
- 來源名次(totalSort / Sheets 名次)——一律不採用,依時間重排。

## 風險與緩解

- **taiwanbike 欄位漂移**(最大風險):寬鬆同義詞對映 + 逐場容錯,單場解析失敗記錄並跳過,不中斷整體。
- **gunTime/成績 語意**:實作時逐場 sanity-check 時間範圍(300–600km 應落在數小時~24h);異常場記錄。
- **Sheets 連結分享可能失效/變私有**:抓取失敗跳過並記錄;清單頁為穩定枚舉來源。
- **focusline Cloudflare**:目前 pass-through 無挑戰;保留瀏覽器 UA、禮貌間隔;若日後收緊再評估。
