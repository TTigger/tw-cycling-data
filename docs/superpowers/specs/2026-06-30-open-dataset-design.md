# 開放資料集發布(Open Dataset Release)— 設計 spec

**日期**:2026-06-30
**狀態**:已核可,待寫實作計畫
**範圍**:把去識別化的逐筆成績資料打包成**版本化、附 schema 與授權的可下載開放資料集**,經 **GitHub Releases** 發布。對標 jenslemb/cyclingdata 等「可下載資料集」,提高被引用與開源貢獻。路線圖 Feature 4(最後一個)。

## 背景與動機

`master.public.json`(119MB、147,609 筆、28 欄)已去識別化但僅供內部 build,未對外發布。把它包成標準開放資料集(CSV/JSON + datapackage + 授權)讓研究者可下載引用,是「被看見」路線圖的收尾。

**隱私評估(已與 owner 討論並定案)**:雖然成績原本已公開且多為事實,但**跨賽事彙整、可一鍵下載**會提高再識別性,且 `uci_id`/`tsu_rider_id` 是可串外部庫的穩定識別碼。故採**保守版**:刪除外部識別碼,保留與網站現有公開程度一致的去識別化欄位 + `name_masked`,並附 opt-out 聯絡。(非法律意見;發布前 owner 自行斟酌來源站 ToS。)

## 已核可的決策

1. **隱私/欄位**:保守版(見下)。
2. **格式**:`CSV(gzip)` + `JSON(gzip)`。
3. **管道**:**GitHub Releases**(版本化資產);**不**在 Vercel 另放一份。
4. **授權**:**CC BY 4.0** + attribution + opt-out(GitHub Issues)。
5. **發布動作**:build 只產檔;實際 `gh release create` 為對外發布,**由 owner 確認後執行**(SDD 過程不自動發布)。

## 欄位(保守版)

來源 28 欄 → **發布 20 欄**:
`race_key, year, date, region, series, race_name_canonical, race_type, race_class, result_label, category_raw, gender, age_band, age_group, rank_overall, finish_seconds, finish_time, splits, team, name_masked, source_platform`

**刪除 8 欄**:
- 再識別/無用:`uci_id`、`tsu_rider_id`、`source_url`、`bib`、`nationality`
- 內部/冗餘:`scraped_at`、`source_format`、`race_name_raw`
- (`name_raw` 本就不存在於 public)

**安全閘**:一個測試斷言**刪除欄一律不出現在輸出**,且輸出欄集合 == `PUBLISH_COLUMNS`。

## 元件設計(單一職責)

### 1. `scrapers/dataset.py`(純函式,可測)
- `PUBLISH_COLUMNS`(上述 20 欄,固定順序)、`DROP_COLUMNS`(明列被刪 8 欄,供測試 + 自我文件)。
- `project_row(row) -> dict`:回只含 `PUBLISH_COLUMNS` 的 dict(缺欄補 None);不得含任何 `DROP_COLUMNS` 鍵。
- `csv_value(v) -> str`:把值(含 `splits` 之 list/None)轉成 CSV 安全字串(list → JSON 字串;None → 空)。

### 2. `scrapers/build_dataset.py`
- 串流 `common.iter_records(master.public.json)`,逐筆 `project_row` → 寫:
  - `data/dist/tw-cycling-results.csv.gz`(`csv` + `gzip`;header = PUBLISH_COLUMNS)
  - `data/dist/tw-cycling-results.json.gz`(逐筆 dict 陣列;`gzip`)
  - `data/dist/datapackage.json`(見下)
  - `data/dist/CHECKSUMS.txt`(各檔 `sha256  filename`)
- `data/dist/` 為 gitignored(大檔/release 資產)。
- 印出筆數與各檔大小。

### 3. `datapackage.json`(Frictionless Data 規格,由 build 產生)
- `name: "tw-cycling-results"`、`title`、`version`(日期式 `YYYY.MM.DD`,由 build 當下 `datetime.now().strftime("%Y.%m.%d")`)、`licenses: [{"name":"CC-BY-4.0","path":"https://creativecommons.org/licenses/by/4.0/"}]`、`attribution`、`homepage`、`contact`(GitHub Issues URL)。
- `resources`:csv.gz / json.gz 各一,含 `path`、`format`、`bytes`、`hash`(sha256)。
- `resources[0].schema.fields`:每欄 `{name, type, description}`(type:string/integer/number/…;PUBLISH_COLUMNS 全部)。
- `count`(總筆數)。

### 4. `DATASET.md`(中文)+ `DATASET.en.md`(英文全文)+ `CITATION.cff`(committed,人讀/引用)
`DATASET.md`(中文,主文件):
- 一句話定位 + 規模(147,609 筆、年份範圍、來源平台數)。
- 欄位表(name / type / 說明)。
- **授權**:CC BY 4.0;引用方式(文字 + 指向 CITATION.cff)。
- **隱私聲明**:已公開賽事成績之去識別化彙整、供研究用;已刪除外部識別碼;**opt-out**:到 GitHub Issues(`https://github.com/TTigger/tw-cycling-data/issues`)申請移除。
- **載入範例**:`pandas.read_csv("tw-cycling-results.csv.gz")` 一段。
- **發布流程**(供 owner):`python scrapers/build_dataset.py` → `gh release create dataset-vYYYY.MM.DD data/dist/* --title … --notes …`。

`DATASET.en.md`(英文全文):與 `DATASET.md` 內容平行的英文版(定位/規模/欄位表/授權/隱私+opt-out/載入範例),供國際研究者;`DATASET.md` 與 `README` 互連 `DATASET.en.md`。

`CITATION.cff`(標準引用 metadata,GitHub 顯示「Cite this repository」):`cff-version`、`title`、`authors`、`license: CC-BY-4.0`、`url`(repo)、`type: dataset`、`version`(日期式)、`date-released`。直接服務「被引用」目標。

### 5. README「Open Dataset」區段(committed)
- 連到 `DATASET.md` + 最新 Release;一句授權 + 規模。中英文 README 各一段。

## 版本與發布

- 版本 = `YYYY.MM.DD`(datapackage.version + release tag `dataset-vYYYY.MM.DD`)。
- 完整重出(非增量;YAGNI)。
- **發布為對外動作**:本案只負責「可重現地產出資產 + 文件 + 發布指令」;`gh release create` 由 owner 確認後執行(或執行時逐項確認)。

## 測試(照 dev-workflow)

- `scrapers/test_dataset.py`:
  - `project_row` 輸出鍵集合 == `PUBLISH_COLUMNS`;**任一 `DROP_COLUMNS` 鍵都不在輸出**(關鍵安全測試,逐欄斷言 `uci_id`/`tsu_rider_id`/`source_url`/`bib`/`nationality`/`name_raw` 不存在)。
  - 缺欄補 None;`csv_value` 對 list(splits)/None 的處理。
- `scrapers/test_build_dataset.py`(或 smoke):用小型 fake master(tmp)跑 `build_dataset` 的核心寫出函式 → 斷言 csv header == PUBLISH_COLUMNS、datapackage `count` == 列數、`resources` 含 sha256、CSV 不含被刪欄名。
- 流程:`python -m pytest scrapers/` → 實跑 `build_dataset.py` → 抽驗(147,609 筆、`zcat tw-cycling-results.csv.gz | head -1` 的 header 無被刪欄、檔案大小合理、CHECKSUMS 正確)→ commit(僅 dataset.py/build_dataset.py/測試/DATASET.md/README/.gitignore,**不含 data/dist 大檔**)。

## 風險與緩解

- **誤含敏感欄**:安全測試逐欄斷言被刪欄不存在;build 以 `PUBLISH_COLUMNS` 白名單投影(白名單而非黑名單,預設安全)。
- **檔案過大上 git**:`data/dist/` gitignored;只發 Release。
- **datapackage 與實際不一致**:`count`/`hash`/`bytes` 一律由產物計算,不寫死;測試斷言一致。
- **發布為不可逆對外動作**:不自動發布;owner 確認。
- **ToS/法律不確定**:DATASET.md 標明去識別化 + opt-out;非法律意見,owner 自行斟酌。

## YAGNI(不做)

- Parquet;Vercel 直連一份;自動發布;增量/差異發布。(DATASET 中英文皆出 + CITATION.cff,見元件 4。)

## 未來待辦(本次不做,記錄備查)

- 若需求出現,加 Parquet 或 Hugging Face Datasets 鏡像。
- 加自動化發布(需 CI + 對外授權的明確流程)。
