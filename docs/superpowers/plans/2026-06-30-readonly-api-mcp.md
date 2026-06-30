# 版本化唯讀 API + Python MCP server 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把既有靜態 JSON 分片正式化為版本化 `/data/v1/` 公開唯讀 API(含 CORS、manifest、文件),並新增一個即時讀線上 API 的 Python MCP server。

**Architecture:** 兩個獨立元件。(A) 後端 build 腳本輸出改至 `web/public/data/v1/`、前端讀取改 base、加 `web/vercel.json`(CORS)、加 `/data/v1/manifest.json`、加 `docs/API.md`。(B) `mcp-server/` Python 套件,純函式(查詢)+ HTTP client + FastMCP server 三層,即時讀線上 v1 端點。

**Tech Stack:** Python 3(scrapers + MCP,官方 `mcp` SDK + `httpx`)、Astro + React + TypeScript(前端)、Vercel(靜態部署 + headers)、pytest、vitest。

## Global Constraints

- **PDPA**:API 與 MCP 僅暴露 `name_masked`、salted `athlete_id`、`has_uci`;絕不暴露 `name_raw`。不新增任何個資欄位。
- **乾淨切換**:只輸出 `/data/v1/`,不保留舊 `/data/` 路徑相容層。
- **manifest 指標由產物推導**:`manifest.json` 的 `stats` 不可寫死,須由實際建置產物計算,並有測試斷言一致。
- **MCP 資料源**:即時讀線上 API;預設 base URL `https://tw-cycling-data.vercel.app/data/v1`,可由環境變數 `TWCD_API_BASE` 覆寫。
- **MCP 技術**:Python,官方 `mcp` SDK(FastMCP)+ `httpx`;以 `uvx`/`uv run` 可執行。**不做 Node/TypeScript MCP**(YAGNI,列未來待辦)。
- **資料授權**:CC BY 4.0(標註來源 `tw-cycling-data` 並連回專案);於 `manifest.license`、`docs/API.md`、README 一致標示。
- **DRY**:所有讀寫 `web/public/data` 的腳本一律改用單一常數 `common.PUBLIC_DATA_DIR`。
- 既有測試流程(`dev-workflow`):`python -m pytest scrapers/ mcp-server/` 全綠、`astro check` clean、build 成功、瀏覽器抽查;每個 task 自己 commit。

---

## File Structure

**修改(路徑遷移,Task 1):**
- `scrapers/common.py` — 新增 `import os` 與 `PUBLIC_DATA_DIR` 常數。
- 7 個資料寫入腳本:`build_viz.py`、`build_athletes.py`、`build_teams.py`、`build_series.py`、`build_insights.py`、`build_race_dna.py`、`build_difficulty.py` — `OUT` 改用常數。
- `build_og.py`(`DATA` 讀)、`build_fonts.py`(glob 讀)、`discover.py`(`WEB_DIR` 寫 coverage)、`overseas_runnet.py`(`PUB_DIR` 寫 overseas)— 改用常數。
- 前端:`web/src/lib/data-load.ts`(base)、`web/src/pages/athletes/[id].astro`、`web/src/pages/race/[slug].astro`(靜態 import)。
- 實體資料夾:`git mv web/public/data/*` → `web/public/data/v1/`。

**新增:**
- `web/vercel.json` — CORS + cache headers(Task 2)。
- `scrapers/build_manifest.py` + `scrapers/test_build_manifest.py` — manifest 產生器(Task 3)。
- `docs/API.md`(Task 4)。
- `mcp-server/` 套件(Task 5–7):`pyproject.toml`、`tw_cycling_data_mcp/{__init__,query,client,server}.py`、`tests/`、`README.md`。

---

## Task 1: 路徑遷移到 `/data/v1/`

把所有讀寫 `web/public/data` 的腳本與前端改成版本化 `v1/` 子目錄,並用 `git mv` 搬移既有產物與輸入(保留 `climb_profiles.json` 等被讀取的輸入檔與 git 歷史)。交付物:網站在 `/data/v1/` 上完整運作。

**Files:**
- Modify: `scrapers/common.py`(加 `import os`、`PUBLIC_DATA_DIR`)
- Modify: `scrapers/build_viz.py:18`、`build_athletes.py:33`、`build_teams.py:28`、`build_series.py:27`、`build_insights.py:22`、`build_race_dna.py:33`、`build_difficulty.py:32`(`OUT`)
- Modify: `scrapers/build_og.py:18`(`DATA`)、`build_fonts.py:38`(`pats`)、`discover.py:32`(`WEB_DIR`)、`overseas_runnet.py:28`(`PUB_DIR`)
- Modify: `web/src/lib/data-load.ts:4`、`web/src/pages/athletes/[id].astro:4`、`web/src/pages/race/[slug].astro:4`
- Move: `web/public/data/*` → `web/public/data/v1/*`
- Test: `scrapers/test_common.py`(新增或追加)

**Interfaces:**
- Produces: `common.PUBLIC_DATA_DIR`(str,絕對化前為 `<scrapers>/../web/public/data/v1`),後續 Task 3 的 `build_manifest.py` 也用它。

- [ ] **Step 1: Write the failing test**

新增 `scrapers/test_common.py`(若已存在則追加此測試):

```python
import os
import common


def test_public_data_dir_points_at_v1():
    # 必須指向 web/public/data/v1(版本化命名空間)
    parts = os.path.normpath(common.PUBLIC_DATA_DIR).split(os.sep)
    assert parts[-3:] == ["public", "data", "v1"], parts
    # 必須以 scrapers/ 為基準回推到 repo 的 web/ 底下
    assert "web" in parts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_common.py::test_public_data_dir_points_at_v1 -v`
Expected: FAIL with `AttributeError: module 'common' has no attribute 'PUBLIC_DATA_DIR'`

- [ ] **Step 3: Add the constant to `common.py`**

在 `scrapers/common.py` 的 import 區把 `import os` 加上(目前只有 `import json, re, time, requests`),並在 `UA = (...)` 之後新增:

```python
# Single source of truth for the versioned public API output directory.
# All build_*/discover/overseas scripts write here; the frontend reads /data/v1/.
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "public", "data", "v1")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_common.py::test_public_data_dir_points_at_v1 -v`
Expected: PASS

- [ ] **Step 5: Move existing data into `v1/` with git mv**

於 repo 根執行(`climb_profiles.json`、`coverage.json`、`overseas/` 等被讀取的輸入也一併保留搬移):

```bash
mkdir -p web/public/data/v1
git mv web/public/data/*.json web/public/data/v1/
for d in athlete race team overseas; do git mv "web/public/data/$d" "web/public/data/v1/$d"; done
ls web/public/data/v1 | head
```

Expected: 所有 `*.json` 與 `athlete/ race/ team/ overseas/` 都在 `v1/` 下;`web/public/data/` 僅剩 `v1/`。

- [ ] **Step 6: Point the 7 data-writing build scripts at the constant**

在每個檔案的 `OUT = os.path.join(HERE, "..", "web", "public", "data")` 改為:

```python
OUT = common.PUBLIC_DATA_DIR
```

檔案與行:`build_viz.py:18`、`build_athletes.py:33`、`build_teams.py:28`、`build_series.py:27`、`build_insights.py:22`、`build_race_dna.py:33`、`build_difficulty.py:32`。確認每個檔案頂部已 `import common`(多數已 import;若無則加上 `import common`,並確保有 `sys.path.insert(0, os.path.dirname(__file__))` 或同目錄可 import)。`os.makedirs(OUT, exist_ok=True)` 若原本沒有,於寫檔前補上以確保 `v1/` 存在。

- [ ] **Step 7: Point the reader/auxiliary scripts at the constant**

- `build_og.py:18`:`DATA = os.path.join(HERE, "..", "web", "public", "data")` → `DATA = common.PUBLIC_DATA_DIR`(確認檔案 `import common`)。
- `build_fonts.py:38`:`pats = [os.path.join(ROOT, "web", "public", "data", "**", "*.json")]` → `pats = [os.path.join(common.PUBLIC_DATA_DIR, "**", "*.json")]`(確認 `import common`)。
- `discover.py:32`:`WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "public", "data")` → `WEB_DIR = common.PUBLIC_DATA_DIR`。
- `overseas_runnet.py:28`:`PUB_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "public", "data", "overseas")` → `PUB_DIR = os.path.join(common.PUBLIC_DATA_DIR, "overseas")`。

- [ ] **Step 8: Point the frontend at `/data/v1/`**

`web/src/lib/data-load.ts`:把第 4 行

```ts
const base = import.meta.env.BASE_URL.replace(/\/$/, "");
```

改為(新增 `API` 常數):

```ts
const base = import.meta.env.BASE_URL.replace(/\/$/, "");
// Versioned public API namespace. All reads go through /data/v1/.
const API = `${base}/data/v1`;
```

然後把檔案內所有 `` `${base}/data/ `` 取代為 `` `${API}/ ``(約 20 處 fetch;`overseas/index.json`、`overseas/${file}.json`、`race/${file}.json`、`athlete/${id}.json`、`team/${id}.json` 等子路徑一併涵蓋)。確認檔案內不再殘留 `${base}/data/`。

兩個 `.astro` 靜態 import:
- `web/src/pages/athletes/[id].astro:4`:`../../../public/data/athletes.json` → `../../../public/data/v1/athletes.json`
- `web/src/pages/race/[slug].astro:4`:`../../../public/data/races.json` → `../../../public/data/v1/races.json`

- [ ] **Step 9: Rebuild data into v1 and verify frontend builds**

Run:
```bash
python scrapers/build_viz.py && python scrapers/build_athletes.py && python scrapers/build_teams.py && python scrapers/build_series.py && python scrapers/build_insights.py && python scrapers/build_race_dna.py && python scrapers/build_difficulty.py
cd web && npm run build
```
Expected: build 腳本印出寫入路徑含 `web/public/data/v1`;`astro build` 成功、無「fetch 404 / import not found」錯誤。
(`npm run build` 等同 astro check + build;若專案分開,先 `npx astro check`。)

- [ ] **Step 10: Run the Python tests**

Run: `python -m pytest scrapers/ -q`
Expected: 全綠(含新 `test_common.py`);既有測試不受影響。

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "refactor(api): migrate public data to versioned /data/v1/ namespace

- common.PUBLIC_DATA_DIR single source of truth
- all build/discover/overseas scripts + frontend read/write /data/v1/
- git mv preserves curated inputs (climb_profiles.json) and history"
```

---

## Task 2: CORS + 快取 header(`web/vercel.json`)

讓第三方可跨網域 fetch v1 端點,並讓 CDN 快取 JSON。交付物:部署後 `/data/v1/*.json` 回應帶 `Access-Control-Allow-Origin: *`。

**Files:**
- Create: `web/vercel.json`
- Test: `scrapers/test_vercel_config.py`(用 Python 驗證 JSON 結構,免額外 JS 工具鏈)

**Interfaces:**
- Produces: 部署層 header 設定(無程式介面)。

- [ ] **Step 1: Write the failing test**

新增 `scrapers/test_vercel_config.py`:

```python
import json
import os

VERCEL = os.path.join(os.path.dirname(__file__), "..", "web", "vercel.json")


def test_vercel_sets_cors_and_cache_for_data():
    with open(VERCEL, encoding="utf-8") as f:
        cfg = json.load(f)
    headers = cfg["headers"]
    # 找到對 /data/ 路徑的設定
    data_rule = next(h for h in headers if "/data/" in h["source"])
    kv = {x["key"]: x["value"] for x in data_rule["headers"]}
    assert kv["Access-Control-Allow-Origin"] == "*"
    assert "max-age" in kv["Cache-Control"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_vercel_config.py -v`
Expected: FAIL(`FileNotFoundError`,尚未建立 `web/vercel.json`)

- [ ] **Step 3: Create `web/vercel.json`**

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "headers": [
    {
      "source": "/data/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET, OPTIONS" },
        { "key": "Cache-Control", "value": "public, max-age=3600, stale-while-revalidate=86400" }
      ]
    }
  ]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_vercel_config.py -v`
Expected: PASS

- [ ] **Step 5: Verify Vercel root + deploy note**

確認 Vercel 專案的 Root Directory 是否為 `web/`(`gh api repos/TTigger/tw-cycling-data` 無此資訊;由 owner 確認或看 Vercel 設定)。若 root 為 `web/`,`web/vercel.json` 正確;若 root 為 repo 根,需把檔案移到 repo 根並把 `source` 改為 `/data/(.*)` 對應實際輸出路徑。於 report 註明此假設,並列出部署後驗證指令:
```bash
curl -sI https://tw-cycling-data.vercel.app/data/v1/manifest.json | grep -i access-control-allow-origin
```
(部署後由 owner 執行確認;非本 task 阻塞項。)

- [ ] **Step 6: Commit**

```bash
git add web/vercel.json scrapers/test_vercel_config.py
git commit -m "feat(api): CORS + cache headers for /data/ (public API cross-origin access)"
```

---

## Task 3: `manifest.json` 產生器

產生 `/data/v1/manifest.json`(版本、指標、端點目錄),指標由實際產物推導。交付物:`build_manifest.py` 寫出 manifest,測試斷言其 stats 與產物一致。

**Files:**
- Modify: `scrapers/build_viz.py`(在 overview 的 kpi 加 `sources` 計數)
- Create: `scrapers/build_manifest.py`
- Test: `scrapers/test_build_manifest.py`

**Interfaces:**
- Consumes: `common.PUBLIC_DATA_DIR`(Task 1);`v1/overview.json`、`v1/races.json`、`v1/athletes.json`、`v1/teams.json`。
- Produces: `build_manifest.compute_manifest(data_dir: str) -> dict`(純函式,讀 data_dir 內產物回 manifest dict);`main()` 寫 `v1/manifest.json`。

- [ ] **Step 1: Add `sources` count to overview kpi in `build_viz.py`**

`build_viz.py` 已逐筆讀 `master.public.json`(`IN`)。在彙整 kpi 的區段(目前產出 `{records, races, series, minYear, maxYear}` 的 `overview["kpi"]`)蒐集 `source_platform` 的相異集合並加入計數。於迴圈中累計:

```python
sources_seen = set()
# ... 在逐筆迴圈內:
sources_seen.add(r.get("source_platform"))
# ... 組 kpi 時:
kpi["sources"] = len([s for s in sources_seen if s])
```

(找到現有建立 `kpi` 的 dict,新增 `"sources"` 鍵;沿用該處既有的 records/minYear/maxYear 計算變數。)

- [ ] **Step 2: Write the failing test**

新增 `scrapers/test_build_manifest.py`:

```python
import json
import os
import build_manifest


def _write(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def test_compute_manifest_derives_stats_from_products(tmp_path):
    d = str(tmp_path)
    _write(os.path.join(d, "overview.json"),
           {"kpi": {"records": 146475, "races": 161, "series": 23,
                    "minYear": 2009, "maxYear": 2026, "sources": 8}})
    _write(os.path.join(d, "races.json"), [{"rk": "a"}, {"rk": "b"}])
    _write(os.path.join(d, "athletes.json"), [{"id": "x"}, {"id": "y"}, {"id": "z"}])
    _write(os.path.join(d, "teams.json"), [{"id": "t"}])

    m = build_manifest.compute_manifest(d)

    assert m["api_version"] == "v1"
    assert m["license"] == "CC-BY-4.0"
    # 指標由產物推導,不可寫死
    assert m["stats"]["records"] == 146475
    assert m["stats"]["sources"] == 8
    assert m["stats"]["year_min"] == 2009 and m["stats"]["year_max"] == 2026
    assert m["stats"]["races"] == 2          # len(races.json)
    assert m["stats"]["athletes"] == 3       # len(athletes.json)
    assert m["stats"]["teams"] == 1          # len(teams.json)
    # 端點目錄涵蓋明細樣板路徑
    paths = {e["path"] for e in m["endpoints"]}
    assert "athlete/{athlete_id}.json" in paths
    assert "race/{race_key}.json" in paths
    assert "manifest.json" in paths
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest scrapers/test_build_manifest.py -v`
Expected: FAIL(`ModuleNotFoundError: No module named 'build_manifest'`)

- [ ] **Step 4: Implement `build_manifest.py`**

```python
# -*- coding: utf-8 -*-
"""Generate /data/v1/manifest.json: api version, dataset stats (derived from
build products, never hard-coded), and the endpoint catalog. Run AFTER the
other build_* scripts so the index files exist."""
import json
import os
import common

ENDPOINTS = [
    {"path": "manifest.json", "kind": "meta", "description": "This file: version, stats, endpoint catalog."},
    {"path": "overview.json", "kind": "meta", "description": "Dataset KPIs, heatmap, trend, gender composition."},
    {"path": "races.json", "kind": "index", "description": "Race index: race_key, year, name, series, finisher rows."},
    {"path": "race/{race_key}.json", "kind": "detail", "description": "One race leaderboard (re-ranked by category + finish time)."},
    {"path": "athletes.json", "kind": "index", "description": "Athlete index (>=2 results): masked name, team, counts."},
    {"path": "athlete/{athlete_id}.json", "kind": "detail", "description": "One athlete's de-identified result history."},
    {"path": "teams.json", "kind": "index", "description": "Team index: id, name, roster size."},
    {"path": "team/{team_id}.json", "kind": "detail", "description": "One team's roster + record."},
    {"path": "series.json", "kind": "index", "description": "Race series aggregates."},
    {"path": "coverage.json", "kind": "meta", "description": "Source/calendar coverage and gap triage."},
]


def _read_json(data_dir, name):
    with open(os.path.join(data_dir, name), encoding="utf-8") as f:
        return json.load(f)


def compute_manifest(data_dir):
    kpi = _read_json(data_dir, "overview.json")["kpi"]
    races = _read_json(data_dir, "races.json")
    athletes = _read_json(data_dir, "athletes.json")
    teams = _read_json(data_dir, "teams.json")
    return {
        "api_version": "v1",
        "dataset": "tw-cycling-data",
        "homepage": "https://tw-cycling-data.vercel.app/",
        "license": "CC-BY-4.0",
        "attribution": "tw-cycling-data (https://github.com/TTigger/tw-cycling-data)",
        "stats": {
            "records": kpi["records"],
            "races": len(races),
            "series": kpi.get("series"),
            "athletes": len(athletes),
            "teams": len(teams),
            "sources": kpi.get("sources"),
            "year_min": kpi["minYear"],
            "year_max": kpi["maxYear"],
        },
        "endpoints": ENDPOINTS,
    }


def main():
    m = compute_manifest(common.PUBLIC_DATA_DIR)
    out = os.path.join(common.PUBLIC_DATA_DIR, "manifest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print(f"manifest: records={m['stats']['records']} races={m['stats']['races']} "
          f"athletes={m['stats']['athletes']} -> {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest scrapers/test_build_manifest.py -v`
Expected: PASS

- [ ] **Step 6: Generate the real manifest end-to-end**

Run:
```bash
python scrapers/build_viz.py && python scrapers/build_manifest.py
python -c "import json;m=json.load(open('web/public/data/v1/manifest.json',encoding='utf-8'));print(m['stats'])"
```
Expected: 印出真實 stats(records ~146k、races ~161、athletes ~29k 等級的合理數字、sources=8)。

- [ ] **Step 7: Commit**

```bash
git add scrapers/build_viz.py scrapers/build_manifest.py scrapers/test_build_manifest.py web/public/data/v1/manifest.json web/public/data/v1/overview.json
git commit -m "feat(api): /data/v1/manifest.json with product-derived stats + endpoint catalog"
```

---

## Task 4: API 文件(`docs/API.md`)+ README Public API 區段

讓 API 可被理解與引用。交付物:`docs/API.md` + README 中英文各一段。

**Files:**
- Create: `docs/API.md`
- Modify: `README.md`、`README.en.md`
- Test: `scrapers/test_api_docs.py`(斷言文件與 manifest 授權一致、列出全部端點)

**Interfaces:**
- Consumes: `build_manifest.ENDPOINTS`(端點清單)、`manifest.license`。

- [ ] **Step 1: Write the failing test**

新增 `scrapers/test_api_docs.py`:

```python
import os
import build_manifest

DOC = os.path.join(os.path.dirname(__file__), "..", "docs", "API.md")


def test_api_doc_lists_every_endpoint_and_license():
    with open(DOC, encoding="utf-8") as f:
        text = f.read()
    assert "CC-BY-4.0" in text or "CC BY 4.0" in text
    for ep in build_manifest.ENDPOINTS:
        assert ep["path"] in text, f"API.md missing endpoint {ep['path']}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_api_docs.py -v`
Expected: FAIL(`FileNotFoundError`)

- [ ] **Step 3: Write `docs/API.md`**

寫入下列內容(端點表須涵蓋 `build_manifest.ENDPOINTS` 的每個 `path`):

````markdown
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
````

- [ ] **Step 4: Add Public API section to both READMEs**

`README.md` 增一段(置於功能總覽附近):

```markdown
## Public API

唯讀 JSON API(CC BY 4.0,去識別化)。Base:`https://tw-cycling-data.vercel.app/data/v1`,入口 [`manifest.json`](https://tw-cycling-data.vercel.app/data/v1/manifest.json)。端點與 schema 見 [`docs/API.md`](docs/API.md)。也提供 Python MCP server(見 [`mcp-server/`](mcp-server/))。
```

`README.en.md` 對應英文段:

```markdown
## Public API

Read-only JSON API (CC BY 4.0, de-identified). Base: `https://tw-cycling-data.vercel.app/data/v1`, entry [`manifest.json`](https://tw-cycling-data.vercel.app/data/v1/manifest.json). Endpoints and schema in [`docs/API.md`](docs/API.md). A Python MCP server is also provided (see [`mcp-server/`](mcp-server/)).
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest scrapers/test_api_docs.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/API.md README.md README.en.md scrapers/test_api_docs.py
git commit -m "docs(api): API.md endpoint+schema reference and README Public API section"
```

---

## Task 5: MCP 純函式(`query.py`)

可單測的查詢邏輯,與 HTTP 隔離。交付物:`normalize_search`、`match_athletes`、`filter_races` + 測試。

**Files:**
- Create: `mcp-server/tw_cycling_data_mcp/__init__.py`(空檔)
- Create: `mcp-server/tw_cycling_data_mcp/query.py`
- Create: `mcp-server/tests/test_query.py`
- Create: `mcp-server/pyproject.toml`(最小,供 pytest 找到套件;Task 7 補完 entry point)

**Interfaces:**
- Produces:
  - `normalize_search(s: str) -> str`
  - `match_athletes(index: list[dict], query: str, limit: int = 20) -> list[dict]`
  - `filter_races(index: list[dict], year: int | None, race_type: str | None, query: str | None, limit: int = 50) -> list[dict]`

- [ ] **Step 1: Write the failing test**

`mcp-server/tests/test_query.py`:

```python
from tw_cycling_data_mcp import query


def test_normalize_strips_mask_and_whitespace_lowercases():
    assert query.normalize_search("林○宇") == "林宇"
    assert query.normalize_search("  AB cd ") == "abcd"


def test_match_athletes_by_visible_name_and_id_prefix():
    idx = [
        {"id": "1a2b3c4d", "nm": "林○宇", "n": 5, "ny": 3, "best": 2},
        {"id": "ff00ff00", "nm": "陳○明", "n": 9, "ny": 4, "best": 1},
    ]
    # 可見字「宇」要命中 林○宇
    out = query.match_athletes(idx, "宇", limit=10)
    assert [a["id"] for a in out] == ["1a2b3c4d"]
    # 16 進位 query 命中 id 前綴
    out = query.match_athletes(idx, "ff00", limit=10)
    assert [a["id"] for a in out] == ["ff00ff00"]
    # 空 query 依 n desc 排序回前 N
    out = query.match_athletes(idx, "", limit=1)
    assert out[0]["id"] == "ff00ff00"


def test_filter_races_by_year_and_query():
    idx = [
        {"rk": "a", "y": 2024, "rn": "東三塔550", "s": "TBA"},
        {"rk": "b", "y": 2025, "rn": "北高360", "s": "TBA"},
        {"rk": "c", "y": 2024, "rn": "苗栗繞圈賽", "s": None},
    ]
    assert {r["rk"] for r in query.filter_races(idx, 2024, None, None)} == {"a", "c"}
    assert [r["rk"] for r in query.filter_races(idx, None, None, "塔")] == ["a"]
    assert query.filter_races(idx, 2024, None, None, limit=1).__len__() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd mcp-server && python -m pytest tests/test_query.py -v`
Expected: FAIL(`ModuleNotFoundError: No module named 'tw_cycling_data_mcp'`)

- [ ] **Step 3: Create minimal `pyproject.toml` and package init**

`mcp-server/pyproject.toml`(最小,Task 7 會補 dependencies / entry point):

```toml
[project]
name = "tw-cycling-data-mcp"
version = "0.1.0"
description = "MCP server for the tw-cycling-data public API"
requires-python = ">=3.10"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["tw_cycling_data_mcp"]
```

`mcp-server/tw_cycling_data_mcp/__init__.py`:空檔。

- [ ] **Step 4: Implement `query.py`**

```python
# -*- coding: utf-8 -*-
"""Pure query helpers for the MCP server — no HTTP, fully unit-testable.
Mirrors the frontend web/src/lib/athletes.ts search semantics."""
import re

_ID_RE = re.compile(r"^[0-9a-f]{4,}$")


def normalize_search(s):
    """Strip the PDPA mask glyph ○ and whitespace, lowercase — so a query of the
    visible characters matches a masked name (mirrors frontend normalizeSearch)."""
    return re.sub(r"[○\s]", "", s or "").lower()


def match_athletes(index, query, limit=20):
    q = (query or "").strip()
    nq = normalize_search(q)
    id_query = bool(_ID_RE.match(nq))
    if q:
        pool = [a for a in index
                if nq in normalize_search(a.get("nm", ""))
                or (id_query and a.get("id", "").startswith(nq))]
    else:
        pool = list(index)
    pool.sort(key=lambda a: (-(a.get("n") or 0), -(a.get("ny") or 0),
                             a.get("best") if a.get("best") is not None else 9999))
    return pool[:limit]


def filter_races(index, year=None, race_type=None, query=None, limit=50):
    nq = normalize_search(query) if query else None
    out = []
    for r in index:
        if year is not None and r.get("y") != year:
            continue
        if race_type is not None and (r.get("s") or "") != race_type:
            continue
        if nq and nq not in normalize_search(r.get("rn", "")):
            continue
        out.append(r)
    return out[:limit]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd mcp-server && python -m pytest tests/test_query.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add mcp-server/pyproject.toml mcp-server/tw_cycling_data_mcp/__init__.py mcp-server/tw_cycling_data_mcp/query.py mcp-server/tests/test_query.py
git commit -m "feat(mcp): pure query helpers (search/filter) mirroring frontend search"
```

---

## Task 6: MCP HTTP 取用層(`client.py`)

把線上 v1 端點包成可注入 fetcher 的 client,測試不打真站。交付物:`ApiClient` + 測試。

**Files:**
- Create: `mcp-server/tw_cycling_data_mcp/client.py`
- Create: `mcp-server/tests/test_client.py`

**Interfaces:**
- Consumes: `TWCD_API_BASE` 環境變數(預設 `https://tw-cycling-data.vercel.app/data/v1`)。
- Produces:
  - `DEFAULT_BASE: str`
  - `ApiClient(base_url: str | None = None, fetch=None)`,方法:`manifest()`、`athletes_index()`、`athlete(athlete_id)`、`races_index()`、`race(file_stem)`、`team(team_id)`,皆回 parsed JSON;`fetch(url) -> dict|list` 可注入(預設用 httpx)。

- [ ] **Step 1: Write the failing test**

`mcp-server/tests/test_client.py`:

```python
from tw_cycling_data_mcp.client import ApiClient


def make_client(routes):
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return routes[url]

    return ApiClient(base_url="http://x/data/v1", fetch=fake_fetch), calls


def test_client_builds_urls_and_returns_json():
    routes = {
        "http://x/data/v1/manifest.json": {"api_version": "v1"},
        "http://x/data/v1/races.json": [{"rk": "a", "file": "a__2024"}],
        "http://x/data/v1/race/a__2024.json": {"rows": []},
        "http://x/data/v1/athlete/abc.json": {"id": "abc"},
    }
    client, calls = make_client(routes)
    assert client.manifest()["api_version"] == "v1"
    assert client.races_index()[0]["rk"] == "a"
    assert client.race("a__2024") == {"rows": []}
    assert client.athlete("abc") == {"id": "abc"}
    assert "http://x/data/v1/race/a__2024.json" in calls


def test_client_default_base_is_production():
    from tw_cycling_data_mcp import client
    assert client.DEFAULT_BASE == "https://tw-cycling-data.vercel.app/data/v1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd mcp-server && python -m pytest tests/test_client.py -v`
Expected: FAIL(`ModuleNotFoundError: ...client`)

- [ ] **Step 3: Implement `client.py`**

```python
# -*- coding: utf-8 -*-
"""HTTP access layer for the tw-cycling-data public v1 API. The fetch callable
is injectable so tests never hit the network."""
import os

DEFAULT_BASE = "https://tw-cycling-data.vercel.app/data/v1"


def _httpx_fetch(url):
    import httpx
    r = httpx.get(url, timeout=15.0, follow_redirects=True)
    r.raise_for_status()
    return r.json()


class ApiClient:
    def __init__(self, base_url=None, fetch=None):
        self.base = (base_url or os.environ.get("TWCD_API_BASE") or DEFAULT_BASE).rstrip("/")
        self._fetch = fetch or _httpx_fetch

    def _get(self, path):
        return self._fetch(f"{self.base}/{path}")

    def manifest(self):
        return self._get("manifest.json")

    def athletes_index(self):
        return self._get("athletes.json")

    def athlete(self, athlete_id):
        return self._get(f"athlete/{athlete_id}.json")

    def races_index(self):
        return self._get("races.json")

    def race(self, file_stem):
        return self._get(f"race/{file_stem}.json")

    def team(self, team_id):
        return self._get(f"team/{team_id}.json")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd mcp-server && python -m pytest tests/test_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mcp-server/tw_cycling_data_mcp/client.py mcp-server/tests/test_client.py
git commit -m "feat(mcp): injectable HTTP client for the v1 API"
```

---

## Task 7: MCP server 組裝(`server.py` + pyproject entry point + README)

把 query + client 接成 FastMCP tools,可由 uvx 執行。交付物:server 可列出 6 個 tools,煙霧測試通過。

**Files:**
- Create: `mcp-server/tw_cycling_data_mcp/server.py`
- Modify: `mcp-server/pyproject.toml`(加 dependencies + entry point)
- Create: `mcp-server/README.md`
- Create: `mcp-server/tests/test_server.py`

**Interfaces:**
- Consumes: `query`(Task 5)、`ApiClient`(Task 6)。
- Produces: `server.mcp`(FastMCP 實例);console script `tw-cycling-data-mcp` → `server:main`。

- [ ] **Step 1: Complete `pyproject.toml`**

把 Task 5 的最小 pyproject 補上依賴與 entry point:

```toml
[project]
name = "tw-cycling-data-mcp"
version = "0.1.0"
description = "MCP server for the tw-cycling-data public API"
requires-python = ">=3.10"
dependencies = ["mcp>=1.2.0", "httpx>=0.27"]

[project.scripts]
tw-cycling-data-mcp = "tw_cycling_data_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["tw_cycling_data_mcp"]
```

- [ ] **Step 2: Write the failing test**

`mcp-server/tests/test_server.py`(用 fake client 注入,驗證 tool 函式邏輯;不啟動 stdio):

```python
from tw_cycling_data_mcp import server


class FakeClient:
    def manifest(self):
        return {"api_version": "v1", "stats": {"records": 10}}

    def athletes_index(self):
        return [{"id": "ff00ff00", "nm": "陳○明", "n": 9, "ny": 4, "best": 1}]

    def races_index(self):
        return [{"rk": "a", "y": 2024, "rn": "東三塔550", "s": "TBA", "file": "a__2024"}]

    def race(self, file_stem):
        return {"file": file_stem, "rows": []}

    def athlete(self, aid):
        return {"id": aid}

    def team(self, tid):
        return {"id": tid}


def test_tool_impls_use_query_and_client():
    c = FakeClient()
    assert server.dataset_overview_impl(c)["stats"]["records"] == 10
    assert server.search_athletes_impl(c, "明", 10)[0]["id"] == "ff00ff00"
    assert server.list_races_impl(c, 2024, None, "塔", 10)[0]["rk"] == "a"
    # get_race 接受 race_key,內部用 races_index 解析 file 後抓明細
    assert server.get_race_impl(c, "a")["file"] == "a__2024"
    assert server.get_athlete_impl(c, "abc")["id"] == "abc"


def test_server_registers_six_tools():
    # FastMCP 實例存在且註冊了預期工具名
    names = server.tool_names()
    assert set(names) == {
        "dataset_overview", "search_athletes", "get_athlete",
        "list_races", "get_race", "get_team",
    }
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd mcp-server && python -m pytest tests/test_server.py -v`
Expected: FAIL(`ModuleNotFoundError: ...server`)

- [ ] **Step 4: Implement `server.py`**

`_impl` 函式承載邏輯(吃注入的 client,可單測);tool 包裝註冊到 FastMCP。

```python
# -*- coding: utf-8 -*-
"""FastMCP server exposing the tw-cycling-data public API as MCP tools.
Reads the live /data/v1 endpoints over HTTP. Tool logic lives in *_impl
functions (client injected) so it is unit-testable without a server."""
from mcp.server.fastmcp import FastMCP

from . import query
from .client import ApiClient

mcp = FastMCP("tw-cycling-data")
_client = ApiClient()


# ---- impls (client injected; unit-testable) ----
def dataset_overview_impl(client):
    return client.manifest()


def search_athletes_impl(client, q, limit):
    return query.match_athletes(client.athletes_index(), q, limit)


def get_athlete_impl(client, athlete_id):
    return client.athlete(athlete_id)


def list_races_impl(client, year, race_type, q, limit):
    return query.filter_races(client.races_index(), year, race_type, q, limit)


def get_race_impl(client, race_key):
    # races.json 的該筆 file 欄位是明細檔名;找不到就直接以 race_key 當檔名嘗試
    idx = client.races_index()
    hit = next((r for r in idx if r.get("rk") == race_key), None)
    return client.race(hit["file"] if hit else race_key)


def get_team_impl(client, team_id):
    return client.team(team_id)


# ---- MCP tools ----
@mcp.tool()
def dataset_overview() -> dict:
    """Dataset size, year range, source count, and license (from manifest.json)."""
    return dataset_overview_impl(_client)


@mcp.tool()
def search_athletes(query: str, limit: int = 20) -> list:
    """Search athletes by visible (masked) name or athlete_id prefix. PDPA: masked names only."""
    return search_athletes_impl(_client, query, limit)


@mcp.tool()
def get_athlete(athlete_id: str) -> dict:
    """One athlete's de-identified result history."""
    return get_athlete_impl(_client, athlete_id)


@mcp.tool()
def list_races(year: int = None, race_type: str = None, query: str = None, limit: int = 50) -> list:
    """List races, optionally filtered by year, series, or name substring."""
    return list_races_impl(_client, year, race_type, query, limit)


@mcp.tool()
def get_race(race_key: str) -> dict:
    """One race leaderboard (re-ranked by category + finish time)."""
    return get_race_impl(_client, race_key)


@mcp.tool()
def get_team(team_id: str) -> dict:
    """One team's roster and record."""
    return get_team_impl(_client, team_id)


def tool_names():
    # mcp 套件版本間 API 名稱可能不同;優先用公開列舉,退而求其次讀內部登錄表。
    import asyncio
    try:
        tools = asyncio.run(mcp.list_tools())
        return [t.name for t in tools]
    except Exception:
        return list(getattr(mcp, "_tool_manager")._tools.keys())


def main():
    mcp.run()


if __name__ == "__main__":
    main()
```

> 註:`tool_names()` 對 `mcp` SDK 版本差異做了退讓。實作時若 `mcp.list_tools()` 簽名不同,以該版本實際 API 調整,確保測試的 6 個工具名可被列出。

- [ ] **Step 5: Run test to verify it passes**

Run: `cd mcp-server && pip install -e . && python -m pytest tests/ -v`
Expected: PASS(6 tools 註冊、各 `_impl` 行為正確)

- [ ] **Step 6: Write `mcp-server/README.md`**

````markdown
# tw-cycling-data MCP server

讓 MCP 用戶端(Claude 等)查詢台灣公路車賽公開資料(去識別化)。即時讀線上 v1 API。

## 執行

```bash
uvx --from git+https://github.com/TTigger/tw-cycling-data#subdirectory=mcp-server tw-cycling-data-mcp
```

或本機開發:
```bash
cd mcp-server && uv run tw-cycling-data-mcp
```

預設讀 `https://tw-cycling-data.vercel.app/data/v1`;以 `TWCD_API_BASE` 覆寫(例如指向本機建置)。

## Tools

`dataset_overview`、`search_athletes(query, limit)`、`get_athlete(athlete_id)`、`list_races(year?, race_type?, query?, limit)`、`get_race(race_key)`、`get_team(team_id)`。

## 在 Claude Desktop 設定

```json
{
  "mcpServers": {
    "tw-cycling-data": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/TTigger/tw-cycling-data#subdirectory=mcp-server", "tw-cycling-data-mcp"]
    }
  }
}
```

資料授權 CC BY 4.0;請標註來源。
````

- [ ] **Step 7: Commit**

```bash
git add mcp-server/
git commit -m "feat(mcp): FastMCP server with 6 read-only tools over the v1 API (uvx-runnable)"
```

---

## Task 8: 記憶與待辦更新

更新專案記憶,記錄 v1 API 契約與未來待辦。交付物:記憶檔更新(非程式碼;無測試)。

**Files:**
- Modify: `C:\Users\user\.claude\projects\C--Users-user-Desktop-tw-cycling-data\memory\data-pipeline.md`
- Modify: `C:\Users\user\.claude\projects\C--Users-user-Desktop-tw-cycling-data\memory\MEMORY.md`(若新增記憶檔才需要;否則僅更新既有行)

- [ ] **Step 1: Update the data-pipeline memory**

在 `data-pipeline.md` 記錄:build 輸出已遷至 `web/public/data/v1/`(單一常數 `common.PUBLIC_DATA_DIR`);新增公開 API 契約(manifest.json + CORS via `web/vercel.json`);MCP server 在 `mcp-server/`(Python,uvx,即時讀線上 v1)。記錄**未來待辦**:Node/TS MCP、動態 serverless API、寫入端點、舊 `/data/` 相容層、分頁/查詢語言。

- [ ] **Step 2: Commit (memory 檔在 repo 外,免 git;若有 MEMORY.md 指標行則一併調整)**

記憶檔位於使用者 home,不進 repo。此步驟僅寫檔,不 commit。

---

## Self-Review

**1. Spec coverage:**
- A1 後端 OUT→v1 → Task 1 ✅;A2 前端 → Task 1 ✅;A3 CORS → Task 2 ✅;A4 manifest(指標推導+測試)→ Task 3 ✅;A5 文件 → Task 4 ✅;B MCP(純函式/client/server/uvx/README/測試)→ Task 5–7 ✅;授權 CC BY 4.0 → Task 3/4 ✅;PDPA → 全程僅遮罩 ✅;未來待辦記錄 → Task 8 + spec 末 ✅;DRY 單一常數 → Task 1 ✅。
- 缺口檢查:`climb_profiles.json`(輸入)以 `git mv` 保留(Task 1 Step 5)✅;`coverage.json`/`overseas/` 由 discover/overseas 腳本寫入,路徑已改(Task 1 Step 7)✅。

**2. Placeholder scan:** 無 TBD/「之後補」;每個改碼步驟附完整程式或精確 before→after。Vercel root 不確定處給了明確驗證指令與 fallback(非佔位)。

**3. Type consistency:** `compute_manifest(data_dir)`、`ApiClient.race(file_stem)`、`get_race_impl` 以 `races.json.file` 解析明細路徑——與 `RaceIndex.file`、前端 `loadRaceDetail` 一致;`match_athletes`/`filter_races` 簽名在 Task 5 定義、Task 7 沿用一致;`build_manifest.ENDPOINTS` 在 Task 3 定義、Task 4 測試引用一致。

---

## 執行順序

Task 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8。Task 5/6 可獨立於 1–4(MCP 讀線上,開發期可用 `TWCD_API_BASE` 指向既有部署),但建議照序以便 manifest/CORS 先就緒。
