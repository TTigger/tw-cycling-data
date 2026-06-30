# /api 改套件 landing page — 設計 spec

**日期**:2026-06-30
**狀態**:已核可,待寫實作計畫
**範圍**:把現有 `/api` 頁改版成類似 npm/PyPI 套件首頁的樣子——快速上手 hero + 規模 badge、保留端點**表格**但每列展開顯示**該端點專屬的 curl/Python/JS 範例**、複製改 **icon 按鈕**。純前端,改 `ApiExplorer.tsx` 一個元件,重用既有 helpers。加碼項 #26。

## 背景與動機

現有 `/api`(Feature「API 探索頁」)已有:規模卡、端點表、**單一全域** curl/Python 範例、文字「複製」鈕、即時預覽。使用者回饋希望更像套件 landing page:**每端點各自的用法範例**、**複製 icon**、更好入門。

## 已核可的決策

1. 逐端點範例放在**展開列內**(保留表格,點開才看)。
2. 複製按鈕改 **icon**(剪貼簿 SVG,複製後顯示 ✓)。
3. 加 hero / 快速上手區 + 規模 badge。
4. 純前端、改一個元件;不動資料、不動後端。

## 元件設計

### `web/src/lib/api-explorer.ts`(純函式,新增 + 既有)
- 既有:`isTemplated`、`endpointPreview`、`curlExample(base,path)`、`pythonExample(base,path)`(保留)。
- **新增** `jsExample(base, path): string` —— 回 JS fetch 範例:
  `` `fetch("${base}/${path}").then(r => r.json()).then(console.log)` ``。
- 三個 `*Example` 皆吃 `path`,可逐端點產生範例。

### `web/src/components/api/ApiExplorer.tsx`(改版,self-loading island 不變)
版面(由上而下):
1. **Hero / 快速上手**:
   - 一句定位(唯讀 JSON API、CORS、CC BY 4.0)。
   - **Base URL** 一行 + 複製 icon。
   - 「10 秒上手」一段 `jsExample(BASE, "races.json")`(或 curl)+ 複製 icon。
2. **規模 badge 列**:由 `manifest.stats` 顯示 records / races / race_editions / athletes / teams / sources / 年份 / 授權(沿用既有數字,改成 pill/badge 樣式)。
3. **端點(表格 + 展開列)**:
   - 表頭:路徑 | 類型 | 說明 | 動作(展開鈕「範例/收合」)。
   - 每列**展開**後顯示:
     - **curl**(`curlExample`)+ 複製 icon
     - **Python**(`pythonExample`)+ 複製 icon
     - **JS**(`jsExample`)+ 複製 icon
     - 索引/meta 端點:**即時預覽**(`fetchEndpoint`+`endpointPreview`,有界,沿用既有);樣板端點(`isTemplated`):顯示「需 id(見 races/athletes/teams.json,連結)」且範例用樣板路徑(如 `race/{race_key}.json`)+ 註明 `{…}` 為佔位。
   - 「開新分頁↗」連到該端點 JSON(索引端點)。
4. **底部延伸連結**:docs/API.md、MCP server、開放資料集(Releases)、授權 + attribution(沿用既有)。

### `CopyButton`(icon 版)
- 剪貼簿 SVG icon 按鈕;`onClick` 寫入剪貼簿,短暫顯示 ✓(打勾 icon 或「✓」字)再還原。aria-label「複製」。沿用既有 `navigator.clipboard`。

## 資料流 / 邊界
- 仍只讀 `/data/v1/manifest.json`(loadManifest)+ 點預覽時 `fetchEndpoint`(有界 endpointPreview)。無新資料、無後端。
- 預覽維持有界(只渲染摘要 + 第 1 筆 + 截斷,大檔不爆 DOM)。
- 錯誤狀態:manifest 載入失敗顯示訊息(非永久 skeleton);預覽失敗顯示訊息。

## 測試(照 dev-workflow)
- `web/src/lib/api-explorer.test.ts`:既有測試保留;新增 `jsExample` 斷言(含 base + path、為 fetch().then(r=>r.json()) 形式)。
- 流程:`vitest` → astro build(/api 產出)→ 瀏覽器抽查 /api:hero/Base URL 複製 icon、規模 badge、點端點展開看到 curl/Python/JS 三段各有複製 icon、索引端點預覽、樣板端點「需 id」。

## YAGNI(不做)
- 不做後端/serverless、OpenAPI、語言切換 tab(三段並列即可)、樣板端點頁內預覽(維持連結)、把大檔整包渲染。
- 不改 `docs/API.md`(完整規格仍在那;/api 是門面)。

## 未來待辦
- 若範例語言增多,再考慮 tab 切換而非並列三段。
