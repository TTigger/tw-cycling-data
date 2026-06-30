# API 探索頁(/api Explorer)— 設計 spec

**日期**:2026-06-30
**狀態**:已核可,待寫實作計畫
**範圍**:新增前端頁 `/api`,把現有公開唯讀 API(`/data/v1/`)做成好入門的門面:規模卡 + 端點表 + **頁內即時抓一筆預覽** + 複製即用範例 + 延伸連結。純前端,讀現有 `manifest.json`,**不動資料、不重建**。Feature 1 之後的加碼項。

## 背景與動機

公開 API 目前只有 `docs/API.md` + raw JSON,單看文件單調、難入門。一個 `/api` 頁讓人**一眼看懂規模、點開看真實 JSON、複製即用**,提升「被引用/被使用」。

**與既有區隔**:`docs/API.md` = 完整規格(開發者細讀);`/api` = 入門門面(規模 + 可互動端點 + 範例)。

## 已確認的現況

- `web/public/data/v1/manifest.json` 已含 `api_version, dataset, homepage, license, attribution, stats{records,races,race_editions,series,athletes,teams,sources,year_min,year_max}, endpoints[{path,kind,description}]`。
- 前端**尚無 manifest loader**;island 慣例為 self-loading(`InsightsApp`/`TrendsApp`/`BenchmarkTool`:useEffect + `Skeleton`)。`EChart` 等在 charts/;`Base.astro` 導覽已有約 11 連結。
- endpoints 路徑分兩類:**索引/meta**(`manifest.json`、`overview.json`、`races.json`、`athletes.json`、`teams.json`、`series.json`、`coverage.json`、`benchmarks.json`)與**樣板明細**(`race/{race_key}.json`、`athlete/{athlete_id}.json`、`team/{team_id}.json`,路徑含 `{`)。

## 已核可的決策

1. **頁內即時預覽**:端點表的索引/meta 端點有「預覽」鈕,**即時 fetch 真實 JSON** 並在列下展開**有界**預覽(不把大檔整包塞進 DOM)。
2. 樣板明細端點(含 `{`)**不做頁內預覽**(需 id),改標註「id 取自 races/athletes/teams.json」+ 連結。
3. 其餘照前述:規模卡、複製範例、延伸連結、導覽加「API」。

## 元件設計(單一職責)

### 1. `web/src/lib/types.ts` — Manifest 型別
```ts
export interface ManifestEndpoint { path: string; kind: string; description: string; }
export interface ManifestStats { records: number; races: number; race_editions: number; series: number; athletes: number; teams: number; sources: number; year_min: number; year_max: number; }
export interface Manifest { api_version: string; dataset: string; homepage: string; license: string; attribution: string; stats: ManifestStats; endpoints: ManifestEndpoint[]; }
```

### 2. `web/src/lib/data-load.ts` — loaders
- `loadManifest(): Promise<Manifest>` → fetch `${API}/manifest.json`。
- `fetchEndpoint(path: string): Promise<unknown>` → fetch `${API}/${path}`(供預覽用任意 v1 路徑;沿用既有 `API` base 常數)。

### 3. `web/src/lib/api-explorer.ts`(純函式,可測)
- `isTemplated(path: string): boolean` → `path.includes("{")`。
- `endpointPreview(data: unknown, maxChars = 1500): { summary: string; body: string }`:
  - array → `summary = "陣列,共 N 筆;顯示第 1 筆:"`、`body = JSON.stringify(data[0], null, 2)`(截斷至 maxChars,超出加 `…`)。
  - object → `summary = "物件,鍵:k1, k2, …"`、`body = JSON.stringify(data, null, 2)`(截斷)。
  - 其他/空 → 合理字串。
  - **永遠只渲染有界字串**(即使 fetch 回 3.9MB 的 athletes.json,也只 stringify 第 1 筆 + 截斷),DOM 不爆。
- `curlExample(base, path)` / `pythonExample(base, path)`:回字串範例(path 用 `races.json`)。

### 4. `web/src/components/api/ApiExplorer.tsx`(self-loading island)
- useEffect `loadManifest()` + `Skeleton`;錯誤狀態顯示訊息(避免永久 skeleton)。
- **規模卡**:從 `manifest.stats` 顯示 records / races / race_editions / athletes / teams / sources / `year_min–year_max`。
- **端點表**:每列 path(`code`)+ kind + description。
  - 索引/meta 列:`預覽` 鈕 → `fetchEndpoint(path)` → `endpointPreview` → 列下 `<pre>` 顯示 summary + body;載入中顯示 spinner;失敗顯示訊息。另附「開新分頁」連到 `${API}/${path}`。
  - 樣板列(`isTemplated`):不顯示預覽鈕;標「需 id(見 races/athletes/teams.json)」。
- **複製範例**:curl + Python 各一塊,各一「複製」鈕(`navigator.clipboard.writeText`,複製後短暫顯示「已複製」)。
- **延伸連結**:`docs/API.md`(GitHub blob)、MCP server(`mcp-server/`)、開放資料集(Releases / DATASET.md)、授權 CC BY 4.0(標一次)。

### 5. `web/src/pages/api.astro` + 導覽
- 掛載 `ApiExplorer` `client:only="react"`;標題 + 一句說明(這是公開唯讀 API,CC BY 4.0)。
- `Base.astro` 導覽加 `<a href="/api">API</a>`。

## 資料流
`/data/v1/manifest.json → loadManifest → ApiExplorer`(規模卡 + 端點表);使用者點預覽 → `fetchEndpoint(path) → endpointPreview`(有界)→ 列下展開。皆讀既有公開檔,無新資料、無後端。

## 誠實 / 邊界
- 預覽只渲染有界片段(摘要 + 第 1 筆/截斷),不把大檔塞進畫面。
- 規模數字一律來自 manifest(永遠最新),不寫死。
- 無個資(API 本就去識別化)。

## 測試(照 dev-workflow)
- 前端 `web/src/lib/api-explorer.test.ts`(vitest):`isTemplated`(含/不含 `{`);`endpointPreview`(array → 摘要含筆數 + 第 1 筆 body;object → 鍵列出;截斷加 `…`;空/None 安全);範例字串含 base 與 path。
- 流程:`vitest` → astro build(`/api/index.html` 產出)→ 瀏覽器抽查 /api(規模卡、點預覽看到真實 JSON、複製鈕、樣板列標註)。

## YAGNI(不做)
- 後端/serverless、寫入、查詢參數、OpenAPI 規格檔、樣板明細端點的頁內預覽(需 id;以連結替代)、把整包大檔渲染進畫面。

## 未來待辦(本次不做,記錄備查)
- 若要,樣板端點可做「抓索引第一筆 id 再抓明細」的範例預覽(races.json 小、可行;athletes.json 3.9MB 較重)。
- 導覽連結漸多,未來可考慮收進「更多」下拉。
