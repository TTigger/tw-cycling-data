# tw-cycling-data 開放資料集

台灣公路自行車賽事成績的**去識別化**逐筆資料集:8 個來源正規化彙整,147,609 筆、2009–2026。供研究與分析使用。

- **授權**:[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。使用請標註來源 `tw-cycling-data`(https://github.com/TTigger/tw-cycling-data)。
- **下載**:見本專案 [GitHub Releases](https://github.com/TTigger/tw-cycling-data/releases)(`tw-cycling-results.csv.gz` / `.json.gz` + `datapackage.json`)。
- **English**: see [DATASET.en.md](DATASET.en.md).

## 隱私

本資料集為**已公開賽事成績**之去識別化彙整:僅含遮罩姓名 `name_masked`(如 李○明),**已刪除**外部識別碼(`uci_id`、`tsu_rider_id`、`source_url`)與 `bib`、`nationality`。若你是當事人並希望移除你的資料,請至 [GitHub Issues](https://github.com/TTigger/tw-cycling-data/issues) 申請。

## 欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `race_key` | string | 賽事鍵;同一賽事跨年共用 |
| `year` | integer | 年份 |
| `date` | string | 賽事日期 YYYY-MM-DD(約 69% 有) |
| `region` | string | 縣市層級地區(約 38% 有) |
| `series` | string | 賽事系列 |
| `race_name_canonical` | string | 正規化賽事名稱 |
| `race_type` | string | 賽別:road / criterium / KOM / TT 等 |
| `race_class` | string | 賽事分類 |
| `result_label` | string | 成績組別標籤 |
| `category_raw` | string | 原始分組字串 |
| `gender` | string | 性別 M/F(約 52% 有) |
| `age_band` | string | 分齡帶 U19/19-29/30-39/40-49/50-59/60+(約 36% 有) |
| `age_group` | string | 細分齡 |
| `rank_overall` | integer | 總名次(認證賽多為空) |
| `finish_seconds` | number | 完賽秒數 |
| `finish_time` | string | 完賽時間字串 |
| `splits` | string | 分段時間(JSON;約 9% 有) |
| `team` | string | 車隊(約 46% 有) |
| `name_masked` | string | 遮罩姓名(如 李○明) |
| `source_platform` | string | 來源平台 |

## 載入

```python
import pandas as pd
df = pd.read_csv("tw-cycling-results.csv.gz")   # gzip 自動處理
```

## 引用

見 [CITATION.cff](CITATION.cff)(GitHub 右側「Cite this repository」)。

## 發布(維護者)

```bash
python scrapers/build_dataset.py
gh release create dataset-vYYYY.MM.DD data/dist/* \
  --title "Dataset YYYY.MM.DD" --notes "去識別化逐筆成績,CC BY 4.0。"
```
