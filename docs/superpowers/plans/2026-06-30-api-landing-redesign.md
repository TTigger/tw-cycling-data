# /api 改套件 landing page 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `/api` 改成套件 landing 樣式:快速上手 hero + 規模 badge、端點表格每列展開顯示該端點 curl/Python/JS 範例、複製改 icon 按鈕。

**Architecture:** 純前端,改 `ApiExplorer.tsx` 一個元件 + 在 `api-explorer.ts` 加一個純函式 `jsExample`。重用既有 `curlExample/pythonExample/isTemplated/endpointPreview` 與 `loadManifest/fetchEndpoint`。

**Tech Stack:** Astro + React island + TypeScript + vitest。

## Global Constraints

- 純前端、不動資料/後端;仍只讀 `/data/v1/manifest.json`(+ 點預覽時 `fetchEndpoint`)。
- 預覽維持**有界**(`endpointPreview`:摘要 + 第 1 筆 + 截斷,大檔不爆 DOM)。
- 複製按鈕為 **icon**(剪貼簿 SVG,複製後顯示 ✓),有 `aria-label`。
- 每端點展開列顯示 **curl / Python / JS** 三段,各有複製 icon;樣板端點(`isTemplated`)以樣板路徑 + 「需 id」連結替代頁內預覽。
- 錯誤狀態不為永久 skeleton(manifest 失敗顯示訊息)。
- 既有 vitest 保留綠;build 產出 /api。

## 已確認的現況

- `web/src/lib/api-explorer.ts`:有 `isTemplated`、`endpointPreview`、`curlExample(base,path)`、`pythonExample(base,path)`;`api-explorer.test.ts` 已有 6+ 測試。
- `web/src/components/api/ApiExplorer.tsx`:現為規模卡 + 端點表(path/kind/desc/preview)+ 單一全域 curl/python 範例(文字「複製」鈕)+ 底部連結。`BASE`/`GH` 常數在檔內。
- `manifest.stats` 欄位:records/races/race_editions/athletes/teams/sources/year_min/year_max;`m.license`/`m.attribution`。

---

## File Structure

**修改:** `web/src/lib/api-explorer.ts`(加 `jsExample`)、`web/src/lib/api-explorer.test.ts`(加斷言)、`web/src/components/api/ApiExplorer.tsx`(改版)

---

## Task 1: `jsExample` 純函式

逐端點 JS fetch 範例。交付物:`jsExample` + 測試。

**Files:**
- Modify: `web/src/lib/api-explorer.ts`
- Test: `web/src/lib/api-explorer.test.ts`

**Interfaces:**
- Produces:`jsExample(base: string, path: string): string`。

- [ ] **Step 1: Add the failing test**

在 `web/src/lib/api-explorer.test.ts` 既有 `describe("examples", ...)`(或檔末)加:

```ts
import { jsExample } from "./api-explorer";

describe("jsExample", () => {
  it("embeds base + path in a fetch().then(r=>r.json()) snippet", () => {
    const base = "https://tw-cycling-data.vercel.app/data/v1";
    const s = jsExample(base, "races.json");
    expect(s).toContain(`${base}/races.json`);
    expect(s).toContain("fetch(");
    expect(s).toContain(".json()");
  });
});
```
(若該檔頂部已 `import { ... } from "./api-explorer"`,把 `jsExample` 併入既有 import,勿重複 import 區塊。)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npx vitest run src/lib/api-explorer.test.ts`
Expected: FAIL(`jsExample` 未匯出)

- [ ] **Step 3: Implement `jsExample` in `web/src/lib/api-explorer.ts`**

於檔末(`pythonExample` 之後)新增:

```ts
export function jsExample(base: string, path: string): string {
  return `fetch("${base}/${path}")\n  .then(r => r.json())\n  .then(console.log);`;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npx vitest run src/lib/api-explorer.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/api-explorer.ts web/src/lib/api-explorer.test.ts
git commit -m "feat(api-page): jsExample fetch snippet helper"
```

---

## Task 2: `ApiExplorer.tsx` 改版

套件 landing 版面 + icon 複製 + 逐端點範例。交付物:/api 改版,build 綠 + 瀏覽器抽查。

**Files:**
- Modify: `web/src/components/api/ApiExplorer.tsx`(整檔改版)

**Interfaces:**
- Consumes:`loadManifest`/`fetchEndpoint`、`isTemplated`/`endpointPreview`/`curlExample`/`pythonExample`/`jsExample`(Task 1)、`Manifest`/`ManifestEndpoint` 型別、`Skeleton`。

- [ ] **Step 1: Replace `web/src/components/api/ApiExplorer.tsx` with the redesigned component**

整檔換成:

```tsx
import { useEffect, useState } from "react";
import { loadManifest, fetchEndpoint } from "../../lib/data-load";
import { isTemplated, endpointPreview, curlExample, pythonExample, jsExample } from "../../lib/api-explorer";
import type { Manifest, ManifestEndpoint } from "../../lib/types";
import Skeleton from "../Skeleton";

const BASE = "https://tw-cycling-data.vercel.app/data/v1";
const GH = "https://github.com/TTigger/tw-cycling-data";

function CopyButton({ text, label = "複製" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button type="button" aria-label={label} title={label}
      onClick={() => { navigator.clipboard?.writeText(text); setDone(true); setTimeout(() => setDone(false), 1200); }}
      className="rounded border border-border p-1 text-muted hover:text-accent">
      {done ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></svg>
      )}
    </button>
  );
}

function Snippet({ label, code }: { label: string; code: string }) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-muted">{label}</span>
        <CopyButton text={code} label={`複製 ${label}`} />
      </div>
      <pre className="mt-1 overflow-auto rounded bg-surface p-2 text-xs">{code}</pre>
    </div>
  );
}

function EndpointRow({ ep }: { ep: ManifestEndpoint }) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const [preview, setPreview] = useState<{ summary: string; body: string } | null>(null);
  const templated = isTemplated(ep.path);

  const onPreview = async () => {
    setState("loading"); setPreview(null);
    try { setPreview(endpointPreview(await fetchEndpoint(ep.path))); setState("idle"); }
    catch { setState("error"); }
  };

  return (
    <>
      <tr className="border-t border-border align-top">
        <td className="py-2 pr-3"><code className="text-accent">{ep.path}</code></td>
        <td className="py-2 pr-3 text-xs text-muted">{ep.kind}</td>
        <td className="py-2 pr-3">{ep.description}</td>
        <td className="py-2 whitespace-nowrap">
          <button type="button" onClick={() => setOpen((o) => !o)}
            className="rounded border border-border px-2 py-0.5 text-xs hover:text-accent">
            {open ? "收合" : "範例"}
          </button>
        </td>
      </tr>
      {open && (
        <tr className="border-t border-border/50">
          <td colSpan={4} className="py-3">
            <div className="space-y-2">
              <Snippet label="curl" code={curlExample(BASE, ep.path)} />
              <Snippet label="Python" code={pythonExample(BASE, ep.path)} />
              <Snippet label="JS" code={jsExample(BASE, ep.path)} />
              {templated ? (
                <p className="text-xs text-muted">
                  路徑含 <code>{"{…}"}</code> 佔位,需 id —— 見{" "}
                  <a className="hover:text-accent" href={`${BASE}/races.json`} target="_blank" rel="noopener noreferrer">races.json</a>{" / "}
                  <a className="hover:text-accent" href={`${BASE}/athletes.json`} target="_blank" rel="noopener noreferrer">athletes.json</a>{" / "}
                  <a className="hover:text-accent" href={`${BASE}/teams.json`} target="_blank" rel="noopener noreferrer">teams.json</a>。
                </p>
              ) : (
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <button type="button" onClick={onPreview}
                      className="rounded border border-border px-2 py-0.5 text-xs hover:text-accent">即時預覽</button>
                    <a href={`${BASE}/${ep.path}`} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-muted hover:text-accent">開新分頁↗</a>
                  </div>
                  {state === "loading" && <p className="text-xs text-muted">載入中…</p>}
                  {state === "error" && <p className="text-xs text-accent">載入失敗,請稍後再試。</p>}
                  {preview && (
                    <div className="space-y-1">
                      <p className="text-xs text-muted">{preview.summary}</p>
                      <pre className="overflow-auto rounded bg-surface p-2 text-xs">{preview.body}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function ApiExplorer() {
  const [m, setM] = useState<Manifest | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { loadManifest().then(setM).catch(() => setFailed(true)); }, []);

  if (failed) return <p className="text-accent">無法載入 API manifest,請稍後再試。</p>;
  if (!m) return <Skeleton cards={2} />;

  const s = m.stats;
  const badge = (label: string, v: number | string) => (
    <span key={label} className="rounded-full border border-border bg-surface px-2.5 py-1 text-xs">
      <span className="num text-ink">{v}</span> <span className="text-muted">{label}</span>
    </span>
  );

  return (
    <div className="space-y-6 text-sm">
      <section className="space-y-3">
        <p className="text-muted">唯讀 JSON API;帶 CORS,可直接跨網域 fetch。去識別化,CC BY 4.0。</p>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted">Base URL</span>
          <code className="rounded bg-surface px-2 py-1 text-xs text-accent">{BASE}</code>
          <CopyButton text={BASE} label="複製 Base URL" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted">10 秒上手</span>
            <CopyButton text={jsExample(BASE, "races.json")} label="複製範例" />
          </div>
          <pre className="mt-1 overflow-auto rounded bg-surface p-2 text-xs">{jsExample(BASE, "races.json")}</pre>
        </div>
      </section>

      <section className="flex flex-wrap gap-2">
        {badge("筆數", s.records.toLocaleString())}
        {badge("賽事", s.races)}
        {badge("屆數", s.race_editions)}
        {badge("選手", s.athletes.toLocaleString())}
        {badge("車隊", s.teams.toLocaleString())}
        {badge("來源", s.sources)}
        {badge("年份", `${s.year_min}–${s.year_max}`)}
        {badge("授權", m.license)}
      </section>

      <section>
        <h2 className="font-display text-xl">端點</h2>
        <p className="mb-2 text-xs text-muted">點「範例」看該端點的 curl / Python / JS 與即時預覽。Base:<code>{BASE}</code></p>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead><tr className="text-xs text-muted">
              <th className="py-1 pr-3">路徑</th><th className="py-1 pr-3">類型</th>
              <th className="py-1 pr-3">說明</th><th className="py-1">範例</th>
            </tr></thead>
            <tbody>{m.endpoints.map((ep) => <EndpointRow key={ep.path} ep={ep} />)}</tbody>
          </table>
        </div>
      </section>

      <section className="text-xs text-muted">
        延伸:<a className="hover:text-accent" href={`${GH}/blob/master/docs/API.md`}>完整 API 文件</a>・
        <a className="hover:text-accent" href={`${GH}/tree/master/mcp-server`}>MCP server</a>・
        <a className="hover:text-accent" href={`${GH}/releases`}>開放資料集(Releases)</a>・
        授權 {m.license}({m.attribution})。
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Build + browser-verify**

Run: `npm --prefix web run build`
Expected: 成功,`/api/index.html` 產出。瀏覽器抽查 `/api`:
- Hero:Base URL + 複製 icon、10 秒上手 snippet + 複製 icon。
- 規模 badge 列顯示真實數字。
- 端點表點「範例」→ 展開顯示 curl / Python / JS 三段,各有複製 icon(點擊變 ✓);索引端點有「即時預覽」(點開顯示摘要 + 第 1 筆);樣板端點(`race/{race_key}.json`)顯示佔位說明 + 連結,無預覽鈕。
- 複製 icon 點擊真的寫入剪貼簿(可貼上驗證)。

- [ ] **Step 3: Commit**

```bash
git add web/src/components/api/ApiExplorer.tsx
git commit -m "feat(api-page): package landing layout — hero, badges, per-endpoint curl/Python/JS, icon copy"
```

---

## Self-Review

**1. Spec coverage:** hero/快速上手 + Base URL 複製 → Task 2 §hero ✅;規模 badge → §badge ✅;端點表格保留 + 展開逐端點 curl/Python/JS → EndpointRow ✅;複製 icon(✓ 回饋)→ CopyButton ✅;即時預覽有界 → endpointPreview ✅;樣板端點佔位 + 連結 → templated 分支 ✅;`jsExample` → Task 1 ✅;底部連結 → §footer ✅;純前端不動資料 → 只讀 manifest/fetchEndpoint ✅。

**2. Placeholder scan:** 無 TBD;Task 2 提供整檔完整程式。

**3. Type consistency:** `jsExample(base,path)`(Task 1)被 ApiExplorer 引用一致;`curlExample/pythonExample/isTemplated/endpointPreview` 簽名沿用既有;`Manifest`/`ManifestEndpoint`/`manifest.stats` 欄位沿用既有(records/races/race_editions/athletes/teams/sources/year_min/year_max/license/attribution)。

---

## 執行順序
Task 1(jsExample)→ Task 2(改版,依賴 jsExample)。
