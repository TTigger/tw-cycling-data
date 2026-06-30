# /api 探索頁 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增前端頁 `/api`:讀現有 `manifest.json`,呈現規模卡 + 端點表 + 頁內即時 JSON 預覽 + 複製即用範例 + 延伸連結,讓公開 API 好入門。

**Architecture:** 純前端、無新資料。型別 + loaders(`loadManifest`/`fetchEndpoint`)+ 純函式 `api-explorer.ts`(`isTemplated`/`endpointPreview`/範例字串)+ self-loading island `ApiExplorer.tsx` + `api.astro` 頁 + 導覽連結。

**Tech Stack:** Astro + React island + TypeScript + vitest;讀 `/data/v1/manifest.json`。

## Global Constraints

- **純前端、不動資料**:只讀既有公開檔(`/data/v1/*.json`)。
- **預覽有界**:`endpointPreview` 只渲染摘要 + 第 1 筆/截斷(maxChars=1500),即使 fetch 回 3.9MB 也不把整包塞進 DOM。
- **樣板明細端點(path 含 `{`)不做頁內預覽**(需 id),改標註 + 連結。
- 規模數字一律來自 `manifest.stats`(不寫死)。
- self-loading island 慣例(useEffect + `Skeleton`,錯誤狀態避免永久 skeleton),沿用 `InsightsApp`/`TrendsApp`。
- 沿用既有 `data-load.ts` 的私有 `API` base 常數(`${base}/data/v1`)。
- 既有測試:`vitest` 綠、astro build 成功、瀏覽器抽查;每 task 自己 commit。

## 已確認的現況

- `manifest.json` 鍵:`api_version, dataset, homepage, license, attribution, stats{records,races,race_editions,series,athletes,teams,sources,year_min,year_max}, endpoints[{path,kind,description}]`。
- endpoints 路徑:索引/meta(`manifest.json,overview.json,races.json,athletes.json,teams.json,series.json,coverage.json,benchmarks.json`)+ 樣板(`race/{race_key}.json,athlete/{athlete_id}.json,team/{team_id}.json`,含 `{`)。
- `data-load.ts` 頂部已有 `const API = `${base}/data/v1`;`,所有 loader 用它。island 用 `Skeleton`(`web/src/components/Skeleton.tsx`,有 `cards` prop)。導覽在 `web/src/layouts/Base.astro`(`/trends` 連結之後可加 `/api`)。

---

## File Structure

**修改:** `web/src/lib/types.ts`(Manifest 型別)、`web/src/lib/data-load.ts`(`loadManifest`/`fetchEndpoint`)、`web/src/layouts/Base.astro`(導覽)
**新增:** `web/src/lib/api-explorer.ts`、`web/src/lib/api-explorer.test.ts`、`web/src/components/api/ApiExplorer.tsx`、`web/src/pages/api.astro`

---

## Task 1: 型別 + loaders + 純函式

可測的純函式 + 資料載入。交付物:型別/loaders/`api-explorer.ts` + vitest。

**Files:**
- Modify: `web/src/lib/types.ts`(Manifest 型別)
- Modify: `web/src/lib/data-load.ts`(`loadManifest`、`fetchEndpoint`)
- Create: `web/src/lib/api-explorer.ts`
- Test: `web/src/lib/api-explorer.test.ts`

**Interfaces:**
- Produces:
  - 型別 `Manifest`/`ManifestStats`/`ManifestEndpoint`(types.ts)
  - `loadManifest(): Promise<Manifest>`、`fetchEndpoint(path: string): Promise<unknown>`(data-load.ts)
  - `isTemplated(path: string): boolean`、`endpointPreview(data: unknown, maxChars?: number): {summary: string; body: string}`、`curlExample(base: string, path: string): string`、`pythonExample(base: string, path: string): string`(api-explorer.ts)

- [ ] **Step 1: Add Manifest types to `web/src/lib/types.ts`**

於檔末新增:

```ts
export interface ManifestEndpoint { path: string; kind: string; description: string; }
export interface ManifestStats {
  records: number; races: number; race_editions: number; series: number;
  athletes: number; teams: number; sources: number; year_min: number; year_max: number;
}
export interface Manifest {
  api_version: string; dataset: string; homepage: string; license: string;
  attribution: string; stats: ManifestStats; endpoints: ManifestEndpoint[];
}
```

- [ ] **Step 2: Write the failing test**

`web/src/lib/api-explorer.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { isTemplated, endpointPreview, curlExample, pythonExample } from "./api-explorer";

describe("isTemplated", () => {
  it("flags templated detail paths", () => {
    expect(isTemplated("race/{race_key}.json")).toBe(true);
    expect(isTemplated("races.json")).toBe(false);
  });
});

describe("endpointPreview", () => {
  it("summarises an array and shows the first element", () => {
    const r = endpointPreview([{ a: 1 }, { a: 2 }, { a: 3 }]);
    expect(r.summary).toContain("3");          // count present
    expect(r.body).toContain('"a": 1');        // first element pretty-printed
    expect(r.body).not.toContain('"a": 2');    // only the first element
  });
  it("summarises an object by its top-level keys", () => {
    const r = endpointPreview({ x: 1, y: 2 });
    expect(r.summary).toContain("x");
    expect(r.body).toContain('"x": 1');
  });
  it("truncates long bodies with an ellipsis", () => {
    const big = [{ s: "z".repeat(5000) }];
    const r = endpointPreview(big, 200);
    expect(r.body.length).toBeLessThanOrEqual(201);  // 200 + ellipsis char
    expect(r.body.endsWith("…")).toBe(true);
  });
  it("handles empty/null safely", () => {
    expect(endpointPreview([]).summary).toContain("0");
    expect(() => endpointPreview(null)).not.toThrow();
  });
});

describe("examples", () => {
  it("embed base + path", () => {
    const base = "https://tw-cycling-data.vercel.app/data/v1";
    expect(curlExample(base, "races.json")).toContain(`${base}/races.json`);
    expect(pythonExample(base, "races.json")).toContain(`${base}/races.json`);
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd web && npx vitest run src/lib/api-explorer.test.ts`
Expected: FAIL (cannot resolve `./api-explorer`)

- [ ] **Step 4: Implement `web/src/lib/api-explorer.ts`**

```ts
/** Pure helpers for the /api explorer page — no fetch, fully unit-testable. */

/** A templated detail path needs an id (e.g. race/{race_key}.json). */
export function isTemplated(path: string): boolean {
  return path.includes("{");
}

function truncate(s: string, maxChars: number): string {
  return s.length > maxChars ? s.slice(0, maxChars) + "…" : s;
}

/** Bounded preview of a fetched endpoint: a one-line summary + a pretty-printed,
 * truncated body. For arrays, only the FIRST element is rendered (so a 3.9MB
 * index never floods the DOM). */
export function endpointPreview(
  data: unknown, maxChars = 1500,
): { summary: string; body: string } {
  if (Array.isArray(data)) {
    const first = data.length ? JSON.stringify(data[0], null, 2) : "(空陣列)";
    return { summary: `陣列,共 ${data.length} 筆${data.length ? ";顯示第 1 筆:" : ""}`,
             body: truncate(first, maxChars) };
  }
  if (data && typeof data === "object") {
    const keys = Object.keys(data as Record<string, unknown>);
    return { summary: `物件,鍵:${keys.join(", ")}`,
             body: truncate(JSON.stringify(data, null, 2), maxChars) };
  }
  return { summary: "(無資料)", body: truncate(JSON.stringify(data ?? null, null, 2), maxChars) };
}

export function curlExample(base: string, path: string): string {
  return `curl ${base}/${path}`;
}

export function pythonExample(base: string, path: string): string {
  return `import requests\nr = requests.get("${base}/${path}")\ndata = r.json()`;
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd web && npx vitest run src/lib/api-explorer.test.ts`
Expected: PASS

- [ ] **Step 6: Add loaders to `web/src/lib/data-load.ts`**

於檔末新增(沿用既有私有 `API` 常數):

```ts
export async function loadManifest(): Promise<import("./types").Manifest> {
  const r = await fetch(`${API}/manifest.json`);
  if (!r.ok) throw new Error(`manifest.json ${r.status}`);
  return r.json();
}
export async function fetchEndpoint(path: string): Promise<unknown> {
  const r = await fetch(`${API}/${path}`);
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}
```

- [ ] **Step 7: Run vitest + commit**

Run: `cd web && npx vitest run src/lib/api-explorer.test.ts`
Expected: PASS（全綠)

```bash
git add web/src/lib/types.ts web/src/lib/data-load.ts web/src/lib/api-explorer.ts web/src/lib/api-explorer.test.ts
git commit -m "feat(api-page): Manifest types, loadManifest/fetchEndpoint, bounded preview helpers"
```

---

## Task 2: ApiExplorer 元件 + /api 頁 + 導覽

互動門面頁。交付物:`/api` 可用,瀏覽器抽查正確。

**Files:**
- Create: `web/src/components/api/ApiExplorer.tsx`
- Create: `web/src/pages/api.astro`
- Modify: `web/src/layouts/Base.astro`(導覽連結)

**Interfaces:**
- Consumes: `loadManifest`/`fetchEndpoint`(Task 1)、`isTemplated`/`endpointPreview`/`curlExample`/`pythonExample`(Task 1)、`Manifest` 型別、`Skeleton`(`web/src/components/Skeleton.tsx`)。

- [ ] **Step 1: Implement `web/src/components/api/ApiExplorer.tsx`**

```tsx
import { useEffect, useState } from "react";
import { loadManifest, fetchEndpoint } from "../../lib/data-load";
import { isTemplated, endpointPreview, curlExample, pythonExample } from "../../lib/api-explorer";
import type { Manifest, ManifestEndpoint } from "../../lib/types";
import Skeleton from "../Skeleton";

const BASE = "https://tw-cycling-data.vercel.app/data/v1";
const GH = "https://github.com/TTigger/tw-cycling-data";

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button type="button"
      onClick={() => { navigator.clipboard?.writeText(text); setDone(true); setTimeout(() => setDone(false), 1200); }}
      className="rounded border border-border px-2 py-0.5 text-xs text-muted hover:text-accent">
      {done ? "已複製" : "複製"}
    </button>
  );
}

function EndpointRow({ ep }: { ep: ManifestEndpoint }) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const [preview, setPreview] = useState<{ summary: string; body: string } | null>(null);
  const templated = isTemplated(ep.path);

  const onPreview = async () => {
    if (open) { setOpen(false); return; }
    setOpen(true); setState("loading"); setPreview(null);
    try {
      const data = await fetchEndpoint(ep.path);
      setPreview(endpointPreview(data));
      setState("idle");
    } catch {
      setState("error");
    }
  };

  return (
    <>
      <tr className="border-t border-border align-top">
        <td className="py-2 pr-3"><code className="text-accent">{ep.path}</code></td>
        <td className="py-2 pr-3 text-xs text-muted">{ep.kind}</td>
        <td className="py-2 pr-3">{ep.description}</td>
        <td className="py-2 whitespace-nowrap">
          {templated ? (
            <span className="text-xs text-muted">需 id(見 races/athletes/teams.json)</span>
          ) : (
            <span className="flex gap-2">
              <button type="button" onClick={onPreview}
                className="rounded border border-border px-2 py-0.5 text-xs hover:text-accent">
                {open ? "收合" : "預覽"}
              </button>
              <a href={`${BASE}/${ep.path}`} target="_blank" rel="noopener"
                className="text-xs text-muted hover:text-accent">開新分頁↗</a>
            </span>
          )}
        </td>
      </tr>
      {open && (
        <tr className="border-t border-border/50">
          <td colSpan={4} className="py-2">
            {state === "loading" && <p className="text-xs text-muted">載入中…</p>}
            {state === "error" && <p className="text-xs text-accent">載入失敗,請稍後再試。</p>}
            {preview && (
              <div className="space-y-1">
                <p className="text-xs text-muted">{preview.summary}</p>
                <pre className="overflow-auto rounded bg-surface p-2 text-xs">{preview.body}</pre>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

export default function ApiExplorer() {
  const [m, setM] = useState<Manifest | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    loadManifest().then(setM).catch(() => setFailed(true));
  }, []);

  if (failed) return <p className="text-accent">無法載入 API manifest,請稍後再試。</p>;
  if (!m) return <Skeleton cards={2} />;

  const s = m.stats;
  const stat = (label: string, v: number | string) => (
    <div className="rounded-lg border border-border bg-surface px-3 py-2">
      <div className="num text-lg text-ink">{v}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );

  return (
    <div className="space-y-6 text-sm">
      <section className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {stat("筆數", s.records.toLocaleString())}
        {stat("賽事", s.races)}
        {stat("賽事屆數", s.race_editions)}
        {stat("選手", s.athletes.toLocaleString())}
        {stat("車隊", s.teams.toLocaleString())}
        {stat("來源", s.sources)}
        {stat("年份", `${s.year_min}–${s.year_max}`)}
        {stat("授權", m.license)}
      </section>

      <section>
        <h2 className="font-display text-xl">端點</h2>
        <p className="mb-2 text-xs text-muted">Base:<code>{BASE}</code>。皆唯讀 JSON,帶 CORS,可直接跨網域 fetch。</p>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead><tr className="text-xs text-muted">
              <th className="py-1 pr-3">路徑</th><th className="py-1 pr-3">類型</th>
              <th className="py-1 pr-3">說明</th><th className="py-1"></th>
            </tr></thead>
            <tbody>{m.endpoints.map((ep) => <EndpointRow key={ep.path} ep={ep} />)}</tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="font-display text-xl">複製即用</h2>
        <div className="space-y-2">
          <div className="flex items-center gap-2"><span className="text-xs text-muted">curl</span>
            <CopyButton text={curlExample(BASE, "races.json")} /></div>
          <pre className="overflow-auto rounded bg-surface p-2 text-xs">{curlExample(BASE, "races.json")}</pre>
          <div className="flex items-center gap-2"><span className="text-xs text-muted">Python</span>
            <CopyButton text={pythonExample(BASE, "races.json")} /></div>
          <pre className="overflow-auto rounded bg-surface p-2 text-xs">{pythonExample(BASE, "races.json")}</pre>
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

- [ ] **Step 2: Implement `web/src/pages/api.astro`**

```astro
---
import Base from "../layouts/Base.astro";
import ApiExplorer from "../components/api/ApiExplorer.tsx";
---
<Base title="API | 台灣公路車賽事成績儀表板">
  <h1 class="font-display text-3xl">公開 API</h1>
  <p class="mt-2 mb-6 text-muted">唯讀 JSON API(去識別化,CC BY 4.0)。看規模、點開端點預覽真實資料、複製即用範例。完整規格見 docs/API.md。</p>
  <ApiExplorer client:only="react" />
</Base>
```

- [ ] **Step 3: Add the nav link in `web/src/layouts/Base.astro`**

在導覽列(`<a href="/trends" …>長期趨勢</a>` 之後)加入:

```astro
<a href="/api" class="py-1 hover:text-accent">API</a>
```

- [ ] **Step 4: Build + browser-verify /api**

Run: `npm --prefix web run build`
Expected: 成功,`/api/index.html` 產出。瀏覽器抽查 `/api`:規模卡顯示真實數字;點某索引端點(如 `races.json`)「預覽」→ 列下顯示摘要 + 第 1 筆 JSON;`benchmarks.json`/`athletes.json` 預覽不卡死(只渲染第 1 筆);樣板列(`race/{race_key}.json`)顯示「需 id」無預覽鈕;複製鈕顯示「已複製」。

- [ ] **Step 5: Commit**

```bash
git add web/src/components/api/ApiExplorer.tsx web/src/pages/api.astro web/src/layouts/Base.astro
git commit -m "feat(api-page): /api explorer — stats, endpoint table with live bounded preview, copy examples"
```

---

## Self-Review

**1. Spec coverage:** 規模卡(manifest.stats)→ Task 2 ✅;端點表 + 頁內即時有界預覽 → Task 1(endpointPreview)+ Task 2(EndpointRow)✅;樣板端點不預覽 → `isTemplated` 分支 ✅;複製範例 → curl/python + CopyButton ✅;延伸連結 + 授權一次 → Task 2 ✅;導覽 → Task 2 Step 3 ✅;純前端不動資料 → 只 fetch 既有檔 ✅;預覽有界(大檔不爆)→ endpointPreview 只取第 1 筆 + 截斷 ✅。

**2. Placeholder scan:** 無 TBD;每步附完整程式。

**3. Type consistency:** `Manifest`/`ManifestStats`/`ManifestEndpoint`(Task 1 types.ts)被 `loadManifest`、`ApiExplorer` 一致使用;`endpointPreview` 回 `{summary, body}` 在 Task 1 定義、Task 2 的 EndpointRow 一致取用;`fetchEndpoint(path)`/`isTemplated`/`curl|pythonExample` 簽名兩 task 一致;`BASE` 字串與 data-load 的 `API`(`${base}/data/v1`)在 production 相同(頁面用絕對 BASE 顯示/連結,fetch 走 data-load 的相對 API — 兩者皆指向 /data/v1)。

---

## 執行順序
Task 1 → 2。Task 1 提供型別/loaders/純函式(Task 2 的 UI 依賴)。
