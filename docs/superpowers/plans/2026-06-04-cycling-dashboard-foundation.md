# 公路車儀表板 — Plan 1:基礎(資料建置管線 + 專案骨架)實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建好 Astro+React+Tailwind+ECharts 專案骨架,並用 Python 把 master 資料集轉成瀏覽器要的精簡檔(viz.json / races.json / 單場檔),含共用的資料載入、篩選狀態與時間/percentile 工具,讓後續頁面可直接接資料開發。

**Architecture:** 建置時(Python `scrapers/build_viz.py`)讀 `data/processed/master_2024_2026.public.json` → 產出 `web/public/data/{viz.json, races.json, race/*.json}`。前端 Astro 靜態殼 + React island;載入精簡 viz.json 進記憶體,以輕量 store 做全域篩選,圖表元件後續 plan 再加。純函式(距離抽取、均速、percentile、時間格式)以測試先行。

**Tech Stack:** Astro 5 · React 19 islands · Tailwind 4 · echarts-for-react · nanostores · TypeScript · Python 3.13 (pytest) · Vitest · Vercel(靜態)

設計依據:`docs/superpowers/specs/2026-06-04-cycling-dashboard-design.md`

---

## 檔案結構(本 plan 建立)

```
scrapers/
  build_viz.py            master.public -> web/public/data/* (含純函式)
  test_build_viz.py       pytest 單元測試
web/
  package.json, astro.config.mjs, tsconfig.json, tailwind.config.ts
  vitest.config.ts
  src/
    pages/index.astro     首頁殼(驗證骨架可跑)
    layouts/Base.astro    全站版型(字體/tokens/header)
    styles/tokens.css     Claude 色彩/字體 CSS 變數
    lib/
      types.ts            SlimRecord / RaceIndex 型別
      data-load.ts        載入 viz.json / races.json
      format.ts           時間↔秒、percentile(純函式)
      format.test.ts      Vitest
      filter-store.ts     nanostores 全域篩選 + URL 同步
  public/data/            (build_viz.py 產出;gitignored)
requirements.txt          (+ pytest)
```

---

## Task 1:Python 建置工具——距離抽取(TDD)

**Files:**
- Create: `scrapers/build_viz.py`
- Test: `scrapers/test_build_viz.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 把 pytest 加入 requirements**

Modify `requirements.txt`,在結尾加一行:
```
pytest==8.3.4
```
然後安裝:
```
python -m pip install pytest==8.3.4
```

- [ ] **Step 2: 寫失敗測試** — `scrapers/test_build_viz.py`

```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_viz as bv


def test_extract_distance_km():
    assert bv.extract_distance_km("104公里挑戰組", None, None) == 104
    assert bv.extract_distance_km("29公里經典組", None, None) == 29
    assert bv.extract_distance_km(None, "145K_總排名", None) == 145
    assert bv.extract_distance_km("80KM", None, None) == 80
    assert bv.extract_distance_km("男子菁英組", None, "2026 太平山王 45K") == 45
    assert bv.extract_distance_km("男子菁英組", "總排名", "太平山王") is None
    assert bv.extract_distance_km(None, None, None) is None
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `cd scrapers && python -m pytest test_build_viz.py::test_extract_distance_km -v`
Expected: FAIL(`AttributeError: module 'build_viz' has no attribute 'extract_distance_km'`)

- [ ] **Step 4: 實作最小程式** — 建立 `scrapers/build_viz.py`

```python
# -*- coding: utf-8 -*-
"""Build browser-ready data files from the master public dataset.

Reads  data/processed/master_2024_2026.public.json
Writes web/public/data/{viz.json, races.json, race/<race_key>__<year>.json}
"""
import json
import os
import re

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master_2024_2026.public.json")
OUT = os.path.join(HERE, "..", "web", "public", "data")

_DIST_RE = re.compile(r"(\d{2,3})\s*(?:公里|[KkＫ]\s*[Mm]?|公?里)")


def extract_distance_km(category_raw, result_label, race_name):
    """Pull a race distance in km from any of the label fields. None if absent."""
    for field in (category_raw, result_label, race_name):
        if not field:
            continue
        m = _DIST_RE.search(str(field))
        if m:
            km = int(m.group(1))
            if 5 <= km <= 700:
                return km
    return None
```

- [ ] **Step 5: 跑測試確認通過**

Run: `cd scrapers && python -m pytest test_build_viz.py::test_extract_distance_km -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scrapers/build_viz.py scrapers/test_build_viz.py requirements.txt
git commit -m "feat(build): distance extraction for viz dataset"
```

---

## Task 2:均速計算(TDD)

**Files:**
- Modify: `scrapers/build_viz.py`, `scrapers/test_build_viz.py`

- [ ] **Step 1: 加失敗測試** — 在 `test_build_viz.py` 追加:

```python
def test_avg_speed_kmh():
    assert bv.avg_speed_kmh(100, 3600) == 100.0          # 100km in 1h
    assert round(bv.avg_speed_kmh(45, 7200), 1) == 22.5  # 45km in 2h
    assert bv.avg_speed_kmh(None, 3600) is None
    assert bv.avg_speed_kmh(100, None) is None
    assert bv.avg_speed_kmh(100, 0) is None              # guard /0
    assert bv.avg_speed_kmh(100, 60) is None             # implausibly fast -> drop
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd scrapers && python -m pytest test_build_viz.py::test_avg_speed_kmh -v`
Expected: FAIL(no attribute `avg_speed_kmh`)

- [ ] **Step 3: 實作** — 在 `build_viz.py` 追加:

```python
def avg_speed_kmh(distance_km, finish_seconds):
    """km/h from distance + elapsed seconds. None if missing or implausible (>80km/h)."""
    if not distance_km or not finish_seconds or finish_seconds <= 0:
        return None
    spd = distance_km / (finish_seconds / 3600)
    if spd > 80:
        return None
    return round(spd, 1)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd scrapers && python -m pytest test_build_viz.py::test_avg_speed_kmh -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scrapers/build_viz.py scrapers/test_build_viz.py
git commit -m "feat(build): avg speed from distance and time"
```

---

## Task 3:精簡紀錄 + 月份(TDD)

**Files:**
- Modify: `scrapers/build_viz.py`, `scrapers/test_build_viz.py`

- [ ] **Step 1: 加失敗測試**

```python
def test_month_of():
    assert bv.month_of("2025-09-07 06:40:00") == 9
    assert bv.month_of("2024-11-14") == 11
    assert bv.month_of(None) is None
    assert bv.month_of("bad") is None


def test_slim_record():
    rec = {
        "race_key": "taipingshan", "race_name_canonical": "太平山王 公路賽",
        "year": 2026, "date": "2026-05-09", "series": "臺灣自行車聯賽(TCL)",
        "race_class": "競賽", "category_raw": "M25", "gender": "M",
        "age_group": "25", "finish_seconds": 7231.4, "rank_overall": 1,
        "result_label": "總排名", "source_platform": "cyclist.org.tw", "region": None,
    }
    s = bv.slim_record(rec)
    assert s["rk"] == "taipingshan"
    assert s["y"] == 2026 and s["mon"] == 5
    assert s["g"] == "M" and s["ag"] == "25"
    assert s["t"] == 7231 and s["rank"] == 1          # seconds rounded to int
    assert s["plat"] == "cyclist.org.tw"
    assert "name_raw" not in s and "splits" not in s   # slim only
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd scrapers && python -m pytest test_build_viz.py -k "month_of or slim_record" -v`
Expected: FAIL

- [ ] **Step 3: 實作** — 在 `build_viz.py` 追加:

```python
def month_of(date_str):
    if not date_str:
        return None
    m = re.match(r"\d{4}-(\d{2})", str(date_str))
    return int(m.group(1)) if m else None


def slim_record(rec):
    """Project a master record to the compact browser shape (short keys)."""
    dist = extract_distance_km(rec.get("category_raw"), rec.get("result_label"),
                               rec.get("race_name_raw") or rec.get("race_name_canonical"))
    t = rec.get("finish_seconds")
    return {
        "rk": rec.get("race_key"),
        "rn": rec.get("race_name_canonical"),
        "y": rec.get("year"),
        "mon": month_of(rec.get("date")),
        "s": rec.get("series"),
        "rc": rec.get("race_class"),
        "cat": rec.get("category_raw"),
        "g": rec.get("gender"),
        "ag": rec.get("age_group"),
        "t": int(t) if t is not None else None,
        "rank": rec.get("rank_overall"),
        "dist": dist,
        "spd": avg_speed_kmh(dist, t),
        "plat": rec.get("source_platform"),
        "reg": rec.get("region"),
    }
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd scrapers && python -m pytest test_build_viz.py -k "month_of or slim_record" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scrapers/build_viz.py scrapers/test_build_viz.py
git commit -m "feat(build): slim record projection + month parsing"
```

---

## Task 4:組裝輸出檔 + 跑建置

**Files:**
- Modify: `scrapers/build_viz.py`

- [ ] **Step 1: 加 main 組裝邏輯** — 在 `build_viz.py` 追加:

```python
def build_races_index(records):
    """One entry per (race_key, year): name, series, count, multi-year flag, has_team."""
    from collections import defaultdict
    agg = defaultdict(lambda: {"rows": 0, "team": False})
    years = defaultdict(set)
    meta = {}
    for r in records:
        key = (r.get("race_key"), r.get("year"))
        a = agg[key]
        a["rows"] += 1
        a["team"] = a["team"] or bool(r.get("team"))
        years[r.get("race_key")].add(r.get("year"))
        meta[r.get("race_key")] = {"rn": r.get("race_name_canonical"), "s": r.get("series")}
    out = []
    for (rk, y), a in agg.items():
        out.append({"rk": rk, "y": y, "rn": meta[rk]["rn"], "s": meta[rk]["s"],
                    "rows": a["rows"], "multi_year": len([x for x in years[rk] if x]) > 1,
                    "has_team": a["team"]})
    return sorted(out, key=lambda x: (-(x["rows"]), str(x["rk"])))


def detail_record(rec):
    """Per-race leaderboard row (de-identified)."""
    return {"rank": rec.get("rank_overall"), "bib": rec.get("bib"),
            "name": rec.get("name_masked"), "cat": rec.get("category_raw"),
            "g": rec.get("gender"), "ag": rec.get("age_group"),
            "team": rec.get("team"), "t": rec.get("finish_seconds"),
            "label": rec.get("result_label")}


def main():
    records = json.load(open(IN, encoding="utf-8"))
    os.makedirs(os.path.join(OUT, "race"), exist_ok=True)
    # 1) slim viz dataset
    viz = [slim_record(r) for r in records]
    json.dump(viz, open(os.path.join(OUT, "viz.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    # 2) races index
    idx = build_races_index(records)
    json.dump(idx, open(os.path.join(OUT, "races.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    # 3) per-race detail files (key sanitized for filename)
    from collections import defaultdict
    groups = defaultdict(list)
    for r in records:
        safe = re.sub(r"[^0-9A-Za-z一-鿿]+", "-", str(r.get("race_key")))
        groups[f"{safe}__{r.get('year')}"].append(r)
    for fname, rows in groups.items():
        rows = sorted([detail_record(x) for x in rows],
                      key=lambda x: (x["rank"] is None, x["rank"] or 0))
        json.dump(rows, open(os.path.join(OUT, "race", f"{fname}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    print(f"viz={len(viz)} races={len(idx)} detailFiles={len(groups)} -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 跑建置(先確保 web/public/data 目錄會被建立)**

Run: `python scrapers/build_viz.py`
Expected: 印出類似 `viz=33051 races=47 detailFiles=~80 -> web\public\data`,且 `web/public/data/viz.json`、`races.json`、`race/*.json` 存在。

- [ ] **Step 3: 驗證 viz.json 大小合理(壓縮後應 <1.5MB)**

Run(檢查未壓縮大小,gzip 後會小很多):
```bash
python -c "import os;print(round(os.path.getsize('web/public/data/viz.json')/1e6,1),'MB')"
```
Expected: 約 3–6 MB 未壓縮(Vercel 會自動 gzip/br 至 <1.5MB)。若 >8MB,回頭精簡欄位。

- [ ] **Step 4: Commit**

```bash
git add scrapers/build_viz.py
git commit -m "feat(build): assemble viz.json, races.json, per-race detail files"
```

---

## Task 5:Astro + React + Tailwind 專案骨架

**Files:**
- Create: `web/`(整個 Astro 專案)

- [ ] **Step 1: 用官方範本建立專案**

Run(在專案根目錄):
```bash
cd C:/Users/user/Desktop/tw-cycling-data
npm create astro@latest web -- --template minimal --no-install --no-git --yes
```
Expected: 建立 `web/` 含 `package.json`、`astro.config.mjs`、`src/pages/index.astro`。

- [ ] **Step 2: 加入 React、Tailwind、ECharts、nanostores 整合**

Run:
```bash
cd web
npx astro add react tailwind --yes
npm install echarts echarts-for-react nanostores @nanostores/react
npm install -D vitest
```
Expected: `astro.config.mjs` 出現 react()、tailwind 整合;依賴寫入 `package.json`。

- [ ] **Step 3: 啟動 dev server 確認骨架可跑**

Run:
```bash
cd web && npm run dev
```
Expected: 印出 `http://localhost:4321`,瀏覽器開啟看到 Astro 預設頁(確認後 Ctrl+C 結束)。

- [ ] **Step 4: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/package.json web/package-lock.json web/astro.config.mjs web/tsconfig.json
git commit -m "chore(web): scaffold Astro + React + Tailwind + ECharts"
```

---

## Task 6:設計 tokens(Claude 暖色 + 字體)

**Files:**
- Create: `web/src/styles/tokens.css`, `web/src/layouts/Base.astro`
- Modify: `web/tailwind.config.ts`(或 `tailwind.config.mjs`,依 astro add 產出為準)

- [ ] **Step 1: 建立 CSS tokens** — `web/src/styles/tokens.css`

```css
/* Claude warm palette + fonts (self-hosted via Google Fonts links for now) */
@import url("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Hanken+Grotesk:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@600;700&family=Spline+Sans+Mono:wght@400;500&display=swap");

:root {
  --bg: #FAF9F5;
  --surface: #FFFFFF;
  --border: #E8E3D9;
  --text: #1F1E1D;
  --text-muted: #6B6760;
  --accent: #D97757;        /* Claude clay coral */
  --series-blue: #5B7B8A;
  --series-sage: #7C8C6B;
  --font-display: "Fraunces", "Noto Serif TC", serif;
  --font-body: "Hanken Grotesk", "Noto Sans TC", system-ui, sans-serif;
  --font-mono: "Spline Sans Mono", ui-monospace, monospace;
}

html { background: var(--bg); color: var(--text); font-family: var(--font-body); }
h1, h2, h3, .display { font-family: var(--font-display); }
.num { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
```

- [ ] **Step 2: 把 Claude tokens 接進 Tailwind** — 在 `web/tailwind.config.*` 的 `theme.extend` 加:

```js
colors: {
  bg: "#FAF9F5", surface: "#FFFFFF", border: "#E8E3D9",
  ink: "#1F1E1D", muted: "#6B6760", accent: "#D97757",
  "series-blue": "#5B7B8A", "series-sage": "#7C8C6B",
},
fontFamily: {
  display: ["Fraunces", "Noto Serif TC", "serif"],
  body: ["Hanken Grotesk", "Noto Sans TC", "system-ui", "sans-serif"],
  mono: ["Spline Sans Mono", "ui-monospace", "monospace"],
},
```

- [ ] **Step 3: 建立全站版型** — `web/src/layouts/Base.astro`

```astro
---
import "../styles/tokens.css";
const { title = "台灣公路車賽事成績儀表板" } = Astro.props;
---
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
  </head>
  <body class="bg-bg text-ink font-body">
    <header class="border-b border-border px-6 py-4">
      <a href="/" class="font-display text-xl text-ink">台灣公路車賽事成績儀表板</a>
      <nav class="mt-1 flex gap-4 text-sm text-muted">
        <a href="/">總覽</a><a href="/explore">探索</a>
        <a href="/race">賽事</a><a href="/climbs">傳奇爬坡</a>
      </nav>
    </header>
    <main class="mx-auto max-w-6xl px-6 py-8"><slot /></main>
  </body>
</html>
```

- [ ] **Step 4: 首頁用版型 + 顯示 KPI 占位** — 覆寫 `web/src/pages/index.astro`

```astro
---
import Base from "../layouts/Base.astro";
---
<Base>
  <h1 class="font-display text-3xl">總覽</h1>
  <p class="mt-2 text-muted">公路車賽事成績資料探索 · 2024–2026</p>
  <div class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
    <div class="rounded-xl border border-border bg-surface p-4">
      <div class="text-sm text-muted">成績筆數</div>
      <div class="num text-3xl text-ink">33,051</div>
    </div>
    <div class="rounded-xl border border-border bg-surface p-4">
      <div class="text-sm text-muted">賽事</div><div class="num text-3xl">47</div>
    </div>
    <div class="rounded-xl border border-border bg-surface p-4">
      <div class="text-sm text-muted">系列</div><div class="num text-3xl">20</div>
    </div>
    <div class="rounded-xl border border-border bg-surface p-4">
      <div class="text-sm text-muted">年份</div><div class="num text-3xl">2024–26</div>
    </div>
  </div>
</Base>
```

- [ ] **Step 5: 啟動確認暖色 + 字體 + KPI 卡正常**

Run: `cd web && npm run dev`
Expected: 首頁暖白底、Fraunces 標題、橘色可用、4 張 KPI 卡顯示(視覺確認後 Ctrl+C)。

- [ ] **Step 6: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src web/tailwind.config.*
git commit -m "feat(web): Claude warm design tokens, base layout, overview shell"
```

---

## Task 7:TS 型別 + 資料載入

**Files:**
- Create: `web/src/lib/types.ts`, `web/src/lib/data-load.ts`

- [ ] **Step 1: 型別** — `web/src/lib/types.ts`

```ts
export interface SlimRecord {
  rk: string; rn: string; y: number | null; mon: number | null;
  s: string | null; rc: string; cat: string | null;
  g: "M" | "F" | null; ag: string | null;
  t: number | null; rank: number | null;
  dist: number | null; spd: number | null;
  plat: string; reg: string | null;
}
export interface RaceIndex {
  rk: string; y: number | null; rn: string; s: string | null;
  rows: number; multi_year: boolean; has_team: boolean;
}
export interface DetailRow {
  rank: number | null; bib: string | null; name: string | null;
  cat: string | null; g: "M" | "F" | null; ag: string | null;
  team: string | null; t: number | null; label: string | null;
}
```

- [ ] **Step 2: 載入器** — `web/src/lib/data-load.ts`

```ts
import type { SlimRecord, RaceIndex, DetailRow } from "./types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

export async function loadViz(): Promise<SlimRecord[]> {
  const r = await fetch(`${base}/data/viz.json`);
  if (!r.ok) throw new Error(`viz.json ${r.status}`);
  return r.json();
}
export async function loadRaces(): Promise<RaceIndex[]> {
  const r = await fetch(`${base}/data/races.json`);
  if (!r.ok) throw new Error(`races.json ${r.status}`);
  return r.json();
}
export async function loadRaceDetail(file: string): Promise<DetailRow[]> {
  const r = await fetch(`${base}/data/race/${file}.json`);
  if (!r.ok) throw new Error(`race ${file} ${r.status}`);
  return r.json();
}
```

- [ ] **Step 3: Commit**

```bash
git add web/src/lib/types.ts web/src/lib/data-load.ts
git commit -m "feat(web): data types and loaders"
```

---

## Task 8:時間 / percentile 純函式(Vitest TDD)

**Files:**
- Create: `web/src/lib/format.ts`, `web/src/lib/format.test.ts`, `web/vitest.config.ts`
- Modify: `web/package.json`(test script)

- [ ] **Step 1: vitest 設定** — `web/vitest.config.ts`

```ts
import { defineConfig } from "vitest/config";
export default defineConfig({ test: { environment: "node" } });
```
並在 `web/package.json` 的 `"scripts"` 加:`"test": "vitest run"`。

- [ ] **Step 2: 寫失敗測試** — `web/src/lib/format.test.ts`

```ts
import { describe, it, expect } from "vitest";
import { secondsToHMS, hmsToSeconds, percentileBeaten } from "./format";

describe("time format", () => {
  it("secondsToHMS", () => {
    expect(secondsToHMS(7231)).toBe("2:00:31");
    expect(secondsToHMS(59)).toBe("0:00:59");
    expect(secondsToHMS(null)).toBe("—");
  });
  it("hmsToSeconds", () => {
    expect(hmsToSeconds("2:00:31")).toBe(7231);
    expect(hmsToSeconds("00:14:38")).toBe(878);
    expect(hmsToSeconds("bad")).toBeNull();
  });
});

describe("percentileBeaten", () => {
  const times = [100, 200, 300, 400, 500]; // sorted ascending (faster first)
  it("faster than all -> ~100% beaten", () => {
    expect(percentileBeaten(90, times)).toBe(100);
  });
  it("slower than all -> 0%", () => {
    expect(percentileBeaten(600, times)).toBe(0);
  });
  it("median -> ~40-60%", () => {
    const p = percentileBeaten(300, times);
    expect(p).toBeGreaterThanOrEqual(40);
    expect(p).toBeLessThanOrEqual(60);
  });
});
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `cd web && npm test`
Expected: FAIL(找不到 `./format` 的匯出)

- [ ] **Step 4: 實作** — `web/src/lib/format.ts`

```ts
export function secondsToHMS(s: number | null): string {
  if (s == null) return "—";
  const sec = Math.round(s);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const ss = sec % 60;
  return `${h}:${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}

export function hmsToSeconds(t: string): number | null {
  const m = /^(\d{1,2}):(\d{2}):(\d{2})/.exec(t.trim());
  if (!m) return null;
  return +m[1] * 3600 + +m[2] * 60 + +m[3];
}

/** % of finishers you beat (slower than you). `sortedTimes` ascending. */
export function percentileBeaten(mySeconds: number, sortedTimes: number[]): number {
  if (!sortedTimes.length) return 0;
  let slower = 0;
  for (const t of sortedTimes) if (t > mySeconds) slower++;
  return Math.round((slower / sortedTimes.length) * 100);
}
```

- [ ] **Step 5: 跑測試確認通過**

Run: `cd web && npm test`
Expected: PASS(全綠)

- [ ] **Step 6: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/lib/format.ts web/src/lib/format.test.ts web/vitest.config.ts web/package.json
git commit -m "feat(web): time + percentile utilities (tested)"
```

---

## Task 9:全域篩選 store + URL 同步

**Files:**
- Create: `web/src/lib/filter-store.ts`

- [ ] **Step 1: 實作 store** — `web/src/lib/filter-store.ts`

```ts
import { map } from "nanostores";
import type { SlimRecord } from "./types";

export interface Filters {
  year: number | null; series: string | null; race: string | null;
  raceClass: string | null; gender: "M" | "F" | null; ageGroup: string | null;
}
export const EMPTY: Filters = {
  year: null, series: null, race: null, raceClass: null, gender: null, ageGroup: null,
};
export const $filters = map<Filters>({ ...EMPTY });

export function setFilter<K extends keyof Filters>(k: K, v: Filters[K]) {
  $filters.setKey(k, v);
  syncToUrl();
}

export function applyFilters(rows: SlimRecord[], f: Filters): SlimRecord[] {
  return rows.filter((r) =>
    (f.year == null || r.y === f.year) &&
    (f.series == null || r.s === f.series) &&
    (f.race == null || r.rk === f.race) &&
    (f.raceClass == null || r.rc === f.raceClass) &&
    (f.gender == null || r.g === f.gender) &&
    (f.ageGroup == null || r.ag === f.ageGroup)
  );
}

function syncToUrl() {
  if (typeof window === "undefined") return;
  const f = $filters.get();
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(f)) if (v != null) p.set(k, String(v));
  const qs = p.toString();
  history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
}

export function hydrateFromUrl() {
  if (typeof window === "undefined") return;
  const p = new URLSearchParams(location.search);
  const next: Filters = { ...EMPTY };
  if (p.get("year")) next.year = Number(p.get("year"));
  next.series = p.get("series");
  next.race = p.get("race");
  next.raceClass = p.get("raceClass");
  const g = p.get("gender");
  next.gender = g === "M" || g === "F" ? g : null;
  next.ageGroup = p.get("ageGroup");
  $filters.set(next);
}
```

- [ ] **Step 2: 型別檢查通過**

Run: `cd web && npx astro check`
Expected: 0 errors(允許 hints/warnings)。

- [ ] **Step 3: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/lib/filter-store.ts
git commit -m "feat(web): global filter store with URL sync"
```

---

## Task 10:資料端到端煙霧測試(Astro 載入 viz.json)

**Files:**
- Create: `web/src/components/DataSmoke.tsx`
- Modify: `web/src/pages/index.astro`

- [ ] **Step 1: 建立 React island** — `web/src/components/DataSmoke.tsx`

```tsx
import { useEffect, useState } from "react";
import { loadViz } from "../lib/data-load";

export default function DataSmoke() {
  const [n, setN] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    loadViz().then((rows) => setN(rows.length)).catch((e) => setErr(String(e)));
  }, []);
  if (err) return <span className="text-accent">載入失敗:{err}</span>;
  return <span className="num">{n == null ? "載入中…" : `${n.toLocaleString()} 筆`}</span>;
}
```

- [ ] **Step 2: 在首頁掛載(client island)** — 在 `index.astro` 的 frontmatter import,並在「成績筆數」卡片把硬編 33,051 換成元件:

```astro
---
import Base from "../layouts/Base.astro";
import DataSmoke from "../components/DataSmoke.tsx";
---
```
把成績筆數卡片內的 `<div class="num text-3xl text-ink">33,051</div>` 改為:
```astro
<div class="num text-3xl text-ink"><DataSmoke client:load /></div>
```

- [ ] **Step 3: 跑 dev 確認真的從 viz.json 載到筆數**

Run: `cd web && npm run dev`
Expected: 首頁「成績筆數」卡顯示 `33,051 筆`(從 `public/data/viz.json` 實際載入;先確認 Task 4 已產出檔案)。

- [ ] **Step 4: build 驗證可靜態產出**

Run: `cd web && npm run build`
Expected: `npm run build` 成功,產出 `web/dist/`。

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/DataSmoke.tsx web/src/pages/index.astro
git commit -m "feat(web): end-to-end data smoke test island"
```

---

## 完成標準(Plan 1)

- `python -m pytest scrapers/test_build_viz.py` 全綠;`python scrapers/build_viz.py` 產出 viz/races/race 檔。
- `cd web && npm test` 全綠;`npm run build` 成功。
- 首頁以 Claude 暖色 + 指定字體呈現,KPI「成績筆數」由 viz.json 實際載入顯示。
- 全域篩選 store、資料載入器、時間/percentile 工具就緒,供 Plan 2(探索頁)直接使用。

---

## Self-Review(對照 spec)

- **資料層(spec §5)**:viz.json/races.json/race 檔 + 短鍵 schema、距離抽取、均速、月份 → Task 1–4 ✓;`uci_id` 預留 = 目前 master 無此欄,slim_record 不含,未來來源接上後加(spec §11 已註)。
- **技術棧(spec §6)**:Astro+React+Tailwind+ECharts+nanostores → Task 5、9 ✓(ECharts 安裝於 Task 5,實際圖表在 Plan 2)。
- **視覺系統(spec §7)**:tokens + 字體 + 版型 → Task 6 ✓。
- **隱私(spec §8/§10)**:只讀 `*.public.json`、detail 用 `name_masked` → Task 4 `detail_record` ✓。
- **圖表(spec §3 的 12 圖)**:不在本 plan(Plan 2–5);本 plan 只建地基 → 範圍正確。
- Placeholder 掃描:無 TBD;每個 code step 均含完整程式。
- 型別一致性:`SlimRecord` 短鍵(rk/y/mon/g/ag/t…)在 build_viz `slim_record`、types.ts、filter-store `applyFilters` 三處一致 ✓;`secondsToHMS/hmsToSeconds/percentileBeaten` 簽章在測試與實作一致 ✓。
