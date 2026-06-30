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
| `coverage.json` | meta | 來源/賽曆涵蓋與缺漏分類 |

> `race/{race_key}.json` 的檔名為 `races.json` 中該筆的 `file` 欄位值(形如 `<race_key>__<year>`)。

## 主要欄位 schema

**races.json[]**:`rk: string`、`y: number|null`、`rn: string`、`s: string|null`、`rows: number`、`multi_year: bool`、`has_team: bool`、`file: string`、`completion?: {fin,total,rate,counts}`。

**athletes.json[]**:`id: string`、`nm: string`(遮罩)、`n: number`(場次)、`ny: number`(年數)、`best: number|null`、`uci: bool`、`tm?: string|null`(代表車隊)。

**race/{race_key}.json** rows:`rank`、`bib`、`name`(遮罩)、`cat`、`g`(M/F/null)、`ag`(分齡)、`team`、`t`(完賽秒)、`label`。

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
