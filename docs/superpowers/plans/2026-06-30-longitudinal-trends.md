# 長期縱貫趨勢 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 補資料集缺的縱貫面——完賽時間分布帶(P25/中位/P75)逐年、女性比例逐年、分齡組成逐年——做成新頁 `/trends`,並把 /race 的 `CrossYearTrend` 從兩線升級為分布帶。

**Architecture:** 後端小幅延伸既有 `build_crossyear`(加 p25/p75/n)與 `build_overview`(加 genderTrend/ageTrend),不新增大型資料檔。前端做一個共用 `FinishTimeBand` 圖(/race 與 /trends 共用),加兩個逐年圖(性別、分齡),組成新頁 `/trends`。

**Tech Stack:** Python(scrapers,重用既有 `_quantile`)、Astro + React + ECharts + TypeScript + vitest、pytest。

## Global Constraints

- **時間趨勢只在同一 race_key 內**(全體逐年會被賽事組合混淆 → 不做)。
- **誠實標註涵蓋/樣本**:女性比例僅「已知性別」(覆蓋 ~63%);某年「已知性別」n < 30 不畫該年點。分齡僅有 `age_band` 者(~36%),UI 標「僅競技/分組賽有分齡」。
- **分齡 band 固定順序**:`["U19","19-29","30-39","40-49","50-59","60+"]`(排除 `MASTER` 雜訊)。
- **分位數**:重用 `build_viz.py:_quantile`(線性內插,對齊前端 `aggregate.ts`)。`p25=round(_quantile(ts,0.25))`、`median=round(_quantile(ts,0.5))`、`p75=round(_quantile(ts,0.75))`。
- **純聚合,零個資**。overview.json 維持 <10KB。
- **不整合 API/MCP**(YAGNI)。
- 既有測試流程:`python -m pytest scrapers/` 綠、`vitest` 綠、astro build 成功、瀏覽器抽查;每 task 自己 commit。

## 已確認的現況

- `viz`(slim record)鍵:`rk, y, mon, s, rc, cat, g, ag(=age_band), t(int 秒), dist, plat …`。
- `build_overview(viz)` 回 `{kpi, heat, trend, women, composition}`;`build_crossyear(viz)` 回 `{rk: [{y, winner, median}]}`(只收 ≥2 年的 race_key)。
- `CrossYearTrend.tsx` 目前畫「冠軍」「中位」兩條線,prop `cy: {y,winner,median}[]`,僅 `RaceDetailApp` 使用。
- 前端 loader 已有 `loadOverview()`、`loadCrossYear()`(回整個 map)、`loadRaces()`。`EChart`/`ChartEmpty` 在 `web/src/components/charts/`,`secondsToHMS` 在 `format.ts`。

---

## File Structure

**修改(後端):** `scrapers/build_viz.py`(`build_crossyear` 加 p25/p75/n;`build_overview` 加 genderTrend/ageTrend,新增 `_gender_trend`/`_age_trend` 純函式)、`scrapers/test_build_viz.py`(新增或既有)
**修改(前端型別):** `web/src/lib/overview.ts`(`OverviewData` 加 `genderTrend`/`ageTrend`,新增型別)、`web/src/lib/types.ts` 若 CrossYear 型別在此
**新增(前端):** `web/src/components/charts/FinishTimeBand.tsx`、`web/src/components/trends/GenderShareTrend.tsx`、`web/src/components/trends/AgeCompositionTrend.tsx`、`web/src/components/trends/TrendsApp.tsx`、`web/src/pages/trends.astro`
**修改(前端):** `web/src/components/race/CrossYearTrend.tsx`(改用分布帶)、`web/src/layouts/Base.astro`(導覽)

---

## Task 1: 後端 — 分布帶 + 性別/分齡逐年聚合

延伸既有 build,加分位帶與兩個逐年聚合。交付物:重建後 `race_crossyear.json` 帶 p25/p75/n、`overview.json` 帶 genderTrend/ageTrend;純函式測試通過。

**Files:**
- Modify: `scrapers/build_viz.py`(`build_crossyear` 第 228–232 區;`build_overview` 結尾 return;新增 `_gender_trend`、`_age_trend`、`AGE_BANDS`)
- Test: `scrapers/test_build_viz.py`(若不存在則建立)

**Interfaces:**
- Consumes: 既有 `_quantile`、`viz` 列(鍵 `y,g,ag,rk,t`)。
- Produces:
  - `build_crossyear(viz)` 每年條目新增 `p25,p75,n`(`{y,winner,median,p25,p75,n}`)。
  - `AGE_BANDS = ["U19","19-29","30-39","40-49","50-59","60+"]`
  - `_gender_trend(viz, years) -> {"years":[...], "f":[...], "known":[...]}`
  - `_age_trend(viz, years) -> {"years":[...], "bands":AGE_BANDS, "pct":[[...]...]}`
  - `build_overview` 回傳新增 `genderTrend`、`ageTrend`。

- [ ] **Step 1: Write the failing test**

新增 `scrapers/test_build_viz.py`(若已存在則追加這些測試;import 既有模組):

```python
import build_viz as BV


def _viz(**kw):
    base = {"rk": "R", "y": 2024, "mon": 5, "s": "S", "rc": None, "cat": None,
            "g": None, "ag": None, "t": 3600, "dist": None, "plat": "p"}
    base.update(kw)
    return base


def test_build_crossyear_adds_band_and_count():
    rows = ([_viz(y=2023, t=t) for t in (100, 200, 300, 400, 500)]
            + [_viz(y=2024, t=t) for t in (110, 210, 310)])
    cy = BV.build_crossyear(rows)["R"]
    y2023 = next(r for r in cy if r["y"] == 2023)
    assert y2023["winner"] == 100 and y2023["n"] == 5
    assert y2023["p25"] <= y2023["median"] <= y2023["p75"]
    assert y2023["median"] == 300                 # _quantile(...,0.5) of 100..500
    y2024 = next(r for r in cy if r["y"] == 2024)
    assert y2024["n"] == 3 and y2024["winner"] == 110


def test_gender_trend_counts_known_only():
    rows = [_viz(y=2023, g="M"), _viz(y=2023, g="F"), _viz(y=2023, g=None),
            _viz(y=2024, g="F")]
    gt = BV._gender_trend(rows, [2023, 2024])
    assert gt["years"] == [2023, 2024]
    assert gt["f"] == [1, 1] and gt["known"] == [2, 1]   # None excluded from known


def test_age_trend_pct_excludes_master_and_unaged():
    rows = [_viz(y=2024, ag="30-39"), _viz(y=2024, ag="30-39"),
            _viz(y=2024, ag="40-49"), _viz(y=2024, ag="MASTER"),
            _viz(y=2024, ag=None)]
    at = BV._age_trend(rows, [2024])
    assert at["bands"] == BV.AGE_BANDS
    bi = at["bands"].index("30-39"); bj = at["bands"].index("40-49")
    # denominator = in-band aged only = 3 (MASTER + None excluded)
    assert at["pct"][bi][0] == 67 and at["pct"][bj][0] == 33
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_build_viz.py -v`
Expected: FAIL(`AttributeError: module 'build_viz' has no attribute '_gender_trend'` 與 crossyear 無 `n`/`p25`)

- [ ] **Step 3: Extend `build_crossyear` in `scrapers/build_viz.py`**

把第 228–232 區的迴圈改為(加 p25/p75/n):

```python
        rows = []
        for y in sorted(years):
            ts = sorted(years[y])
            rows.append({"y": y, "winner": ts[0],
                         "median": round(_quantile(ts, 0.5)),
                         "p25": round(_quantile(ts, 0.25)),
                         "p75": round(_quantile(ts, 0.75)),
                         "n": len(ts)})
        out[rk] = rows
```

- [ ] **Step 4: Add `AGE_BANDS` + the two trend helpers (above `build_overview`)**

```python
AGE_BANDS = ["U19", "19-29", "30-39", "40-49", "50-59", "60+"]


def _gender_trend(viz, years):
    """Per-year female count and known-gender total (M/F only)."""
    yi = {y: i for i, y in enumerate(years)}
    f = [0] * len(years)
    known = [0] * len(years)
    for r in viz:
        if r["y"] is None or r["g"] not in ("M", "F"):
            continue
        i = yi[r["y"]]
        known[i] += 1
        if r["g"] == "F":
            f[i] += 1
    return {"years": years, "f": f, "known": known}


def _age_trend(viz, years):
    """Per-year age-band composition as % of that year's aged finishers
    (only AGE_BANDS count; MASTER and unaged excluded from numerator+denominator)."""
    yi = {y: i for i, y in enumerate(years)}
    band_i = {b: i for i, b in enumerate(AGE_BANDS)}
    counts = [[0] * len(years) for _ in AGE_BANDS]
    totals = [0] * len(years)
    for r in viz:
        if r["y"] is None or r["ag"] not in band_i:
            continue
        yj = yi[r["y"]]
        counts[band_i[r["ag"]]][yj] += 1
        totals[yj] += 1
    pct = [[round(100 * counts[b][j] / totals[j]) if totals[j] else 0
            for j in range(len(years))] for b in range(len(AGE_BANDS))]
    return {"years": years, "bands": AGE_BANDS, "pct": pct}
```

- [ ] **Step 5: Wire the two trends into `build_overview`'s return**

把 `build_overview` 結尾的 return(第 213–214 行)改為:

```python
    return {"kpi": kpi, "heat": heat, "trend": trend, "women": women,
            "composition": composition,
            "genderTrend": _gender_trend(viz, years),
            "ageTrend": _age_trend(viz, years)}
```

(`years` 已在 `build_overview` 內定義於第 160 行,直接重用。)

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest scrapers/test_build_viz.py -v`
Expected: PASS(3 tests)

- [ ] **Step 7: Rebuild real data + sanity-check**

Run:
```bash
python scrapers/build_viz.py
python -c "import json;o=json.load(open('web/public/data/v1/overview.json',encoding='utf-8'));print('genderTrend years',len(o['genderTrend']['years']));print('ageTrend bands',o['ageTrend']['bands']);cy=json.load(open('web/public/data/v1/race_crossyear.json',encoding='utf-8'));k=next(iter(cy));print('crossyear sample',cy[k][0])"
```
Expected: genderTrend/ageTrend 存在;crossyear 樣本含 `p25/p75/n`。

- [ ] **Step 8: Run full scrapers suite + commit**

Run: `python -m pytest scrapers/ -q`
Expected: 全綠。

```bash
git add scrapers/build_viz.py scrapers/test_build_viz.py web/public/data/v1/overview.json web/public/data/v1/race_crossyear.json
git commit -m "feat(trends): crossyear p25/p75/n band + per-year gender/age trends in overview"
```

---

## Task 2: 共用分布帶圖 + 升級 /race CrossYearTrend

做一個 `FinishTimeBand` 圖,讓 /race 的跨年圖從兩線變成分布帶。交付物:`FinishTimeBand` 元件,`CrossYearTrend` 改用它;/race 多年賽事頁顯示帶。

**Files:**
- Create: `web/src/components/charts/FinishTimeBand.tsx`
- Modify: `web/src/components/race/CrossYearTrend.tsx`
- Modify: `web/src/lib/overview.ts`(`CrossYearMap` 條目型別加 `p25,p75,n`;新增 `GenderTrend`/`AgeTrend` 型別 + `OverviewData` 欄位)

**Interfaces:**
- Consumes: `EChart`(`../charts/EChart`)、`ChartEmpty`、`secondsToHMS`。
- Produces:
  - 型別 `CrossYearPoint { y:number; winner:number; median:number; p25:number; p75:number; n:number }`,`CrossYearMap = Record<string, CrossYearPoint[]>`。
  - `GenderTrend { years:number[]; f:number[]; known:number[] }`、`AgeTrend { years:number[]; bands:string[]; pct:number[][] }`;`OverviewData` 加 `genderTrend:GenderTrend; ageTrend:AgeTrend`。
  - `FinishTimeBand({ cy }: { cy: CrossYearPoint[] })` React 元件。

- [ ] **Step 1: Update types in `web/src/lib/overview.ts`**

把現有 `CrossYearMap`(第 8 行)改為具名點型別,並加 trend 型別 + OverviewData 欄位:

```ts
export interface CrossYearPoint { y: number; winner: number; median: number; p25: number; p75: number; n: number; }
export type CrossYearMap = Record<string, CrossYearPoint[]>;

export interface GenderTrend { years: number[]; f: number[]; known: number[]; }
export interface AgeTrend { years: number[]; bands: string[]; pct: number[][]; }
```

並把 `OverviewData` 介面(第 6 行)加上兩欄:

```ts
export interface OverviewData { kpi: Kpi; heat: Heat; trend: Trend; women: WomenShare[]; composition: Composition; genderTrend: GenderTrend; ageTrend: AgeTrend; }
```

- [ ] **Step 2: Implement `web/src/components/charts/FinishTimeBand.tsx`**

```tsx
import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import ChartEmpty from "./ChartEmpty";
import { secondsToHMS } from "../../lib/format";
import type { CrossYearPoint } from "../../lib/overview";

/** Cross-year finish-time evolution for ONE race: median line + P25–P75 band
 * (drawn as a transparent P25 baseline + stacked filled range) + winner line.
 * Shared by the race page and the /trends page. */
export default function FinishTimeBand({ cy }: { cy: CrossYearPoint[] }) {
  if (cy.length < 2) return <ChartEmpty height={260}>僅單一年度,無跨年比較</ChartEmpty>;
  const years = cy.map((c) => String(c.y));
  const option: EChartsOption = {
    grid: { left: 64, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const c = cy[p[0].dataIndex];
        return `${c.y}(${c.n} 人）<br/>冠軍 ${secondsToHMS(c.winner)}`
          + `<br/>中位 ${secondsToHMS(c.median)}`
          + `<br/>P25–P75 ${secondsToHMS(c.p25)} – ${secondsToHMS(c.p75)}`;
      },
    },
    legend: { bottom: 0, data: ["冠軍", "中位"] },
    xAxis: { type: "category", data: years },
    yAxis: { type: "value", name: "完賽時間", axisLabel: { formatter: (v: number) => secondsToHMS(v) } },
    series: [
      // P25 baseline (invisible) + range area to P75 — stacked so the fill spans P25..P75
      { name: "_p25", type: "line", stack: "band", symbol: "none", lineStyle: { opacity: 0 },
        data: cy.map((c) => c.p25), tooltip: { show: false }, silent: true },
      { name: "P25–P75", type: "line", stack: "band", symbol: "none", lineStyle: { opacity: 0 },
        areaStyle: { color: "#5B7B8A", opacity: 0.18 },
        data: cy.map((c) => c.p75 - c.p25), tooltip: { show: false }, silent: true },
      { name: "中位", type: "line", smooth: true, symbol: "circle",
        itemStyle: { color: "#5B7B8A" }, data: cy.map((c) => c.median) },
      { name: "冠軍", type: "line", smooth: true, symbol: "circle",
        itemStyle: { color: "#D97757" }, data: cy.map((c) => c.winner) },
    ],
  };
  return <EChart option={option} height={260} />;
}
```

- [ ] **Step 3: Rewrite `web/src/components/race/CrossYearTrend.tsx` to use it**

```tsx
import FinishTimeBand from "../charts/FinishTimeBand";
import type { CrossYearPoint } from "../../lib/overview";

export default function CrossYearTrend({ cy }: { cy: CrossYearPoint[] }) {
  return <FinishTimeBand cy={cy} />;
}
```

(保留此薄包裝,讓 `RaceDetailApp` 既有 import 路徑不變;`cy` 現在帶 p25/p75/n,由 `race_crossyear.json` 提供。)

- [ ] **Step 4: Build + browser-verify /race**

Run: `npm --prefix web run build`
Expected: 成功。瀏覽器抽查一場**多年**賽事的 /race(如「捷安特自行車嘉年華」或「戀戀197」),確認跨年圖顯示中位線 + P25–P75 帶 + 冠軍線,tooltip 顯示人數與分位。

- [ ] **Step 5: Commit**

```bash
git add web/src/components/charts/FinishTimeBand.tsx web/src/components/race/CrossYearTrend.tsx web/src/lib/overview.ts
git commit -m "feat(trends): FinishTimeBand (median + P25-P75) shared; /race CrossYearTrend uses it"
```

---

## Task 3: `/trends` 頁(性別 + 分齡逐年 + 賽事分布帶)

新頁整合三張縱貫圖。交付物:`/trends` 可用,瀏覽器抽查正確。

**Files:**
- Create: `web/src/components/trends/GenderShareTrend.tsx`
- Create: `web/src/components/trends/AgeCompositionTrend.tsx`
- Create: `web/src/components/trends/TrendsApp.tsx`
- Create: `web/src/pages/trends.astro`
- Modify: `web/src/layouts/Base.astro`(導覽連結)

**Interfaces:**
- Consumes: `loadOverview()`、`loadCrossYear()`、`loadRaces()`(`data-load.ts`);`GenderTrend`/`AgeTrend`/`CrossYearMap`(Task 2);`FinishTimeBand`(Task 2);`EChart`/`ChartEmpty`/`Skeleton`/`Card`(既有);`secondsToHMS`。

- [ ] **Step 1: Implement `GenderShareTrend.tsx`**

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import type { GenderTrend } from "../../lib/overview";

const MIN_KNOWN = 30; // years with fewer known-gender finishers are not plotted

export default function GenderShareTrend({ gt }: { gt: GenderTrend }) {
  const pts = gt.years.map((y, i) =>
    gt.known[i] >= MIN_KNOWN ? Math.round((100 * gt.f[i]) / gt.known[i]) : null);
  if (pts.every((p) => p == null)) return <ChartEmpty height={260}>已知性別樣本不足</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 44, right: 16, top: 24, bottom: 32 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const i = p[0].dataIndex;
        return p[0].value == null ? `${gt.years[i]}:樣本不足`
          : `${gt.years[i]}:女性 ${p[0].value}%(${gt.f[i]}/${gt.known[i]})`;
      },
    },
    xAxis: { type: "category", data: gt.years.map(String) },
    yAxis: { type: "value", name: "女性 %", max: 100, axisLabel: { formatter: "{value}%" } },
    series: [{ name: "女性比例", type: "line", smooth: true, connectNulls: false,
      itemStyle: { color: "#D97757" }, data: pts }],
  };
  return <EChart option={option} height={260} />;
}
```

- [ ] **Step 2: Implement `AgeCompositionTrend.tsx`**

```tsx
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import type { AgeTrend } from "../../lib/overview";

const COLORS = ["#9CC3D5", "#5B7B8A", "#7FB069", "#E6B05E", "#D97757", "#8E6C88"];

export default function AgeCompositionTrend({ at }: { at: AgeTrend }) {
  if (!at.years.length) return <ChartEmpty height={260}>無分齡資料</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 44, right: 16, top: 24, bottom: 48 },
    tooltip: { trigger: "axis" },
    legend: { bottom: 0 },
    xAxis: { type: "category", data: at.years.map(String) },
    yAxis: { type: "value", name: "% (分齡者)", max: 100, axisLabel: { formatter: "{value}%" } },
    series: at.bands.map((b, bi) => ({
      name: b, type: "line", stack: "age", areaStyle: { opacity: 0.7 }, symbol: "none",
      itemStyle: { color: COLORS[bi % COLORS.length] }, data: at.pct[bi],
    })),
  };
  return <EChart option={option} height={260} />;
}
```

- [ ] **Step 3: Implement `TrendsApp.tsx`**

(對齊 `InsightsApp`/`BenchmarkTool` 的 self-loading island 慣例:useEffect 載資料 + Skeleton。沿用既有 `Card`/`Skeleton` — 實作時確認其 import 路徑與既有頁一致,例如 `InsightsApp` 怎麼引用 Card/Skeleton 就照樣。)

```tsx
import { useEffect, useMemo, useState } from "react";
import { loadOverview, loadCrossYear, loadRaces } from "../../lib/data-load";
import type { OverviewData, CrossYearMap } from "../../lib/overview";
import type { RaceIndex } from "../../lib/types";
import Skeleton from "../Skeleton";
import GenderShareTrend from "./GenderShareTrend";
import AgeCompositionTrend from "./AgeCompositionTrend";
import FinishTimeBand from "../charts/FinishTimeBand";

export default function TrendsApp() {
  const [ov, setOv] = useState<OverviewData | null>(null);
  const [cy, setCy] = useState<CrossYearMap | null>(null);
  const [races, setRaces] = useState<RaceIndex[] | null>(null);
  const [rk, setRk] = useState("");

  useEffect(() => {
    Promise.all([loadOverview(), loadCrossYear(), loadRaces()])
      .then(([o, c, r]) => { setOv(o); setCy(c); setRaces(r); })
      .catch(() => { setOv(null); });
  }, []);

  // multi-year races that have band data, labelled from the races index
  const bandRaces = useMemo(() => {
    if (!cy || !races) return [];
    const name = new Map(races.map((r) => [r.rk, r.rn] as const));
    return Object.keys(cy)
      .map((k) => ({ rk: k, rn: name.get(k) ?? k, n: cy[k].length }))
      .sort((a, b) => b.n - a.n);
  }, [cy, races]);

  if (!ov || !cy || !races) return <Skeleton cards={3} />;
  const activeRk = rk && cy[rk] ? rk : bandRaces[0]?.rk ?? "";

  return (
    <div className="space-y-6">
      <section>
        <h2 className="font-display text-xl">女性參與比例(逐年)</h2>
        <p className="mb-2 text-xs text-muted">僅含已知性別者(約 6 成);樣本太少的年份不畫。</p>
        <GenderShareTrend gt={ov.genderTrend} />
      </section>
      <section>
        <h2 className="font-display text-xl">分齡組成(逐年)</h2>
        <p className="mb-2 text-xs text-muted">僅競技/分組賽有分齡(約 36%);各年為「該年有分齡者」的占比。</p>
        <AgeCompositionTrend at={ov.ageTrend} />
      </section>
      <section>
        <h2 className="font-display text-xl">完賽時間演變(單場跨年)</h2>
        <p className="mb-2 text-xs text-muted">同一賽事跨年比較才公平:中位線 + P25–P75 分布帶 + 冠軍。</p>
        <select aria-label="選賽事" value={activeRk} onChange={(e) => setRk(e.target.value)}
          className="mb-2 w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink">
          {bandRaces.map((r) => <option key={r.rk} value={r.rk}>{r.rn}（{r.n} 年）</option>)}
        </select>
        {activeRk && <FinishTimeBand cy={cy[activeRk]} />}
      </section>
    </div>
  );
}
```

- [ ] **Step 4: Implement `web/src/pages/trends.astro`**

```astro
---
import Base from "../layouts/Base.astro";
import TrendsApp from "../components/trends/TrendsApp.tsx";
---
<Base title="長期趨勢 | 台灣公路車賽事成績儀表板">
  <h1 class="font-display text-3xl">長期趨勢</h1>
  <p class="mt-2 mb-6 text-muted">2009–2026 的縱貫演變:女性參與、分齡組成,以及同一賽事跨年的完賽時間分布。皆為去識別化聚合,標註涵蓋限制。</p>
  <TrendsApp client:only="react" />
</Base>
```

- [ ] **Step 5: Add the nav link in `web/src/layouts/Base.astro`**

在導覽列(`<a href="/benchmark" …>分齡對標</a>` 之後)加入:

```astro
<a href="/trends" class="py-1 hover:text-accent">長期趨勢</a>
```

- [ ] **Step 6: Build + browser-verify /trends**

Run: `npm --prefix web run build`
Expected: 成功,`/trends/index.html` 產出。瀏覽器抽查 `/trends`:女性比例折線(樣本少的年份斷點)、分齡組成堆疊、賽事下拉切換顯示分布帶。

- [ ] **Step 7: Commit**

```bash
git add web/src/components/trends/ web/src/pages/trends.astro web/src/layouts/Base.astro
git commit -m "feat(trends): /trends page — per-year gender share, age composition, per-race finish-time band"
```

---

## Self-Review

**1. Spec coverage:** 分布帶 p25/p75/n → Task 1+2 ✅;女性比例逐年 → Task 1(_gender_trend)+ Task 3(GenderShareTrend)✅;分齡組成逐年 → Task 1(_age_trend)+ Task 3 ✅;共用 FinishTimeBand 兩處用 → Task 2(/race)+ Task 3(/trends)✅;CrossYearTrend 升級 → Task 2 ✅;誠實標註(年內門檻 30、覆蓋字)→ Task 3 UI ✅;全體時間逐年不做 → 只在 race_key 內 ✅;不整合 API/MCP → 無此 task ✅;分齡 band 排序固定排除 MASTER → Task 1 AGE_BANDS ✅。

**2. Placeholder scan:** 無 TBD;每步附完整程式。Task 3 Step 3 對 Card/Skeleton import 給「對齊既有頁」具體指示(非佔位)。

**3. Type consistency:** `CrossYearPoint`(Task 2 定義,含 p25/p75/n)被 `FinishTimeBand`/`CrossYearTrend`/`TrendsApp` 一致使用;`GenderTrend`/`AgeTrend`(Task 2)被 Task 3 三元件一致使用;後端 `_gender_trend`/`_age_trend`/`build_crossyear` 輸出(Task 1)鍵名與前端型別一致(years/f/known;years/bands/pct;y/winner/median/p25/p75/n)。

---

## 執行順序

Task 1 → 2 → 3。Task 1 先(產生帶 band 的資料);Task 2 定義前端型別 + 共用圖(Task 3 依賴);Task 3 組頁。
