# tw-cycling-data Public API (v1)

唯讀靜態 JSON API。Base URL:`https://tw-cycling-data.vercel.app/data/v1`
入口 manifest:[`/data/v1/manifest.json`](https://tw-cycling-data.vercel.app/data/v1/manifest.json)

所有回應帶 `Access-Control-Allow-Origin: *`,可直接於瀏覽器/notebook 跨網域 fetch。

## 隱私 (PDPA)

僅提供去識別化資料:遮罩姓名 `name_masked`(如 `李○明`)、加鹽雜湊 `athlete_id`、`has_uci` 布林。**不提供真實姓名**。

## 授權

資料以 **CC BY 4.0** 釋出。使用請標註來源 `tw-cycling-data`(https://github.com/TTigger/tw-cycling-data)並連回專案。

## 端點

| 路徑 | 類型 | 說明 |
|---|---|---|
| `manifest.json` | meta | 版本、資料集指標、端點目錄 |
| `overview.json` | meta | 全站 KPI、熱度、趨勢、性別組成 |
| `races.json` | index | 賽事索引:`rk`(race_key)、`y`(年)、`rn`(名稱)、`s`(系列)、`rows`(完賽人數)、`file`(明細檔名) |
| `race/{race_key}.json` | detail | 單場排行榜(已依分組+完賽時間重排) |
| `athletes.json` | index | 選手索引(≥2 場):`id`、`nm`(遮罩名)、`tm`(車隊)、`n`/`ny`/`best` |
| `athlete/{athlete_id}.json` | detail | 單一選手去識別化生涯成績 |
| `teams.json` | index | 車隊索引 |
| `team/{team_id}.json` | detail | 單一車隊成員與戰績 |
| `series.json` | index | 賽事系列彙整 |
| `benchmarks.json` | index | 各賽事(跨年)依分齡/性別/分組 cohort 的完賽時間百分位斷點 |
| `coverage.json` | meta | 來源/賽曆涵蓋與缺漏分類 |

> `race/{race_key}.json` 的檔名為 `races.json` 中該筆的 `file` 欄位值(形如 `<race_key>__<year>`)。

## 主要欄位 schema

**races.json[]**:`rk: string`、`y: number|null`、`rn: string`、`s: string|null`、`rows: number`、`multi_year: bool`、`has_team: bool`、`file: string`、`completion?: {fin,total,rate,counts}`。

**athletes.json[]**:`id: string`、`nm: string`(遮罩)、`n: number`(場次)、`ny: number`(年數)、`best: number|null`、`uci: bool`、`tm?: string|null`(代表車隊)。

**race/{race_key}.json** rows:`rank`、`bib`、`name`(遮罩)、`cat`、`g`(M/F/null)、`ag`(分齡)、`team`、`t`(完賽秒)、`label`。

## benchmarks.json

對標工具的資料。鍵為 `race_key`;每場跨所有年份彙整。`groups` 依 `result_label`(距離/項目)分層——同一賽事的不同距離/項目**不混比**;cohort(all/age/cat)在**各群組內**計算。

```jsonc
{
  "<race_key>": {
    "rn": "桃園繞圈賽",
    "groups": {
      "公路繞圈賽": {
        "years": [2023, 2024],
        "cohorts": {
          "all":           { "n": 129, "type": "all", "label": "全部完賽者",  "bp": [t0, …, t100] },
          "age:40-49":     { "n": 40,  "type": "age", "label": "40-49 歲",    "bp": [...] }
        }
      },
      "個人計時賽": { "years": [...], "cohorts": { "all": { ... } } }
    }
  }
}
```

- cohort key:`all` / `age:<band>` / `age:<band>|g:<M|F>` / `cat:<division>`;`type` ∈ {all, age, cat}。
- `bp` = 101 個完賽秒數斷點(各百分位時間,升冪;`bp[0]`=最快、`bp[50]`=中位、`bp[100]`=最慢)。
- 查百分位:「你贏過(比你慢的)%」= `bp` 中嚴格比你慢的比例 × 100。
- 僅收每 cohort `n>=20`、且該賽事有 `all` cohort 者。去識別化純聚合,無個資。

## 範例

curl:

```bash
curl https://tw-cycling-data.vercel.app/data/v1/manifest.json
curl https://tw-cycling-data.vercel.app/data/v1/races.json | jq '.[0]'
```

Python:

```python
import requests
BASE = "https://tw-cycling-data.vercel.app/data/v1"
races = requests.get(f"{BASE}/races.json").json()
first = races[0]
detail = requests.get(f"{BASE}/race/{first['file']}.json").json()
print(first["rn"], "->", len(detail["rows"]), "finishers")
```

## 版本與穩定性

路徑前綴 `v1` 在重大不相容變更前不變。指標見 `manifest.json` 的 `stats`(由建置產物推導)。
