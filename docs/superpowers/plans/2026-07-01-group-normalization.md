# 分組/距離正規化 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 winner/median/分位/benchmark 的比較單位從 `race_key` 改為 **(race_key, result_label)**(距離/項目),讓混多組的賽事不再跨組混比。

**Architecture:** 後端 `build_crossyear` 與 `benchmarks.build_index` 改成多一層 `group`(result_label,缺值=`全部`)。前端型別加 group 維度,/race、/trends、/benchmark 加「距離/組別」選擇;`FinishTimeBand` 不變。MCP `benchmark_lookup`/`race_benchmark` 加選填 group。重建 web/v1(不動 dataset)。

**Tech Stack:** Python(build_viz、benchmarks、MCP)、Astro + React + TS + vitest、pytest。

## Global Constraints

- **分組鍵 = `result_label`**;缺值 → 群組名 `全部`。
- **crossyear**:每 (race_key, group) 各自 ≥2 年才收;沿用 `_quantile`;由**完賽記錄**(含 result_label)計算(非 slim viz)。
- **benchmarks**:cohort(all/age/age|g/cat)在**各 group 內**計算;門檻 n≥20、101 斷點;group 保留須其 `all` cohort 達標;race 保留須 ≥1 group。
- 向後相容:MCP `race_benchmark` 的 `result_label` 選填,未給時取預設(最大 all.n 的 group)。
- 不動 dataset 逐筆、不重發 release;重建 web/v1。
- 既有測試:`pytest scrapers/ mcp-server/` + `vitest` 綠;build 成功。

## 已確認的現況

- `build_viz.main`:`finishers = [r for r in records if is_finisher(r)]`;`viz = [slim_record(r) ...]`;呼叫 `build_crossyear(viz)`。完賽記錄 `r` 有 `race_key/year/finish_seconds/result_label`。slim viz **無** result_label。
- `build_crossyear(viz)` 現況見下 Task 1;`benchmarks.build_index(rows)` 現況見下 Task 2(rows 來自 `common.iter_records(master.public.json)`,有 result_label)。
- 前端 `CrossYearPoint`(overview.ts)不變;`CrossYearMap` 現為 `Record<string, CrossYearPoint[]>`。`benchmark.ts` 有 `availableCohorts(race)`/`pickDefaultCohort(race)`/`parseFinishTime`。`BenchmarkRace` 現為 `{rn, years, cohorts}`。
- 消費端:`RaceDetailApp` 用 `<CrossYearTrend cy={crossYear[sel.rk] ?? []} />`;`TrendsApp` 用 `cy[activeRk]`;`BenchmarkTool` 用 `data[rk]` → `availableCohorts(race)`。MCP `query.benchmark_lookup(benchmarks, race_key, seconds, age_band, gender)`、`server.race_benchmark(race_key, finish_time, age_band, gender)`。

---

## Task 1: `build_crossyear` → 依 (race_key, result_label) 分組

**Files:** Modify `scrapers/build_viz.py`(`build_crossyear` + `main` 的呼叫);Test `scrapers/test_build_viz.py`

**Interfaces:** Produces `build_crossyear(records) -> {race_key: {group: [{y,winner,median,p25,p75,n}]}}`。

- [ ] **Step 1: Write the failing test**

在 `scrapers/test_build_viz.py` 追加:

```python
def _fin(rk, y, t, label):
    return {"race_key": rk, "year": y, "finish_seconds": t, "result_label": label,
            "status": None}


def test_build_crossyear_groups_by_result_label():
    rows = ([_fin("R", 2023, t, "TT") for t in (80, 90, 100)]
            + [_fin("R", 2024, t, "TT") for t in (82, 92)]
            + [_fin("R", 2023, t, "公路") for t in (900, 1000, 1100)]
            + [_fin("R", 2024, t, "公路") for t in (950, 1050)])
    cy = BV.build_crossyear(rows)["R"]
    assert set(cy) == {"TT", "公路"}
    tt2023 = next(p for p in cy["TT"] if p["y"] == 2023)
    assert tt2023["winner"] == 80 and tt2023["median"] == 90 and tt2023["n"] == 3
    rd2023 = next(p for p in cy["公路"] if p["y"] == 2023)
    assert rd2023["winner"] == 900 and rd2023["median"] == 1000
    # a group with <2 years is dropped
    rows2 = [_fin("S", 2024, t, "只有一年") for t in (100, 200, 300)]
    assert "S" not in BV.build_crossyear(rows2)


def test_build_crossyear_missing_label_is_all_group():
    rows = ([_fin("R", 2023, t, None) for t in (100, 200)]
            + [_fin("R", 2024, t, None) for t in (110, 210)])
    cy = BV.build_crossyear(rows)["R"]
    assert set(cy) == {"全部"}
```

Run: `python -m pytest scrapers/test_build_viz.py -k crossyear -v` → FAIL(舊版依 race_key、無 group)。

- [ ] **Step 2: Replace `build_crossyear` in `scrapers/build_viz.py`**

把現有 `def build_crossyear(viz): ...`(整個函式)換成:

```python
def build_crossyear(records):
    """Per (race_key, result_label) cross-year winner/median/quartiles. Grouping
    by result_label (the distance/event) so a race that mixes distances (e.g. TT
    vs road) never blends unlike groups. Reads finisher records (which carry
    result_label; the slim viz rows do not)."""
    by = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # rk -> group -> y -> [t]
    for r in records:
        rk, y, t = r.get("race_key"), r.get("year"), r.get("finish_seconds")
        if not rk or y is None or t is None:
            continue
        group = r.get("result_label") or "全部"
        by[rk][group][y].append(int(t))
    out = {}
    for rk, groups in by.items():
        gout = {}
        for group, years in groups.items():
            if len(years) < 2:                     # each group needs >=2 years
                continue
            gout[group] = [{"y": y, "winner": (ts := sorted(years[y]))[0],
                            "median": round(_quantile(ts, 0.5)),
                            "p25": round(_quantile(ts, 0.25)),
                            "p75": round(_quantile(ts, 0.75)),
                            "n": len(ts)} for y in sorted(years)]
        if gout:
            out[rk] = gout
    return out
```

- [ ] **Step 3: Update `main` to pass finishers**

在 `build_viz.py:main`,把 `json.dump(build_crossyear(viz), ...)` 改為 `json.dump(build_crossyear(finishers), ...)`(`finishers` 已於 main 定義;它們帶 result_label)。

- [ ] **Step 4: Run tests + regenerate + sanity**

Run:
```bash
python -m pytest scrapers/test_build_viz.py -k crossyear -v
python scrapers/build_viz.py
python -c "import json;cy=json.load(open('web/public/data/v1/race_crossyear.json',encoding='utf-8'));k=next(iter(cy));print(k, list(cy[k])[:3])"
python -m pytest scrapers/ -q
```
Expected: crossyear 測試綠;race_crossyear.json 現為 `{rk: {group: [...]}}`;pytest 全綠。

- [ ] **Step 5: Commit**

```bash
git add scrapers/build_viz.py scrapers/test_build_viz.py web/public/data/v1/race_crossyear.json
git commit -m "feat(normalize): build_crossyear groups by (race_key, result_label)"
```

---

## Task 2: `benchmarks.build_index` → 巢狀 group

**Files:** Modify `scrapers/benchmarks.py`(`build_index`);Test `scrapers/test_benchmarks.py`

**Interfaces:** Produces `build_index(rows, min_n=20) -> {race_key: {rn, groups: {group: {years, cohorts}}}}`。`cohort_keys`/`percentile_breakpoints` 不變。

- [ ] **Step 1: Write the failing test**

在 `scrapers/test_benchmarks.py` 追加(沿用/仿照既有 helper;每組需 ≥20 才收 `all`):

```python
def test_build_index_nests_by_result_label_group():
    rows = []
    for i in range(25):   # group "130K" — 25 finishers
        rows.append({"race_key": "R", "year": 2024, "age_band": "40-49", "gender": "M",
                     "category_raw": "M40", "finish_seconds": 3600 + i, "result_label": "130K",
                     "race_name_canonical": "賽事R", "status": None})
    for i in range(22):   # group "50K" — 22 finishers
        rows.append({"race_key": "R", "year": 2024, "age_band": "30-39", "gender": "M",
                     "category_raw": "M30", "finish_seconds": 1800 + i, "result_label": "50K",
                     "race_name_canonical": "賽事R", "status": None})
    idx = B.build_index(rows, min_n=20)
    assert set(idx["R"]["groups"]) == {"130K", "50K"}
    g130 = idx["R"]["groups"]["130K"]
    assert g130["cohorts"]["all"]["n"] == 25 and len(g130["cohorts"]["all"]["bp"]) == 101
    # each group's `all` uses ONLY that group's times (not blended)
    assert g130["cohorts"]["all"]["bp"][0] == 3600
    assert idx["R"]["groups"]["50K"]["cohorts"]["all"]["bp"][0] == 1800
    assert idx["R"]["rn"] == "賽事R"


def test_build_index_drops_group_without_enough_finishers():
    rows = [{"race_key": "R", "year": 2024, "age_band": None, "gender": None,
             "category_raw": None, "finish_seconds": 3600, "result_label": "tiny",
             "race_name_canonical": "賽事R", "status": None}]
    assert "R" not in B.build_index(rows, min_n=20)  # only 1 finisher in the only group
```

Run: `python -m pytest scrapers/test_benchmarks.py -k group -v` → FAIL。

- [ ] **Step 2: Replace `build_index` in `scrapers/benchmarks.py`**

```python
def build_index(rows, min_n=MIN_COHORT_N):
    """Group finishers by (race_key, result_label); within each group accumulate
    per-cohort finish seconds; emit only cohorts with n>=min_n. A group is kept
    only if its `all` cohort reaches min_n; a race is kept if it has >=1 group."""
    races = {}   # rk -> {rn, groups: {group: {years:set, cohorts:{key:{type,label,_secs}}}}}
    for r in rows:
        rk = r.get("race_key")
        fs = r.get("finish_seconds")
        if not rk or fs is None or not _is_finisher(r):
            continue
        try:
            fs = int(fs)
        except (TypeError, ValueError):
            continue
        group = r.get("result_label") or "全部"
        race = races.setdefault(rk, {
            "rn": r.get("race_name_canonical") or r.get("race_name_raw") or rk, "groups": {}})
        grp = race["groups"].setdefault(group, {"years": set(), "cohorts": {}})
        if r.get("year") is not None:
            grp["years"].add(r["year"])
        for key, ctype, label in cohort_keys(r):
            c = grp["cohorts"].setdefault(key, {"type": ctype, "label": label, "_secs": []})
            c["_secs"].append(fs)

    out = {}
    for rk, race in races.items():
        groups = {}
        for group, grp in race["groups"].items():
            cohorts = {}
            for key, c in grp["cohorts"].items():
                if len(c["_secs"]) < min_n:
                    continue
                secs = sorted(c["_secs"])
                cohorts[key] = {"n": len(secs), "type": c["type"], "label": c["label"],
                                "bp": percentile_breakpoints(secs)}
            if "all" not in cohorts:            # group too small
                continue
            groups[group] = {"years": sorted(grp["years"]), "cohorts": cohorts}
        if groups:
            out[rk] = {"rn": race["rn"], "groups": groups}
    return out
```

- [ ] **Step 3: Run tests + regenerate + sanity**

Run:
```bash
python -m pytest scrapers/test_benchmarks.py -q
python scrapers/build_benchmarks.py
python -c "import json;d=json.load(open('web/public/data/v1/benchmarks.json',encoding='utf-8'));k=next(iter(d));print(k, list(d[k]['groups'])[:4])"
python -m pytest scrapers/ -q
```
Expected: benchmarks 測試綠;benchmarks.json 現為 `{rk: {rn, groups: {...}}}`;pytest 全綠。

- [ ] **Step 4: Commit**

```bash
git add scrapers/benchmarks.py scrapers/test_benchmarks.py web/public/data/v1/benchmarks.json
git commit -m "feat(normalize): benchmarks nested by (race_key, result_label) group"
```

---

## Task 3: 前端型別 + benchmark.ts 群組 helpers

**Files:** Modify `web/src/lib/overview.ts`(CrossYearMap)、`web/src/lib/types.ts`(benchmark 型別)、`web/src/lib/benchmark.ts`;Test `web/src/lib/benchmark.test.ts`

**Interfaces:**
- `CrossYearMap = Record<string, Record<string, CrossYearPoint[]>>`。
- `BenchmarkGroup { years:number[]; cohorts: Record<string,Cohort> }`;`BenchmarkRace { rn:string; groups: Record<string,BenchmarkGroup> }`。
- `availableGroups(race) -> {label,group,n}[]`(依 all.n 降序);`pickDefaultGroup(race) -> string`;`availableCohorts(group)`、`pickDefaultCohort(group)`(改吃 `BenchmarkGroup`)。

- [ ] **Step 1: Update types**

`web/src/lib/overview.ts`:把 `export type CrossYearMap = Record<string, CrossYearPoint[]>;` 改為
`export type CrossYearMap = Record<string, Record<string, CrossYearPoint[]>>;`(race_key → group → points)。

`web/src/lib/types.ts`:把 `BenchmarkRace` 改為分組結構(`Cohort` 不變):

```ts
export interface BenchmarkGroup { years: number[]; cohorts: Record<string, Cohort>; }
export interface BenchmarkRace { rn: string; groups: Record<string, BenchmarkGroup>; }
export type BenchmarkFile = Record<string, BenchmarkRace>;
```
(移除舊 `BenchmarkRace` 的 `years`/`cohorts` 直屬欄位。)

- [ ] **Step 2: Write the failing test**

`web/src/lib/benchmark.test.ts`:把用到 `BenchmarkRace`（舊 `.cohorts`)的既有測試改為新的 `groups` 結構,並新增群組 helper 測試:

```ts
import { availableCohorts, pickDefaultCohort, availableGroups, pickDefaultGroup } from "./benchmark";
import type { BenchmarkRace } from "./types";

const race: BenchmarkRace = {
  rn: "賽事R",
  groups: {
    "130K": { years: [2024], cohorts: {
      all: { n: 100, type: "all", label: "全部完賽者", bp: [] },
      "age:40-49": { n: 60, type: "age", label: "40-49 歲", bp: [] },
    } },
    "50K": { years: [2024], cohorts: { all: { n: 40, type: "all", label: "全部完賽者", bp: [] } } },
  },
};

describe("benchmark groups", () => {
  it("lists groups by size desc + default is largest", () => {
    expect(availableGroups(race).map((g) => g.label)).toEqual(["130K", "50K"]);
    expect(pickDefaultGroup(race)).toBe("130K");
  });
  it("cohorts operate within a group", () => {
    const g = race.groups["130K"];
    expect(availableCohorts(g).map((c) => c.key)).toEqual(["age:40-49", "all"]);
    expect(pickDefaultCohort(g)).toBe("age:40-49");
  });
});
```

Run: `cd web && npx vitest run src/lib/benchmark.test.ts` → FAIL。

- [ ] **Step 3: Update `web/src/lib/benchmark.ts`**

把 `availableCohorts`/`pickDefaultCohort` 的參數改吃 `BenchmarkGroup`,並新增群組 helpers(保留 `parseFinishTime` 不變):

```ts
import type { BenchmarkRace, BenchmarkGroup } from "./types";

/** Distance/event groups within a race, largest (by `all` count) first. */
export function availableGroups(race: BenchmarkRace) {
  return Object.entries(race.groups)
    .map(([label, group]) => ({ label, group, n: group.cohorts.all?.n ?? 0 }))
    .sort((a, b) => b.n - a.n);
}

/** Default group: the largest one. */
export function pickDefaultGroup(race: BenchmarkRace): string {
  return availableGroups(race)[0]?.label ?? "";
}

/** Cohorts within a group, most-specific first: age|gender, age, cat, all. */
export function availableCohorts(group: BenchmarkGroup) {
  const rank = (key: string, type: string) =>
    type === "age" && key.includes("|g:") ? 0 : type === "age" ? 1 : type === "cat" ? 2 : 3;
  return Object.entries(group.cohorts)
    .map(([key, cohort]) => ({ key, cohort }))
    .sort((a, b) => rank(a.key, a.cohort.type) - rank(b.key, b.cohort.type)
      || b.cohort.n - a.cohort.n);
}

/** Default cohort key within a group: plain age band, else category, else all. */
export function pickDefaultCohort(group: BenchmarkGroup): string {
  const c = group.cohorts;
  const plainAge = Object.keys(c).find((k) => c[k].type === "age" && !k.includes("|g:"));
  if (plainAge) return plainAge;
  const cat = Object.keys(c).find((k) => c[k].type === "cat");
  if (cat) return cat;
  return "all";
}
```
(保留原本檔內的 `parseFinishTime`;只改上述四個函式的簽名/實作 + 新增兩個群組 helper。)

- [ ] **Step 4: Run test + commit**

Run: `cd web && npx vitest run src/lib/benchmark.test.ts` → PASS。

```bash
git add web/src/lib/overview.ts web/src/lib/types.ts web/src/lib/benchmark.ts web/src/lib/benchmark.test.ts
git commit -m "feat(normalize): frontend group types + benchmark group helpers"
```

---

## Task 4: /race CrossYearTrend 加組別選擇

**Files:** Modify `web/src/components/race/CrossYearTrend.tsx`

**Interfaces:** Consumes `CrossYearMap[rk]`(= `Record<group, CrossYearPoint[]>`)、`FinishTimeBand`。

- [ ] **Step 1: Rewrite `CrossYearTrend.tsx` to take the group-map + select**

現況:`CrossYearTrend` 是 `FinishTimeBand` 的薄包裝,吃 `cy: CrossYearPoint[]`。改為吃**群組 map**並自帶下拉:

```tsx
import { useState } from "react";
import FinishTimeBand from "../charts/FinishTimeBand";
import ChartEmpty from "../charts/ChartEmpty";
import type { CrossYearPoint } from "../../lib/overview";

/** cy: race_key's group-map (group label -> cross-year points). Shows a group
 * selector when a race mixes distances/events; single-group races auto-select. */
export default function CrossYearTrend({ cy }: { cy: Record<string, CrossYearPoint[]> }) {
  const groups = Object.keys(cy);
  const [sel, setSel] = useState("");
  const active = sel && cy[sel] ? sel : groups[0] ?? "";
  if (!groups.length) return <ChartEmpty height={260}>無跨年資料</ChartEmpty>;
  return (
    <div className="space-y-2">
      {groups.length > 1 && (
        <select aria-label="距離/組別" value={active} onChange={(e) => setSel(e.target.value)}
          className="rounded-lg border border-border bg-surface px-2 py-1 text-xs text-ink">
          {groups.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
      )}
      <FinishTimeBand cy={cy[active]} />
    </div>
  );
}
```

- [ ] **Step 2: Confirm RaceDetailApp passes the group-map**

`RaceDetailApp` 現況傳 `cy={crossYear[sel.rk] ?? []}`。`crossYear[sel.rk]` 現在已是群組 map(型別 Task 3 改過);把 fallback `?? []` 改為 `?? {}`:找到該處改為 `cy={crossYear[sel.rk] ?? {}}`。(其餘不動。)

- [ ] **Step 3: Build + browser-verify /race**

Run: `npm --prefix web run build`
Expected: 成功。瀏覽器抽查一場**多距離**賽事(如桃園繞圈賽)的 /race:出現組別下拉,切換各組看到各自合理的 winner/median 帶;單組賽事無下拉、照常顯示。

- [ ] **Step 4: Commit**

```bash
git add web/src/components/race/CrossYearTrend.tsx web/src/components/race/RaceDetailApp.tsx
git commit -m "feat(normalize): /race cross-year group selector"
```

---

## Task 5: /trends 加組別選擇

**Files:** Modify `web/src/components/trends/TrendsApp.tsx`

**Interfaces:** Consumes `CrossYearMap`(race_key → group → points)、`FinishTimeBand`、races 索引(名稱)。

- [ ] **Step 1: Add group state + selector in TrendsApp**

TrendsApp 現況:`bandRaces` 由 `Object.keys(cy)` 產生,渲染賽事下拉 → `FinishTimeBand cy={cy[activeRk]}`。改為賽事 → 組別 → band:
- `bandRaces` 仍列 race_key(名稱由 races 索引);`activeRk` 不變。
- 新增 `groupSel` state;`activeGroup` = 選的 group,預設 `Object.keys(cy[activeRk])[0]`。
- 賽事下拉之後加**組別下拉**(當 `cy[activeRk]` 有 >1 group 時顯示);`FinishTimeBand cy={cy[activeRk][activeGroup]}`。
- 切換賽事時重置 `groupSel`(讓新賽事用其第一組)。

實作(找到 TrendsApp 內「完賽時間演變」那段,把賽事下拉 + FinishTimeBand 換成):

```tsx
{/* activeRk from the existing race selector; add group selection below it */}
{activeRk && (() => {
  const groupMap = cy[activeRk] ?? {};
  const groups = Object.keys(groupMap);
  const activeGroup = groupSel && groupMap[groupSel] ? groupSel : groups[0] ?? "";
  return (
    <>
      {groups.length > 1 && (
        <select aria-label="距離/組別" value={activeGroup} onChange={(e) => setGroupSel(e.target.value)}
          className="mb-2 ml-2 rounded-lg border border-border bg-surface px-2 py-1 text-sm text-ink">
          {groups.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
      )}
      {activeGroup && <FinishTimeBand cy={groupMap[activeGroup]} />}
    </>
  );
})()}
```
並加 `const [groupSel, setGroupSel] = useState("")`;賽事下拉的 `onChange` 一併 `setGroupSel("")`。`bandRaces` 的 `n`(年數)改用該賽事**最大組**的年數(或維持 race_key 存在即可)——實作時對齊既有 bandRaces 結構,確保 race 有至少一個 group。

> 註:實作時讀 TrendsApp 現有 `bandRaces`/`activeRk`/render 區塊,依上述最小改動接上 group 維度;`GenderShareTrend`/`AgeCompositionTrend` 兩區塊不動。

- [ ] **Step 2: Build + browser-verify /trends**

Run: `npm --prefix web run build`
Expected: 成功。/trends 的「完賽時間演變」:賽事 → 組別(多組時)→ 分布帶;各組合理。

- [ ] **Step 3: Commit**

```bash
git add web/src/components/trends/TrendsApp.tsx
git commit -m "feat(normalize): /trends race+group finish-time band"
```

---

## Task 6: /benchmark 加距離/組別步驟

**Files:** Modify `web/src/components/benchmark/BenchmarkTool.tsx`

**Interfaces:** Consumes `BenchmarkFile`(race → groups → cohorts)、`availableGroups`/`pickDefaultGroup`/`availableCohorts`/`pickDefaultCohort`/`parseFinishTime`、`percentileBeaten`/`secondsToHMS`。

- [ ] **Step 1: Insert a group step in BenchmarkTool**

現況流程:選賽事(`data[rk]`)→ `availableCohorts(race)` → 選 cohort → 時間 → 百分位。改為:選賽事 → **選距離/組別** → 選該組 cohort → 時間 → 百分位。

改動(讀 BenchmarkTool 現檔,依此接上):
- import 加 `availableGroups, pickDefaultGroup`。
- 新增 `groupKey` state;`race = data[rk]`;`activeGroupKey = groupKey && race?.groups[groupKey] ? groupKey : (race ? pickDefaultGroup(race) : "")`;`group = race?.groups[activeGroupKey]`。
- 賽事選好後,若該 race `Object.keys(race.groups).length > 1`,顯示**組別下拉**(`availableGroups(race)`,顯示 label + all 人數);選賽事的 onChange 重置 `groupKey` 與 `cohortKey`。
- cohort 相關改吃 `group`:`availableCohorts(group)`、`pickDefaultCohort(group)`、`group.cohorts[activeKey]`;人數/年份改讀 `group`(`group.years` 若需要)。
- 賽事下拉的顯示可改用「最大組人數」或 race 總人數;年份範圍改用該組 `group.years`(或所有組聯集)。
- 其餘(輸入時間、`percentileBeaten(secs, cohort.bp)`、誠實標註、小樣本警示)不變。

> 註:這是既有元件的接補;實作時保留其 self-loading/錯誤/誠實標註結構,只在「選賽事」與「選 cohort」之間插入群組選擇並把 cohort 來源改成 `group.cohorts`。

- [ ] **Step 2: Build + browser-verify /benchmark**

Run: `npm --prefix web run build`
Expected: 成功。/benchmark:選賽事 → 距離/組別(多組時)→ cohort → 輸入時間 → 百分位;各組獨立、數字合理。

- [ ] **Step 3: Commit**

```bash
git add web/src/components/benchmark/BenchmarkTool.tsx
git commit -m "feat(normalize): /benchmark distance/group step"
```

---

## Task 7: MCP `race_benchmark` 加 group 參數

**Files:** Modify `mcp-server/tw_cycling_data_mcp/query.py`、`server.py`;Test `mcp-server/tests/test_query.py`、`test_server.py`

**Interfaces:** `benchmark_lookup(benchmarks, race_key, seconds, result_label=None, age_band=None, gender=None)`;`race_benchmark(race_key, finish_time, result_label=None, age_band=None, gender=None)`。

- [ ] **Step 1: Write the failing query test**

在 `mcp-server/tests/test_query.py` 更新/新增 `benchmark_lookup` 測試為分組結構:

```python
def test_benchmark_lookup_group_and_cohort_fallback():
    bm = {"R": {"rn": "賽事R", "groups": {
        "130K": {"years": [2024], "cohorts": {
            "all": {"n": 100, "type": "all", "label": "全部完賽者", "bp": [60, 70, 80, 90, 100]},
            "age:40-49": {"n": 60, "type": "age", "label": "40-49 歲", "bp": [50, 60, 70, 80, 90]}}},
        "50K": {"years": [2024], "cohorts": {
            "all": {"n": 40, "type": "all", "label": "全部完賽者", "bp": [30, 40, 50, 60, 70]}}}}}}
    # explicit group + cohort
    r = query.benchmark_lookup(bm, "R", 55, result_label="130K", age_band="40-49")
    assert r["group"] == "130K" and r["cohort_label"] == "40-49 歲" and r["n"] == 60
    # no group given -> default largest (130K, all.n=100)
    r2 = query.benchmark_lookup(bm, "R", 75)
    assert r2["group"] == "130K" and r2["cohort_label"] == "全部完賽者"
    # explicit smaller group
    r3 = query.benchmark_lookup(bm, "R", 45, result_label="50K")
    assert r3["group"] == "50K" and r3["percentile_beat"] == 60
    # unknown race
    assert "error" in query.benchmark_lookup(bm, "NOPE", 75)
```

Run: `cd mcp-server && python -m pytest tests/test_query.py -k benchmark -v` → FAIL。

- [ ] **Step 2: Update `benchmark_lookup` in `query.py`**

把現有 `benchmark_lookup` 換成(挑 group → 挑 cohort;`percentile_beaten` 不變):

```python
def benchmark_lookup(benchmarks, race_key, seconds, result_label=None, age_band=None, gender=None):
    """Pick a distance/event group (given, else the largest by `all` count) then
    the most-specific available cohort (age|gender -> age -> all) within it."""
    race = benchmarks.get(race_key)
    if not race:
        return {"error": f"no benchmark for race_key '{race_key}'"}
    groups = race["groups"]
    if result_label and result_label in groups:
        group_key = result_label
    else:
        group_key = max(groups, key=lambda g: groups[g]["cohorts"].get("all", {}).get("n", 0))
    cohorts = groups[group_key]["cohorts"]
    candidates = []
    if age_band and gender:
        candidates.append(f"age:{age_band}|g:{gender}")
    if age_band:
        candidates.append(f"age:{age_band}")
    candidates.append("all")
    key = next((k for k in candidates if k in cohorts), None)
    if key is None:
        return {"error": f"no usable cohort for race '{race_key}' group '{group_key}'"}
    c = cohorts[key]
    return {"race_key": race_key, "rn": race["rn"], "group": group_key,
            "years": groups[group_key]["years"], "cohort_label": c["label"],
            "cohort_type": c["type"], "n": c["n"],
            "percentile_beat": percentile_beaten(seconds, c["bp"])}
```

Run: `cd mcp-server && python -m pytest tests/test_query.py -k benchmark -v` → PASS。

- [ ] **Step 3: Update `race_benchmark` tool + its test**

`server.py`:把 `race_benchmark_impl` 與 tool 加 `result_label`:

```python
def race_benchmark_impl(client, race_key, finish_time, result_label, age_band, gender):
    seconds = _query_module.hms_to_seconds(finish_time)
    if seconds is None:
        return {"error": f"could not parse finish_time '{finish_time}' (use HH:MM:SS / MM:SS / seconds)"}
    return _query_module.benchmark_lookup(client.benchmarks(), race_key, seconds, result_label, age_band, gender)


@mcp.tool()
def race_benchmark(race_key: str, finish_time: str, result_label: str = None,
                   age_band: str = None, gender: str = None) -> dict:
    """Percentile a finish time beats within a race's distance/event group and
    age/gender/category cohort. result_label picks the distance group (default:
    the largest); finish_time accepts HH:MM:SS / MM:SS / seconds. PDPA: aggregate only."""
    return race_benchmark_impl(_client, race_key, finish_time, result_label, age_band, gender)
```

在 `test_server.py` 把 `FakeClient.benchmarks()` 改成巢狀 groups 結構,並更新 `test_race_benchmark_impl_*` 呼叫加 `result_label`(可傳 None)並斷言回傳含 `group`。`tool_names()` 的 7-tool 斷言不變(仍是 race_benchmark)。

Run: `cd mcp-server && python -m pytest tests/ -q` → PASS。

- [ ] **Step 4: Commit**

```bash
git add mcp-server/
git commit -m "feat(normalize): MCP race_benchmark picks distance/event group"
```

---

## Task 8: manifest + API.md benchmarks 說明更新

**Files:** Modify `docs/API.md`;`scrapers/build_manifest.py`(benchmarks 端點 description);Test `scrapers/test_api_docs.py` 若有斷言結構則更新

- [ ] **Step 1: Update the benchmarks schema section in `docs/API.md`**

把 `docs/API.md` 的 `benchmarks.json` 範例/說明改為巢狀 groups 結構:

````markdown
```jsonc
{
  "<race_key>": {
    "rn": "桃園繞圈賽",
    "groups": {
      "公路繞圈賽": {
        "years": [2023, 2024],
        "cohorts": {
          "all":           { "n": 129, "type": "all", "label": "全部完賽者",  "bp": [t0, …, t100] },
          "age:40-49":     { "n": 40,  "type": "age", "label": "40-49 歲",    "bp": [...] }
        }
      },
      "個人計時賽": { "years": [...], "cohorts": { "all": { ... } } }
    }
  }
}
```
````
並在說明加一句:`groups` 依 `result_label`(距離/項目)分層——同一賽事的不同距離/項目**不混比**;cohort(all/age/cat)在**各群組內**計算。

- [ ] **Step 2: Update the manifest endpoint description**

`scrapers/build_manifest.py` 的 benchmarks 端點 `description` 改為含群組:
`"Per-race finish-time percentile breakpoints, grouped by distance/event (result_label) then age/gender/category cohort."`

- [ ] **Step 3: Run + regenerate + commit**

Run:
```bash
python -m pytest scrapers/test_api_docs.py -q
python scrapers/build_manifest.py
python -m pytest scrapers/ -q
```
Expected: 綠。

```bash
git add docs/API.md scrapers/build_manifest.py web/public/data/v1/manifest.json
git commit -m "docs(normalize): benchmarks grouped-by-distance schema in API.md + manifest"
```

---

## 重建(controller 執行,合併前)

> Task 1–8 review 通過後,controller 重跑完整 build 並 commit 重生資料(部分 Task 已各自重生;此步確保一致):

- [ ] `python scrapers/build_viz.py && python scrapers/build_benchmarks.py && python scrapers/build_manifest.py`
- [ ] `npm --prefix web run build`(astro build)
- [ ] `git add web/public/data/v1 && git commit -m "chore(data): rebuild web/v1 with group-normalized crossyear + benchmarks"`(若已被前面 Task commit 涵蓋則略)
- [ ] 抽查:桃園繞圈賽 /race 各組 winner/median 合理、/benchmark 各組獨立。**不動 dataset、不重發 release。**

---

## Self-Review

**1. Spec coverage:** 比較單位 (race_key,result_label) → crossyear(Task 1)+ benchmarks(Task 2)✅;群組缺值=全部 → 兩後端 `or "全部"` ✅;前端型別 group 維度 → Task 3 ✅;/race 組別選 → Task 4 ✅;/trends 組別選 → Task 5 ✅;/benchmark 組別步驟 → Task 6 ✅;MCP group 參數(向後相容)→ Task 7 ✅;API.md/manifest 說明 → Task 8 ✅;不重發 release → 無 dataset 改動 ✅;/race 排行榜不動 → 未碰 ✅。

**2. Placeholder scan:** 無 TBD;後端/型別/helpers/MCP 給完整程式;三個 UI 消費端給精確接補指示 + 關鍵程式(實作者讀現檔接上,非佔位)。

**3. Type consistency:** `CrossYearMap`(Task 3)= race→group→`CrossYearPoint[]`,被 CrossYearTrend(Task 4)/TrendsApp(Task 5)一致取用;`BenchmarkRace.groups[g].cohorts`(Task 3)被 benchmark.ts helpers(Task 3)、BenchmarkTool(Task 6)、MCP benchmark_lookup(Task 7,巢狀 groups)一致;後端輸出鍵(crossyear `{rk:{group:[...]}}`、benchmarks `{rk:{rn,groups:{g:{years,cohorts}}}}`)與前端/MCP 型別一致。

---

## 執行順序
Task 1、2(後端,可並序)→ Task 3(型別/helpers,前端依賴)→ Task 4、5、6(三個 UI 消費端)→ Task 7(MCP)→ Task 8(文件)→ controller 重建。
