# 公路車儀表板 — Plan 4:賽事詳情頁實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 做出賽事詳情頁 `/race`:選一場賽事 → 排行榜表(姓名遮罩、分頁、組別篩選)+「你贏過多少%」percentile 查詢 + 該場完賽時間分布 + 領獎台 + (多年賽)跨年「變快了嗎」+ (競技賽)車隊戰力榜。

**Architecture:** `race.astro` 掛 `client:only="react"` 的 `RaceDetailApp`。App 載入 `races.json`(賽事清單,新增 `file` 欄位)+ `viz.json`(供跨年統計);選賽事後依其 `file` lazy load `/data/race/<file>.json`(單場排行榜,含遮罩姓名/車隊)。詳情聚合為純函式(`racedetail.ts`,TDD);percentile 用既有 `format.percentileBeaten`。`build_viz.py` 抽出 `race_file_name()` 讓「寫檔」與「索引 file 欄位」共用同一命名,前端不必重算。

**Tech Stack:** Astro 6 · React 19 islands(client:only)· ECharts 6 · Python(pytest)· Vitest。沿用既有 lib/components。

設計依據:`docs/superpowers/specs/2026-06-04-cycling-dashboard-design.md` 頁 C。

---

## 檔案結構(本 plan 建立/修改)

```
scrapers/build_viz.py        + race_file_name(); build_races_index 加 file 欄位(改)
scrapers/test_build_viz.py   + test_race_file_name;更新 races-index 測試(改)
web/src/lib/
  types.ts                   RaceIndex 加 file: string(改)
  racedetail.ts              categoriesOf / podium / teamStrength / crossYear(純函式)
  racedetail.test.ts         Vitest
web/src/components/race/
  RacePicker.tsx             賽事選擇(系列分組,選擇 → URL ?rk=&y=)
  Leaderboard.tsx            排行榜表(分頁 + 組別篩選)
  PercentileWidget.tsx       「你贏過多少%」
  Podium.tsx                 領獎台 top3
  RaceTimeHistogram.tsx      該場完賽時間分布
  CrossYearTrend.tsx         跨年 冠軍/中位 折線(多年賽才顯示)
  TeamStrength.tsx           車隊戰力榜(競技賽才顯示)
  RaceDetailApp.tsx          orchestrator
web/src/pages/race.astro     /race 頁
```

---

## Task 1:build_viz 加 file 欄位(TDD)+ RaceIndex 型別

**Files:**
- Modify: `scrapers/build_viz.py`, `scrapers/test_build_viz.py`, `web/src/lib/types.ts`

- [ ] **Step 1: 加失敗測試** — 在 `scrapers/test_build_viz.py` 追加,並更新既有 races-index 測試:

```python
def test_race_file_name():
    assert bv.race_file_name("taipingshan", 2026) == "taipingshan__2026"
    assert bv.race_file_name("【96】台北", 2025) == "96-台北__2025"   # punctuation -> single dash, trimmed
    assert bv.race_file_name("a/b c", 2024) == "a-b-c__2024"
```

並在既有 `test_build_races_index` 末尾(回傳 out 後)補一行斷言每筆都有正確 file:
```python
    assert all("file" in e for e in out)
    assert out[0]["file"] == bv.race_file_name(out[0]["rk"], out[0]["y"])
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd scrapers && python -m pytest test_build_viz.py -k "race_file_name or build_races_index" -v`
Expected: FAIL(無 `race_file_name`;races-index 缺 file)

- [ ] **Step 3: 實作** — 在 `scrapers/build_viz.py`:

(a) 在檔案上方(`detail_record` 附近)新增:
```python
def race_file_name(rk, year):
    """Stable per-race-year filename stem; shared by main() and the races index
    so the frontend never recomputes the sanitization."""
    safe = re.sub(r"[^0-9A-Za-z一-鿿]+", "-", str(rk)).strip("-")
    return f"{safe}__{year}"
```

(b) 在 `build_races_index` 內,建立每筆 out 時加入 `file`:
把
```python
        out.append({"rk": rk, "y": y, "rn": meta[rk]["rn"], "s": meta[rk]["s"],
                    "rows": a["rows"], "multi_year": len([x for x in years[rk] if x]) > 1,
                    "has_team": a["team"]})
```
改成
```python
        out.append({"rk": rk, "y": y, "rn": meta[rk]["rn"], "s": meta[rk]["s"],
                    "rows": a["rows"], "multi_year": len([x for x in years[rk] if x]) > 1,
                    "has_team": a["team"], "file": race_file_name(rk, y)})
```

(c) 在 `main()` 的 per-race 寫檔處改用同一函式:
把
```python
        safe = re.sub(r"[^0-9A-Za-z一-鿿]+", "-", str(r.get("race_key"))).strip("-")
        groups[f"{safe}__{r.get('year')}"].append(r)
```
改成
```python
        groups[race_file_name(r.get("race_key"), r.get("year"))].append(r)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd scrapers && python -m pytest test_build_viz.py -v`
Expected: PASS(全部)

- [ ] **Step 5: 重新產生資料(races.json 帶 file)**

Run: `python scrapers/build_viz.py`
Expected: 印出 viz=33051 races=57 detailFiles=57;`web/public/data/races.json` 每筆有 `file`。

- [ ] **Step 6: 更新 RaceIndex 型別** — `web/src/lib/types.ts`,在 `RaceIndex` 介面加 `file: string;`:
```ts
export interface RaceIndex {
  rk: string; y: number | null; rn: string; s: string | null;
  rows: number; multi_year: boolean; has_team: boolean; file: string;
}
```

- [ ] **Step 7: 型別 + 測試 + Commit**

Run: `cd web && npx astro check` (0 errors) `&&` `npm test` (仍綠).
```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add scrapers/build_viz.py scrapers/test_build_viz.py web/src/lib/types.ts
git commit -m "feat(build): race_file_name + file field in races index; RaceIndex.file"
```

---

## Task 2:賽事詳情聚合純函式(TDD)

**Files:**
- Create: `web/src/lib/racedetail.ts`, `web/src/lib/racedetail.test.ts`

- [ ] **Step 1: 寫失敗測試** — `web/src/lib/racedetail.test.ts`

```ts
import { describe, it, expect } from "vitest";
import { categoriesOf, podium, teamStrength, crossYear } from "./racedetail";
import type { DetailRow } from "./types";

function d(p: Partial<DetailRow>): DetailRow {
  return { rank: 1, bib: "1", name: "甲", cat: "菁英", g: "M", ag: null, team: "A隊", t: 1000, label: null, ...p };
}

describe("categoriesOf", () => {
  it("distinct sorted non-null categories", () => {
    expect(categoriesOf([d({ cat: "B" }), d({ cat: "A" }), d({ cat: "A" }), d({ cat: null })]))
      .toEqual(["A", "B"]);
  });
});

describe("podium", () => {
  it("top 3 by rank", () => {
    const p = podium([d({ rank: 3, name: "丙" }), d({ rank: 1, name: "甲" }), d({ rank: 2, name: "乙" }), d({ rank: 4, name: "丁" })]);
    expect(p.map((x) => x.name)).toEqual(["甲", "乙", "丙"]);
  });
});

describe("teamStrength", () => {
  it("counts top-cutoff and podium per team, sorted", () => {
    const rows = [
      d({ team: "A隊", rank: 1 }), d({ team: "A隊", rank: 2 }), d({ team: "A隊", rank: 12 }),
      d({ team: "B隊", rank: 5 }), d({ team: null, rank: 1 }),
    ];
    const ts = teamStrength(rows, 10, 10);
    expect(ts[0].team).toBe("A隊");
    expect(ts[0].top).toBe(2);     // ranks 1,2 within cutoff 10 (12 excluded)
    expect(ts[0].podium).toBe(2);  // ranks 1,2 within top3
    expect(ts.find((t) => t.team === "B隊")?.top).toBe(1);
  });
});

describe("crossYear", () => {
  it("winner(min)/median/n per year, sorted by year", () => {
    const rows = [
      { y: 2025, t: 100 }, { y: 2025, t: 200 }, { y: 2025, t: 300 },
      { y: 2024, t: 400 }, { y: 2024, t: 600 },
    ];
    const cy = crossYear(rows);
    expect(cy.map((x) => x.y)).toEqual([2024, 2025]);
    expect(cy[0]).toEqual({ y: 2024, winner: 400, median: 500, n: 2 });
    expect(cy[1].winner).toBe(100);
    expect(cy[1].median).toBe(200);
  });
});
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd web && npm test`
Expected: FAIL(無 `./racedetail`)

- [ ] **Step 3: 實作** — `web/src/lib/racedetail.ts`

```ts
import { quantile } from "./aggregate";
import type { DetailRow } from "./types";

export function categoriesOf(rows: DetailRow[]): string[] {
  return [...new Set(rows.map((r) => r.cat).filter((c): c is string => !!c))].sort();
}

export interface PodiumEntry { rank: number; name: string | null; team: string | null; t: number | null; }
export function podium(rows: DetailRow[], n = 3): PodiumEntry[] {
  return rows
    .filter((r) => r.rank != null)
    .sort((a, b) => (a.rank as number) - (b.rank as number))
    .slice(0, n)
    .map((r) => ({ rank: r.rank as number, name: r.name, team: r.team, t: r.t }));
}

export interface TeamStat { team: string; top: number; podium: number; }
export function teamStrength(rows: DetailRow[], topN = 10, cutoff = 10): TeamStat[] {
  const g = new Map<string, { top: number; pod: number }>();
  for (const r of rows) {
    if (!r.team || r.rank == null) continue;
    const e = g.get(r.team) || { top: 0, pod: 0 };
    if (r.rank <= cutoff) e.top++;
    if (r.rank <= 3) e.pod++;
    g.set(r.team, e);
  }
  return [...g.entries()]
    .map(([team, e]) => ({ team, top: e.top, podium: e.pod }))
    .filter((t) => t.top > 0)
    .sort((a, b) => b.top - a.top || b.podium - a.podium)
    .slice(0, topN);
}

export interface YearStat { y: number; winner: number; median: number; n: number; }
export function crossYear(rows: { y: number | null; t: number | null }[]): YearStat[] {
  const g = new Map<number, number[]>();
  for (const r of rows) {
    if (r.y == null || r.t == null) continue;
    const a = g.get(r.y) || [];
    a.push(r.t);
    g.set(r.y, a);
  }
  return [...g.entries()]
    .map(([y, ts]) => {
      ts.sort((a, b) => a - b);
      return { y, winner: ts[0], median: quantile(ts, 0.5), n: ts.length };
    })
    .sort((a, b) => a.y - b.y);
}
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd web && npm test`
Expected: PASS(全綠)

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/lib/racedetail.ts web/src/lib/racedetail.test.ts
git commit -m "feat(web): race-detail aggregations (tested)"
```

---

## Task 3:RacePicker + Leaderboard

**Files:**
- Create: `web/src/components/race/RacePicker.tsx`, `web/src/components/race/Leaderboard.tsx`

- [ ] **Step 1: RacePicker** — `web/src/components/race/RacePicker.tsx`

```tsx
import type { RaceIndex } from "../../lib/types";

interface Props { races: RaceIndex[]; onPick: (r: RaceIndex) => void; }

export default function RacePicker({ races, onPick }: Props) {
  // group by series for a tidy list
  const bySeries = new Map<string, RaceIndex[]>();
  for (const r of [...races].sort((a, b) => (b.y ?? 0) - (a.y ?? 0) || b.rows - a.rows)) {
    const s = r.s || "其他";
    const arr = bySeries.get(s) || [];
    arr.push(r);
    bySeries.set(s, arr);
  }
  return (
    <div className="space-y-5">
      <p className="text-muted">選一場賽事查看排行榜與分析:</p>
      {[...bySeries.entries()].map(([s, list]) => (
        <div key={s}>
          <h3 className="font-display text-sm text-muted">{s}</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {list.map((r) => (
              <button key={r.file} onClick={() => onPick(r)}
                className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink hover:border-accent hover:text-accent">
                {r.y} {r.rn} <span className="num text-muted">({r.rows})</span>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Leaderboard** — `web/src/components/race/Leaderboard.tsx`

```tsx
import { useMemo, useState } from "react";
import { categoriesOf } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const PAGE = 50;

export default function Leaderboard({ rows }: { rows: DetailRow[] }) {
  const cats = useMemo(() => categoriesOf(rows), [rows]);
  const [cat, setCat] = useState<string>("");
  const [page, setPage] = useState(0);

  const filtered = useMemo(
    () => (cat ? rows.filter((r) => r.cat === cat) : rows),
    [rows, cat],
  );
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE));
  const p = Math.min(page, pages - 1);
  const slice = filtered.slice(p * PAGE, p * PAGE + PAGE);

  return (
    <div>
      <div className="mb-3 flex items-center gap-3 text-sm">
        <select className="rounded-lg border border-border bg-surface px-3 py-2 text-ink"
          value={cat} onChange={(e) => { setCat(e.target.value); setPage(0); }}>
          <option value="">全部組別</option>
          {cats.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <span className="text-muted">{filtered.length.toLocaleString()} 筆</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted">
              <th className="py-2 pr-3">名次</th><th className="pr-3">號碼</th><th className="pr-3">姓名</th>
              <th className="pr-3">組別</th><th className="pr-3">車隊</th><th className="pr-3">完賽</th>
            </tr>
          </thead>
          <tbody>
            {slice.map((r, i) => (
              <tr key={`${r.bib}-${i}`} className="border-b border-border/60">
                <td className="num py-1.5 pr-3">{r.rank ?? "—"}</td>
                <td className="num pr-3 text-muted">{r.bib ?? ""}</td>
                <td className="pr-3 text-ink">{r.name ?? "—"}</td>
                <td className="pr-3 text-muted">{r.cat ?? ""}</td>
                <td className="pr-3 text-muted">{r.team ?? ""}</td>
                <td className="num pr-3">{secondsToHMS(r.t)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="mt-3 flex items-center gap-3 text-sm">
          <button className="rounded border border-border px-2 py-1 text-muted disabled:opacity-40"
            disabled={p <= 0} onClick={() => setPage(p - 1)}>上一頁</button>
          <span className="num text-muted">{p + 1} / {pages}</span>
          <button className="rounded border border-border px-2 py-1 text-muted disabled:opacity-40"
            disabled={p >= pages - 1} onClick={() => setPage(p + 1)}>下一頁</button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: 型別檢查 + Commit**

Run: `cd web && npx astro check` (0 errors).
```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/race/RacePicker.tsx web/src/components/race/Leaderboard.tsx
git commit -m "feat(web): race picker + paginated leaderboard"
```

---

## Task 4:PercentileWidget + Podium + RaceTimeHistogram

**Files:**
- Create: `web/src/components/race/PercentileWidget.tsx`, `web/src/components/race/Podium.tsx`, `web/src/components/race/RaceTimeHistogram.tsx`

- [ ] **Step 1: PercentileWidget** — `web/src/components/race/PercentileWidget.tsx`

```tsx
import { useMemo, useState } from "react";
import { categoriesOf } from "../../lib/racedetail";
import { hmsToSeconds, percentileBeaten, secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

export default function PercentileWidget({ rows }: { rows: DetailRow[] }) {
  const cats = useMemo(() => categoriesOf(rows), [rows]);
  const [cat, setCat] = useState<string>("");
  const [input, setInput] = useState<string>("");

  const times = useMemo(
    () => (cat ? rows.filter((r) => r.cat === cat) : rows)
      .map((r) => r.t).filter((t): t is number => t != null).sort((a, b) => a - b),
    [rows, cat],
  );
  const mine = hmsToSeconds(input);
  const pct = mine != null && times.length ? percentileBeaten(mine, times) : null;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-3 text-sm">
        <label className="flex flex-col gap-1">
          <span className="text-muted">組別</span>
          <select className="rounded-lg border border-border bg-surface px-3 py-2 text-ink"
            value={cat} onChange={(e) => setCat(e.target.value)}>
            <option value="">全部</option>
            {cats.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-muted">你的完賽時間 (時:分:秒)</span>
          <input className="rounded-lg border border-border bg-surface px-3 py-2 text-ink num"
            placeholder="2:30:00" value={input} onChange={(e) => setInput(e.target.value)} />
        </label>
      </div>
      {input && mine == null && <p className="text-sm text-accent">請輸入 時:分:秒(例 2:30:00)</p>}
      {pct != null && (
        <p className="text-lg text-ink">
          你贏過 <span className="num text-2xl text-accent">{pct}%</span> 的完賽者
          <span className="text-sm text-muted">(中位 {secondsToHMS(times[Math.floor(times.length / 2)])} · {times.length} 人)</span>
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Podium** — `web/src/components/race/Podium.tsx`

```tsx
import { podium } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const MEDAL = ["#D9A441", "#9FA6AD", "#B07A52"]; // gold / silver / bronze (warm)

export default function Podium({ rows }: { rows: DetailRow[] }) {
  const top = podium(rows, 3);
  if (!top.length) return <p className="text-muted">無名次資料</p>;
  return (
    <div className="flex flex-wrap gap-3">
      {top.map((p, i) => (
        <div key={i} className="min-w-[140px] flex-1 rounded-xl border border-border bg-surface p-3">
          <div className="num text-lg" style={{ color: MEDAL[i] }}>#{p.rank}</div>
          <div className="text-ink">{p.name ?? "—"}</div>
          <div className="text-xs text-muted">{p.team ?? ""}</div>
          <div className="num text-sm text-muted">{secondsToHMS(p.t)}</div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: RaceTimeHistogram** — `web/src/components/race/RaceTimeHistogram.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { histogram } from "../../lib/aggregate";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

export default function RaceTimeHistogram({ rows }: { rows: DetailRow[] }) {
  const values = rows.map((r) => r.t).filter((t): t is number => t != null);
  const bins = histogram(values, 300); // 5-min buckets for a single race
  if (!bins.length) return <div className="flex h-[280px] items-center justify-center text-muted">無時間資料</div>;
  const option: EChartsOption = {
    grid: { left: 48, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => { const b = bins[p[0].dataIndex]; return `${secondsToHMS(b.x0)}–${secondsToHMS(b.x1)}<br/>${p[0].value} 人`; },
    },
    xAxis: { type: "category", data: bins.map((b) => secondsToHMS(b.x0)),
      axisLabel: { interval: Math.max(0, Math.floor(bins.length / 8)) } },
    yAxis: { type: "value", name: "人數" },
    series: [{ type: "bar", data: bins.map((b) => b.count), itemStyle: { color: "#D97757" }, barWidth: "90%" }],
  };
  return <EChart option={option} height={280} />;
}
```

- [ ] **Step 4: 型別檢查 + Commit**

Run: `cd web && npx astro check` (0 errors).
```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/race/PercentileWidget.tsx web/src/components/race/Podium.tsx web/src/components/race/RaceTimeHistogram.tsx
git commit -m "feat(web): percentile widget, podium, race time histogram"
```

---

## Task 5:CrossYearTrend + TeamStrength

**Files:**
- Create: `web/src/components/race/CrossYearTrend.tsx`, `web/src/components/race/TeamStrength.tsx`

- [ ] **Step 1: CrossYearTrend** — `web/src/components/race/CrossYearTrend.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { crossYear } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";

export default function CrossYearTrend({ rows }: { rows: { y: number | null; t: number | null }[] }) {
  const cy = crossYear(rows);
  if (cy.length < 2) return <div className="flex h-[260px] items-center justify-center text-muted">僅單一年度,無跨年比較</div>;
  const option: EChartsOption = {
    grid: { left: 64, right: 16, top: 24, bottom: 40 },
    tooltip: { trigger: "axis", formatter: (p: any) =>
      p.map((s: any) => `${s.seriesName} ${secondsToHMS(s.value)}`).join("<br/>") },
    legend: { bottom: 0, textStyle: { color: "#6B6760" } },
    xAxis: { type: "category", data: cy.map((c) => String(c.y)) },
    yAxis: { type: "value", name: "完賽時間", axisLabel: { formatter: (v: number) => secondsToHMS(v) } },
    series: [
      { name: "冠軍", type: "line", data: cy.map((c) => c.winner), itemStyle: { color: "#D97757" }, smooth: true },
      { name: "中位", type: "line", data: cy.map((c) => c.median), itemStyle: { color: "#5B7B8A" }, smooth: true },
    ],
  };
  return <EChart option={option} height={260} />;
}
```

- [ ] **Step 2: TeamStrength** — `web/src/components/race/TeamStrength.tsx`

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { teamStrength } from "../../lib/racedetail";
import type { DetailRow } from "../../lib/types";

export default function TeamStrength({ rows }: { rows: DetailRow[] }) {
  const teams = teamStrength(rows, 12, 10);
  if (!teams.length) return <div className="flex h-[300px] items-center justify-center text-muted">無車隊資料</div>;
  const option: EChartsOption = {
    grid: { left: 160, right: 24, top: 16, bottom: 32 },
    tooltip: { trigger: "item", formatter: (p: any) => {
      const t = teams[p.dataIndex]; return `${t.team}<br/>前 10 名 ${t.top} 次<br/>領獎台 ${t.podium} 次`; } },
    xAxis: { type: "value", name: "前 10 名人次" },
    yAxis: { type: "category", inverse: true, data: teams.map((t) => t.team),
      axisLabel: { width: 150, overflow: "truncate" } },
    series: [{ type: "bar", data: teams.map((t) => t.top), itemStyle: { color: "#7C8C6B" }, barWidth: "70%" }],
  };
  return <EChart option={option} height={300} />;
}
```

- [ ] **Step 3: 型別檢查 + Commit**

Run: `cd web && npx astro check` (0 errors).
```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/race/CrossYearTrend.tsx web/src/components/race/TeamStrength.tsx
git commit -m "feat(web): cross-year trend + team strength charts"
```

---

## Task 6:RaceDetailApp + /race 頁 + 端到端驗證

**Files:**
- Create: `web/src/components/race/RaceDetailApp.tsx`, `web/src/pages/race.astro`

- [ ] **Step 1: RaceDetailApp** — `web/src/components/race/RaceDetailApp.tsx`

```tsx
import { useEffect, useMemo, useState } from "react";
import "../../lib/echarts-theme";
import { loadRaces, loadViz, loadRaceDetail } from "../../lib/data-load";
import { secondsToHMS } from "../../lib/format";
import type { RaceIndex, DetailRow, SlimRecord } from "../../lib/types";
import RacePicker from "./RacePicker";
import Leaderboard from "./Leaderboard";
import PercentileWidget from "./PercentileWidget";
import Podium from "./Podium";
import RaceTimeHistogram from "./RaceTimeHistogram";
import CrossYearTrend from "./CrossYearTrend";
import TeamStrength from "./TeamStrength";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

export default function RaceDetailApp() {
  const [races, setRaces] = useState<RaceIndex[]>([]);
  const [viz, setViz] = useState<SlimRecord[]>([]);
  const [sel, setSel] = useState<RaceIndex | null>(null);
  const [detail, setDetail] = useState<DetailRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // initial load + URL hydrate (?rk=&y=)
  useEffect(() => {
    Promise.all([loadRaces(), loadViz()]).then(([rs, v]) => {
      setRaces(rs); setViz(v);
      const p = new URLSearchParams(location.search);
      const rk = p.get("rk"), y = p.get("y");
      if (rk && y) {
        const m = rs.find((r) => r.rk === rk && String(r.y) === y);
        if (m) pick(m, false);
      }
    }).catch((e) => setErr(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function pick(r: RaceIndex, pushUrl = true) {
    setSel(r); setDetail(null);
    if (pushUrl) history.pushState(null, "", `?rk=${encodeURIComponent(r.rk)}&y=${r.y}`);
    loadRaceDetail(r.file).then(setDetail).catch((e) => setErr(String(e)));
  }

  const crossRows = useMemo(
    () => (sel ? viz.filter((v) => v.rk === sel.rk).map((v) => ({ y: v.y, t: v.t })) : []),
    [viz, sel],
  );

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!races.length) return <p className="text-muted">載入中…</p>;

  if (!sel) return <RacePicker races={races} onPick={(r) => pick(r)} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-ink">{sel.y} {sel.rn}</h1>
          <p className="text-sm text-muted">{sel.s} · {sel.rows.toLocaleString()} 筆成績</p>
        </div>
        <button className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent"
          onClick={() => { setSel(null); history.pushState(null, "", location.pathname); }}>← 換一場</button>
      </div>

      {!detail ? <p className="text-muted">載入排行榜…</p> : (
        <>
          <Card title="領獎台"><Podium rows={detail} /></Card>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="你贏過多少%" hint="輸入你的完賽時間"><PercentileWidget rows={detail} /></Card>
            <Card title="完賽時間分布" hint="每 5 分鐘一桶"><RaceTimeHistogram rows={detail} /></Card>
            {sel.multi_year && <Card title="跨年:變快了嗎" hint="冠軍與中位完賽時間"><CrossYearTrend rows={crossRows} /></Card>}
            {sel.has_team && <Card title="車隊戰力榜" hint="前 10 名人次"><TeamStrength rows={detail} /></Card>}
          </div>
          <Card title="排行榜"><Leaderboard rows={detail} /></Card>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: /race 頁** — `web/src/pages/race.astro`

```astro
---
import Base from "../layouts/Base.astro";
import RaceDetailApp from "../components/race/RaceDetailApp.tsx";
---
<Base title="賽事 | 台灣公路車賽事成績儀表板">
  <h1 class="font-display text-3xl">賽事</h1>
  <p class="mt-2 mb-6 text-muted">選一場賽事,查看排行榜、領獎台、完賽時間分布,並用 percentile 看你的成績落點。</p>
  <RaceDetailApp client:only="react" />
</Base>
```

- [ ] **Step 3: build + 型別 + 測試**

Run: `cd web && npm run build && npx astro check && npm test`
Expected: build 成功(`dist/race/index.html`);astro check 0 errors;vitest 全綠(format + aggregate + overview + racedetail)。

- [ ] **Step 4: 端到端瀏覽器驗證(控制端執行)**

啟 `cd web && npm run preview`(背景):
- 開 `http://localhost:4321/race` → 顯示賽事選擇(依系列分組)。
- 選「太平山王」(多年、競技)→ 顯示領獎台、percentile、時間分布、跨年折線(有 2 年)、車隊戰力榜、排行榜表。
- percentile:輸入 `2:30:00` → 顯示「你贏過 X%」。
- 排行榜:切換組別、翻頁正常。
- 直接開 `http://localhost:4321/race?rk=<某rk>&y=2026` → 直接進該場(URL 還原)。
驗證後關閉 preview。

- [ ] **Step 5: Commit**

```bash
cd C:/Users/user/Desktop/tw-cycling-data
git add web/src/components/race/RaceDetailApp.tsx web/src/pages/race.astro
git commit -m "feat(web): race detail page (leaderboard, percentile, podium, cross-year, team)"
```

---

## 完成標準(Plan 4)

- `python -m pytest scrapers/test_build_viz.py` 與 `cd web && npm test` 全綠;`npm run build`、`npx astro check` 通過。
- `races.json` 每筆有 `file`;`/race` 可選賽事 → 載入該場排行榜。
- 排行榜(分頁+組別篩選)、percentile「你贏過多少%」、領獎台、時間分布皆正確。
- 多年賽顯示跨年折線;競技賽顯示車隊戰力榜;單年/無車隊則隱藏對應卡片。
- URL `?rk=&y=` 可直接進入特定賽事。

---

## Self-Review(對照 spec 頁 C)

- 排行榜表(遮罩姓名/分頁/組別篩選)→ Task 3 Leaderboard ✓
- C5 percentile「你贏過多少%」→ Task 4 PercentileWidget(用 format.percentileBeaten)✓
- 該場時間分布 + 領獎台 → Task 4 RaceTimeHistogram + Podium ✓
- C6 跨年「變快了嗎」→ Task 5 CrossYearTrend(viz 依 rk 篩,crossYear)✓(多年才顯示)
- C12 車隊戰力榜 → Task 5 TeamStrength ✓(has_team 才顯示)
- 賽事選擇 + URL 還原 → Task 6 RacePicker + RaceDetailApp(?rk=&y=)✓
- 資料檔名單一真相 → Task 1 race_file_name + races.json `file`(前端不重算)✓
- Placeholder 掃描:每步含完整程式;無 TBD。
- 型別一致:`DetailRow`/`RaceIndex(+file)` 於 racedetail、components、data-load 一致;`PodiumEntry/TeamStat/YearStat` 由 racedetail 匯出;沿用 aggregate.histogram/quantile、format.secondsToHMS/hmsToSeconds/percentileBeaten。
- DRY:沿用既有 EChart/data-load/format/aggregate;cross-year 用既有 viz.json(不另存多檔)。
