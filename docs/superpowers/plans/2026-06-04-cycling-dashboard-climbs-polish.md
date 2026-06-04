# 公路車儀表板 — Plan 5:招牌爬坡頁 + RWD/打磨 + 效能(部署前止步)實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 補上招牌爬坡頁 `/climbs`(武嶺/KOM 全民時間分布 + 「你贏過多少%」percentile),做手機 RWD 與打磨(清死碼、補測試、防呆),並做低風險的 ECharts 程式碼分割。**本 plan 不含實際部署**——做完後停下來與使用者討論部署細節。

**Architecture:** `climbs.astro` 掛 `client:only="react"` 的 `ClimbsApp`,載入 `races.json`、以 `isClimbRace()` 篩出傳奇爬坡賽,選一場 → lazy load 其 detail 檔,以 **percentile 為主角** 呈現(沿用既有 `PercentileWidget`/`RaceTimeHistogram`/`Podium`/`Leaderboard`)。RWD 靠既有 Tailwind 響應式類別 + 少量調整;效能用 Vite `manualChunks` 把 echarts 切成獨立快取 chunk。

**Tech Stack:** Astro 6 · React 19 islands · ECharts · Vitest。沿用既有 lib/components。

設計依據:`docs/superpowers/specs/2026-06-04-cycling-dashboard-design.md` 頁 D + §8(RWD/效能)。

---

## 檔案結構(本 plan 建立/修改)

```
web/src/lib/
  climbs.ts              isClimbRace / climbRaces(純函式)
  climbs.test.ts         Vitest
  racedetail.ts          移除未使用的 podium() 匯出(改)
  racedetail.test.ts     移除 podium 測試(改)
  aggregate.test.ts      補 raceSpread 電輔車 排除測試(改)
web/src/components/
  climbs/ClimbsApp.tsx    招牌爬坡 orchestrator
  charts/FinishTimeHistogram.tsx  tooltip 防呆(改)
web/src/pages/climbs.astro        /climbs 頁
web/astro.config.mjs              Vite manualChunks + chunkSizeWarningLimit(改)
web/src/layouts/Base.astro        手機 nav/標題微調(改)
```

---

## Task 1:招牌爬坡偵測(TDD)

**Files:**
- Create: `web/src/lib/climbs.ts`, `web/src/lib/climbs.test.ts`

- [ ] **Step 1: 寫失敗測試** — `web/src/lib/climbs.test.ts`

```ts
import { describe, it, expect } from "vitest";
import { isClimbRace, climbRaces } from "./climbs";
import type { RaceIndex } from "./types";

function r(p: Partial<RaceIndex>): RaceIndex {
  return { rk: "k", y: 2025, rn: "賽", s: "S", rows: 100, multi_year: false, has_team: false, file: "k__2025", ...p };
}

describe("isClimbRace", () => {
  it("matches legendary climbs by name", () => {
    expect(isClimbRace("2025 TIS崇越盃武嶺自行車挑戰賽")).toBe(true);
    expect(isClimbRace("臺灣KOM登山王之路-春季")).toBe(true);
    expect(isClimbRace("臺灣KOM太平洋經典賽")).toBe(true);
    expect(isClimbRace("96聯賽武嶺站")).toBe(true);
    expect(isClimbRace("環花東國際自行車賽")).toBe(false);
    expect(isClimbRace(null)).toBe(false);
  });
});

describe("climbRaces", () => {
  it("filters + sorts by year desc then rows desc", () => {
    const list = climbRaces([
      r({ rn: "武嶺A", y: 2024, rows: 100 }),
      r({ rn: "武嶺B", y: 2025, rows: 50 }),
      r({ rn: "環花東", y: 2025, rows: 999 }),
    ]);
    expect(list.map((x) => x.rn)).toEqual(["武嶺B", "武嶺A"]);
  });
});
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd web && npm test`
Expected: FAIL(無 `./climbs`)

- [ ] **Step 3: 實作** — `web/src/lib/climbs.ts`

```ts
import type { RaceIndex } from "./types";

const CLIMB_RE = /武嶺|KOM|登山王|塔塔加|大禹嶺|爬坡/i;

export function isClimbRace(rn: string | null): boolean {
  return !!rn && CLIMB_RE.test(rn);
}

export function climbRaces(races: RaceIndex[]): RaceIndex[] {
  return races
    .filter((r) => isClimbRace(r.rn))
    .sort((a, b) => (b.y ?? 0) - (a.y ?? 0) || b.rows - a.rows);
}
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd web && npm test`
Expected: PASS(全綠)

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/lib/climbs.ts web/src/lib/climbs.test.ts
git commit -m "feat(web): climb-race detection (tested)"
```

---

## Task 2:ClimbsApp + /climbs 頁

**Files:**
- Create: `web/src/components/climbs/ClimbsApp.tsx`, `web/src/pages/climbs.astro`

- [ ] **Step 1: ClimbsApp** — `web/src/components/climbs/ClimbsApp.tsx`

```tsx
import { useEffect, useState } from "react";
import "../../lib/echarts-theme";
import { loadRaces, loadRaceDetail } from "../../lib/data-load";
import { climbRaces } from "../../lib/climbs";
import type { RaceIndex, DetailRow } from "../../lib/types";
import PercentileWidget from "../race/PercentileWidget";
import RaceTimeHistogram from "../race/RaceTimeHistogram";
import Podium from "../race/Podium";
import Leaderboard from "../race/Leaderboard";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

export default function ClimbsApp() {
  const [climbs, setClimbs] = useState<RaceIndex[]>([]);
  const [sel, setSel] = useState<RaceIndex | null>(null);
  const [detail, setDetail] = useState<DetailRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadRaces().then((rs) => {
      const cl = climbRaces(rs);
      setClimbs(cl);
      const p = new URLSearchParams(location.search);
      const rk = p.get("rk"), y = p.get("y");
      const m = cl.find((r) => r.rk === rk && String(r.y) === y) ?? cl[0];
      if (m) pick(m, false);
    }).catch((e) => setErr(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function pick(r: RaceIndex, pushUrl = true) {
    setSel(r); setDetail(null);
    if (pushUrl) history.pushState(null, "", `?rk=${encodeURIComponent(r.rk)}&y=${r.y}`);
    loadRaceDetail(r.file).then(setDetail).catch((e) => setErr(String(e)));
  }

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!climbs.length) return <p className="text-muted">載入中…</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {climbs.map((r) => (
          <button key={r.file} onClick={() => pick(r)}
            className={`rounded-lg border px-3 py-2 text-sm ${
              sel && sel.file === r.file ? "border-accent text-accent" : "border-border text-ink hover:border-accent"
            }`}>
            {r.y} {r.rn} <span className="num text-muted">({r.rows})</span>
          </button>
        ))}
      </div>

      {sel && (
        <>
          <h1 className="font-display text-2xl text-ink">{sel.y} {sel.rn}</h1>
          {!detail ? <p className="text-muted">載入成績…</p> : (
            <div className="space-y-6">
              <Card title="你贏過多少%" hint="輸入你的爬坡完賽時間,看落在所有完賽者的前幾%">
                <PercentileWidget rows={detail} />
              </Card>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card title="全民完賽時間分布" hint="每 5 分鐘一桶"><RaceTimeHistogram rows={detail} /></Card>
                <Card title="領獎台"><Podium rows={detail} /></Card>
              </div>
              <Card title="排行榜"><Leaderboard rows={detail} /></Card>
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: /climbs 頁** — `web/src/pages/climbs.astro`

```astro
---
import Base from "../layouts/Base.astro";
import ClimbsApp from "../components/climbs/ClimbsApp.tsx";
---
<Base title="傳奇爬坡 | 台灣公路車賽事成績儀表板">
  <h1 class="font-display text-3xl">傳奇爬坡</h1>
  <p class="mt-2 mb-6 text-muted">武嶺、KOM 登山王等台灣招牌爬坡賽。輸入你的完賽時間,看你在全民中的落點。</p>
  <ClimbsApp client:only="react" />
</Base>
```

- [ ] **Step 3: build + 型別 + 測試**

Run: `cd web && npm run build && npx astro check && npm test`
Expected: build 成功(`dist/climbs/index.html`);astro check 0 errors;vitest 全綠。

- [ ] **Step 4: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/climbs/ClimbsApp.tsx web/src/pages/climbs.astro
git commit -m "feat(web): legendary climbs page (percentile-first)"
```

---

## Task 3:清死碼 + 補測試 + 防呆

**Files:**
- Modify: `web/src/lib/racedetail.ts`, `web/src/lib/racedetail.test.ts`, `web/src/lib/aggregate.test.ts`, `web/src/components/charts/FinishTimeHistogram.tsx`

- [ ] **Step 1: 移除未使用的 `podium()`** — `web/src/lib/racedetail.ts`:刪除 `export function podium(...)` 整個函式(已被 `categoryPodium` 取代,無元件使用)。保留 `PodiumEntry`(仍被 `categoryPodium` 回傳型別使用)、`categoriesOf`、`largestCategory`、`categoryPodium`、`teamStrength`、`crossYear`。
   並在 `web/src/lib/racedetail.test.ts` 移除 `describe("podium", ...)` 區塊與 import 中的 `podium`。

- [ ] **Step 2: 補 raceSpread 電輔車 排除測試** — 在 `web/src/lib/aggregate.test.ts` 的 `describe("raceSpread", ...)` 內追加:

```ts
  it("excludes 電輔車 race_class", () => {
    const rows = [
      ...Array.from({ length: 10 }, (_, i) => ({ rk: "E", y: 2025, t: 100 + i, rc: "電輔車", s: "96聯賽" })),
    ];
    expect(raceSpread(rows, 10)).toEqual([]);
  });
```
(若既有測試的 row 物件沒有 `s` 欄位,請一併補 `s: null`,使型別一致;raceSpread 的 row 型別含 `s`。)

- [ ] **Step 3: FinishTimeHistogram tooltip 防呆** — `web/src/components/charts/FinishTimeHistogram.tsx`,在 tooltip formatter 內加守衛(與 AgeBoxplot 一致):
把
```tsx
      formatter: (p: any) => {
        const b = bins[p[0].dataIndex];
        return `${secondsToHMS(b.x0)}–${secondsToHMS(b.x1)}<br/>${p[0].value} 人`;
      },
```
改成
```tsx
      formatter: (p: any) => {
        const b = bins[p[0].dataIndex];
        if (!b) return "";
        return `${secondsToHMS(b.x0)}–${secondsToHMS(b.x1)}<br/>${p[0].value} 人`;
      },
```

- [ ] **Step 4: 測試 + 型別**

Run: `cd web && npm test && npx astro check`
Expected: vitest 全綠(podium 測試已移除、新增電輔車測試通過);astro check 0 errors(確認 racedetail 無 podium 殘留引用)。

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/lib/racedetail.ts web/src/lib/racedetail.test.ts web/src/lib/aggregate.test.ts web/src/components/charts/FinishTimeHistogram.tsx
git commit -m "chore(web): remove dead podium export, add 電輔車 test, histogram tooltip guard"
```

---

## Task 4:RWD 微調 + ECharts 程式碼分割

**Files:**
- Modify: `web/src/layouts/Base.astro`, `web/astro.config.mjs`

- [ ] **Step 1: 手機版 header** — `web/src/layouts/Base.astro`,讓標題在手機縮小、nav 可換行(改 header 區塊):
把
```astro
    <header class="border-b border-border px-6 py-4">
      <a href="/" class="font-display text-xl text-ink">{siteTitle}</a>
      <nav class="mt-1 flex gap-4 text-sm text-muted">
        <a href="/">總覽</a><a href="/explore">探索</a>
        <a href="/race">賽事</a><a href="/climbs">傳奇爬坡</a>
      </nav>
    </header>
```
改成
```astro
    <header class="border-b border-border px-4 py-3 sm:px-6 sm:py-4">
      <a href="/" class="font-display text-lg text-ink sm:text-xl">{siteTitle}</a>
      <nav class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
        <a href="/" class="hover:text-accent">總覽</a><a href="/explore" class="hover:text-accent">探索</a>
        <a href="/race" class="hover:text-accent">賽事</a><a href="/climbs" class="hover:text-accent">傳奇爬坡</a>
      </nav>
    </header>
```
並把 `<main class="mx-auto max-w-6xl px-6 py-8">` 改為 `<main class="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">`。

- [ ] **Step 2: ECharts 切 chunk** — `web/astro.config.mjs`,在 config 物件加(或合併進既有 `vite` 設定):

```js
  vite: {
    build: {
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: { manualChunks: { echarts: ["echarts", "echarts-for-react"] } },
      },
    },
  },
```
(若 `astro.config.mjs` 已有 `vite` 或其他鍵,請合併而非覆蓋;tailwind 的 vite plugin 等設定要保留。)

- [ ] **Step 3: build 驗證** — `cd web && npm run build`
Expected: build 成功;輸出可見獨立的 `echarts-*.js` chunk;不再出現(或大幅降低)chunk-size 警告。`npx astro check` 0 errors。

- [ ] **Step 4: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/layouts/Base.astro web/astro.config.mjs
git commit -m "perf(web): split echarts chunk; chore: mobile header tweaks"
```

---

## Task 5:端到端驗證(控制端執行,含手機視窗)

- [ ] **Step 1: 啟 preview 並驗證**

啟 `cd web && npm run preview`(背景):
- `/climbs`:顯示武嶺/KOM 爬坡賽清單,預設選第一場 → percentile 卡為主角、時間分布、領獎台、排行榜皆繪出。輸入時間 → 「你贏過 X%」。
- 手機視窗(resize 至 ~390px 寬):總覽/探索/賽事/爬坡四頁——nav 換行正常、圖表單欄堆疊、表格可橫向捲、篩選器換行不溢出。
- 既有三頁 regression:總覽 KPI、探索篩選聯動、賽事 percentile 仍正常。
驗證後關閉 preview。

---

## ⛔ 部署前止步(STOP — 不要自動部署)

完成 Task 1–5 並合併後,**不要執行任何部署**。改為向使用者回報「儀表板四頁完成」,並提出部署待討論的細節清單,等使用者決定後再進行:
- Vercel 專案設定:root directory = `web/`,framework preset = Astro,build = `astro build`,output = `dist`。
- 資料檔策略:`web/public/data/*`(gitignored)需在部署前產生——是 commit 進去、還是在 CI build step 跑 `python build_viz.py`?(Vercel 預設無 Python;最簡單是把 `web/public/data` 改為**部署用**納入版控,或改 build 流程。)← 需與使用者討論。
- 網域、是否公開、PDPA 頁尾(資料來源 + 下架聯絡)。
- 是否先 `git push` 到 GitHub(目前無遠端)。

---

## 完成標準(Plan 5,部署除外)

- `/climbs` 招牌爬坡頁完成(percentile 為主角 + 分布 + 領獎台 + 排行榜)。
- 四頁皆有手機 RWD;ECharts 切成獨立 chunk、chunk 警告消除。
- 死碼(`podium()`)移除;`raceSpread` 電輔車 測試與 histogram 防呆補上。
- `npm test` / `npx astro check` / `npm run build` 全通過。
- **未部署**;部署細節待與使用者討論。

---

## Self-Review(對照 spec 頁 D + §8)

- C8 武嶺/KOM 全民時間分布 + percentile → Task 1 isClimbRace + Task 2 ClimbsApp(沿用 PercentileWidget/RaceTimeHistogram)✓
- §8 RWD/手機 → Task 4 header + 既有響應式 grid/flex/overflow;Task 5 手機視窗驗證 ✓
- §8 效能 → Task 4 echarts 獨立 chunk(快取);字體已 display:swap ✓
- 打磨/清理 → Task 3 移除死碼 pod()、補測試、防呆 ✓
- 部署 → 明確止步,待討論(符合使用者指示)✓
- Placeholder 掃描:每步含完整程式;無 TBD。
- 型別一致:`RaceIndex`/`DetailRow` 沿用;`isClimbRace/climbRaces` 由 climbs.ts 匯出;ClimbsApp 重用 race 子元件(DRY)。
