# 版本化唯讀 API + Python MCP server — 設計 spec

**日期**:2026-06-30
**狀態**:已核可,待寫實作計畫
**範圍**:把既有的靜態 per-entity JSON 分片正式化為**有版本、有文件、可跨網域取用**的公開唯讀 API(`/data/v1/`),並新增一個**即時讀線上 API 的 Python MCP server**(`mcp-server/`)。這是「被引用、被看見」路線圖的 Feature 1(共 4 個子專案)。

## 背景與動機

網站部署已經在 `web/public/data/` 下提供事實上的靜態 API:
- 明細分片:`athlete/{athlete_id}.json`(29,033)、`race/{race_key}.json`(216)、`team/{team_id}.json`(1,022)、`overseas/index.json`。
- 彙整檔:`athletes.json`、`races.json`、`teams.json`、`series.json`、`overview.json`、`coverage.json`… 共 15 檔。

缺的不是資料,而是**讓它能被當 API 用、被引用**的東西:版本與穩定路徑、欄位 schema 文件、跨網域 CORS、一個可發現的 manifest 入口,以及上層的 MCP 封裝。對標對象(FirstCycling 被包成 Python wrapper 又包成 MCP、PCS/CyclingStatsDataBase 開 REST)都有對外 API;本資料集的差異化(台灣業餘×多源×PDPA 去識別化)更值得被當資料源引用。

## 已核可的決策

1. **API 範圍**:**重構為版本化 `/data/v1/` 命名空間**(非僅最小正式化)。文件補齊、路徑與 manifest 指標正確。
2. **MCP 執行環境**:**先做 Python**(官方 MCP SDK,uvx/pip 一鍵執行);Node/TypeScript 之後再說。
3. **MCP 資料源**:**即時讀線上 API**(HTTP 抓已部署的 `/data/v1/` 端點),不打包資料快照。
4. **MCP 位置**:`mcp-server/`(repo 根目錄下獨立 Python 套件)。
5. **乾淨切換**:只輸出 `/data/v1/`,不保留舊 `/data/` 路徑相容層(目前無文件化的對外消費者)。

## 架構總覽

兩個獨立元件,皆建在既有資料分片上,互不耦合:

- **A. 版本化公開 API**(`/data/v1/`)— 後端 build 輸出改目錄、前端讀取改 base、加 CORS、加 manifest 入口與 `docs/API.md`。
- **B. Python MCP server**(`mcp-server/`)— 純函式(查詢正規化、索引篩選)+ HTTP 取用層分離;即時讀 A 的線上端點。

資料流:
`master.public.json → build_*.py → web/public/data/v1/*.json(+ manifest.json)→ Vercel(CORS header)→ ① 前端網站 ② MCP server(HTTP)③ 任意第三方 fetch`

## 元件設計

### A1. 後端輸出改為 `v1/`(DRY)

- 在 `scrapers/common.py` 新增單一來源常數:
  `PUBLIC_DATA_DIR = os.path.join(<repo>, "web", "public", "data", "v1")`(以 `common.py` 所在位置回推 repo 根)。
- 8 個 build 腳本(`build_viz.py`、`build_athletes.py`、`build_teams.py`、`build_series.py`、`build_insights.py`、`build_race_dna.py`、`build_difficulty.py`、`build_fonts.py`)各自的 `OUT = .../web/public/data` 改為引用 `common.PUBLIC_DATA_DIR`。子目錄(`race/`、`athlete/`、`team/`、`overseas/`)維持相對於該 OUT。
- 其餘寫 `web/public/data` 的腳本(若有,如 overseas/coverage 來源)一併改用同常數。
- 既有 `web/public/data/*.json` 與子目錄舊檔:實作時一次性 `git rm` 移除,改由 v1 重建(避免新舊並存造成混淆)。

### A2. 前端讀取改為 `/data/v1/`

- `web/src/lib/data-load.ts`:目前 `const base = import.meta.env.BASE_URL.replace(/\/$/, "")`,所有 fetch 用 `${base}/data/...`。改為新增 `const API = `${base}/data/v1``,所有端點改用 `${API}/...`。**單點修改**。
- 兩個建置期靜態 import 改路徑:
  - `web/src/pages/athletes/[id].astro`:`../../../public/data/athletes.json` → `../../../public/data/v1/athletes.json`
  - `web/src/pages/race/[slug].astro`:`../../../public/data/races.json` → `../../../public/data/v1/races.json`

### A3. CORS + 快取(`web/vercel.json`)

- 新增 `web/vercel.json`(Vercel 專案 root 為 `web/`;實作時先確認 root dir 設定)。對 `/data/(.*)`(涵蓋 v1)加 header:
  - `Access-Control-Allow-Origin: *`(讓第三方網站/notebook 可跨網域 fetch)
  - `Cache-Control: public, max-age=3600, stale-while-revalidate=86400`(JSON 可被 CDN 快取)
- 若 Vercel root 不是 `web/`,改放到部署 root 的 `vercel.json`,路徑前綴對應調整。

### A4. manifest 入口與指標(`/data/v1/manifest.json`)

- 由一個小腳本/或併入 `build_viz.py` 尾端產生 `manifest.json`,內容:
  - `api_version`: `"v1"`
  - `dataset_version`: 以建置日期(由現有 `scraped_at`/`master_summary` 取,或建置當下日期字串)
  - `generated_at`: ISO8601
  - `stats`:`records`、`races`、`series`、`athletes`、`teams`、`sources`(數)、`year_min`、`year_max`(取自 `overview.json` 的 kpi + athletes/teams 索引長度)
  - `license`:資料授權標示(見「授權」)
  - `endpoints`:陣列,每筆 `{ path, description, kind: "index"|"detail"|"meta", schema?: "<docs/API.md#anchor>" }`,涵蓋全部端點(含 `athlete/{id}`、`race/{race_key}`、`team/{id}` 的樣板路徑)。
- **指標正確性**:manifest 的 stats 必須由實際建置產物推導(不可寫死),測試斷言其與來源一致。

### A5. 文件(`docs/API.md` + README 區段)

- `docs/API.md`:
  - 端點總表(路徑、用途、回傳形狀摘要)。
  - 每個主要端點的欄位 schema(以 markdown 表;與 `web/src/lib/types.ts` 對齊)。
  - PDPA 去識別化說明(僅 `name_masked`、salted `athlete_id`、`has_uci`;無 `name_raw`)。
  - **授權**:明確標示資料授權(見下「授權」)。
  - 取用範例:`curl` + Python(`requests`)各一,示範 `manifest → races → race detail`。
- `README.md` / `README.en.md`:新增「Public API」區段,連到 `docs/API.md` 與 manifest URL,附最小範例。

### B. Python MCP server(`mcp-server/`)

- 結構:
  - `mcp-server/pyproject.toml` — 套件名 `tw-cycling-data-mcp`,entry point 可被 `uvx`/`uv run` 執行;依賴官方 `mcp` SDK + `httpx`(或 `requests`)。
  - `mcp-server/tw_cycling_data_mcp/__init__.py`
  - `mcp-server/tw_cycling_data_mcp/server.py` — FastMCP server,註冊 tools。
  - `mcp-server/tw_cycling_data_mcp/client.py` — HTTP 取用層(base URL,讀 manifest/index/detail;逾時與錯誤處理)。
  - `mcp-server/tw_cycling_data_mcp/query.py` — **純函式**:`normalize_search(s)`(去 ○/空白、小寫,比照前端 `athletes.ts`)、`filter_races(index, year, race_type, query)`、`match_athletes(index, query, limit)`。
  - `mcp-server/README.md` — 安裝/uvx 執行/設定 base URL/在 Claude 設定的範例。
  - `mcp-server/tests/` — pytest。
- Base URL:預設 `https://tw-cycling-data.vercel.app/data/v1`,可由環境變數 `TWCD_API_BASE` 覆寫(指向本機建置或 staging)。
- **Tools**:
  - `dataset_overview()` → 讀 `manifest.json`(+ 必要時 `overview.json`),回資料集規模/年份/來源數/授權。
  - `search_athletes(query: str, limit: int = 20)` → 取 `athletes.json` 索引,以 `normalize_search` 比對(含 `athlete_id` 前綴),回 `{id, name_masked, team, ...}` 清單。
  - `get_athlete(athlete_id: str)` → `athlete/{athlete_id}.json`。
  - `list_races(year: int | None, race_type: str | None, query: str | None, limit: int = 50)` → 篩 `races.json`。
  - `get_race(race_key: str)` → `race/{race_key}.json`(前端已依分組+時間重排,直接回)。
  - `get_team(team_id: str)` → `team/{team_id}.json`。
- 錯誤處理:HTTP 404 → 回清楚的「查無此 id」訊息;逾時/連線錯誤 → 回可重試提示;不可讓例外冒泡成未處理錯誤。

## 授權

- 程式碼:沿用 repo 既有授權。
- **資料**:於 `docs/API.md`、`manifest.license`、README 標示資料授權(建議 CC BY 4.0,要求標註來源 `tw-cycling-data` 並連回專案);實作前若 repo 尚無資料授權聲明,於 Task 中一併加入 `LICENSE`/`DATA_LICENSE` 說明。最終字串於寫計畫時定稿(預設 CC BY 4.0,除非 owner 另指定)。

## 測試(照 dev-workflow 全套)

- **後端**:pytest 斷言 (a) build 輸出落在 `web/public/data/v1/`;(b) `manifest.json` 的 `stats` 與實際產物一致(races 數=races.json 長度、athletes 數=athlete 分片數…);(c) `endpoints` 涵蓋所有實際端點。既有 pytest 全綠。
- **前端**:`astro check` clean + `astro build` 成功;瀏覽器抽查首頁/一場 race/一位選手頁,確認讀 `/data/v1/` 正常(對標 dev-workflow 的 browser-verify)。
- **MCP**:`mcp-server/tests/` 以 pytest 測純函式(`normalize_search`、`filter_races`、`match_athletes` 的命中/邊界);HTTP 取用層用 mock/fake fetcher(注入式 client),**不打真站**;一個煙霧測試確認 server 能列出 tools。
- **流程**:`python -m pytest scrapers/ mcp-server/` → 重建 v1 → astro check/build → 瀏覽器驗證 → 各自 commit。

## 風險與緩解

- **Vercel root dir 不確定**:`vercel.json` 放錯位置 → CORS 不生效。緩解:實作 CORS 任務時先以 `gh`/Vercel 設定確認 root,部署後用 `curl -I` 驗證 `Access-Control-Allow-Origin` 真的回來。
- **大量舊檔搬移**:30k+ 檔案 `git rm` + 重建,diff 巨大但機械。緩解:用 build 腳本重生,git 自然追蹤;commit 訊息標明「路徑遷移」。
- **manifest 指標漂移**:寫死數字會過期。緩解:一律由產物推導 + 測試斷言。
- **MCP 依賴線上站**:站台離線時 MCP 失效。緩解:已是核可決策(即時讀);錯誤處理回友善訊息,文件註明可用 `TWCD_API_BASE` 指向本機。

## PDPA

維持去識別化:API 與 MCP 僅暴露 `name_masked`、salted `athlete_id`、`has_uci`;`name_raw` 僅存內部 master.json(gitignored)。MCP 不引入任何新的個資欄位。

## 實作順序(降風險)

1. **A1+A2 路徑遷移**(後端 OUT→v1、前端 base→v1)→ 重建 → 網站在 v1 上正常。
2. **A3 CORS** → 部署驗證 header。
3. **A4 manifest** → 指標測試。
4. **A5 文件**(API.md + README)。
5. **B MCP server**(純函式→client→server→tests)。

## 記憶 / 文件更新

- 更新 `data-pipeline` 記憶:build 輸出已遷至 `web/public/data/v1/`,並有 manifest + CORS 的公開 API 契約。
- README 增 Public API 區段(見 A5)。

## 未來待辦(本次不做,記錄備查)

- **Node/TypeScript MCP**:與 web 同生態、npx 散布最廣,之後可並行提供(owner 表示「之後再說」)。
- **動態 serverless API**:Vercel Functions 提供查詢/過濾/分頁,超出靜態 JSON 能力時再評估。
- **寫入端點**:目前純唯讀;若未來要接受投稿/修正再設計。
- **舊 `/data/` 相容層**:本次乾淨切換不保留;若日後出現對外消費者依賴舊路徑,再加 wildcard 轉址。
- **分頁 / 查詢語言**:索引檔目前整包回傳;資料量再成長時加分頁或查詢參數。
