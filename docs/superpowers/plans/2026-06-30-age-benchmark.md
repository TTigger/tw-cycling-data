# 分齡/性別對標工具 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增「對標工具」——選賽事 + 分齡/性別 cohort + 輸入完賽時間 → 回該 cohort 百分位;含預運算 `benchmarks.json`、新頁 `/benchmark`,並整合公開 API(manifest + API.md)與 MCP server(新 tool `race_benchmark`)。

**Architecture:** 後端 `build_benchmarks.py` 讀 `master.public.json`,每個 race_key(跨年彙整)各 cohort 算 101 個完賽時間百分位斷點 → `web/public/data/v1/benchmarks.json`。前端新頁載入該檔,互動查詢;百分位查詢重用既有 `format.percentileBeaten`。MCP 加 client/query/server 三層 tool。

**Tech Stack:** Python 3(scrapers + MCP)、Astro + React + TypeScript + vitest(前端)、pytest。

## Global Constraints

- **Cohort 混合**:分齡(`age_band`)優先,否則賽事分組(`category_raw`);UI/回應誠實標示 cohort `type`(all/age/cat)與樣本數 `n`。
- **門檻**:每 cohort 僅在 `n >= 20`(`MIN_COHORT_N`)收錄;race_key 僅在其 `all` cohort 達標時收錄。
- **斷點**:每 cohort 固定 **101** 個完賽秒數斷點 `bp`(各百分位時間,升冪);檔案有界。
- **彙整單位**:同一 `race_key` 跨所有年份;**不跨 series**。
- **百分位定義**:`percentile_beaten` = 嚴格比你慢的比例(tie 不算贏過),時間越快贏過越多。前端**重用** `web/src/lib/format.ts` 的 `percentileBeaten` 與 `hmsToSeconds`;MCP(Python)各自實作對等純函式(語言邊界)。
- **finisher**:`r.get("status") in (None, "FIN")`(沿用 build_viz 語意;多數來源無 status 欄)。
- **PDPA**:純聚合完賽時間 + cohort 標籤;不暴露任何個資(連 name_masked 都不需要)。
- 既有測試流程:`python -m pytest scrapers/ mcp-server/` 全綠、`vitest` 綠、astro build 成功、瀏覽器抽查;每 task 自己 commit。

## 已確認的資料事實(實測 2026-06-30)

- `master.public.json` 每筆含:`race_key`、`year`、`age_band`、`age_group`、`gender`、`category_raw`、`result_label`、`finish_seconds`、`race_name_canonical`、`race_name_raw`、`status`(多數來源無此鍵,`.get` 回 None)。
- `age_band` 乾淨 10 年分齡,值域 `{"40-49","30-39","50-59","19-29","U19","60+","MASTER"}`,母體 53,545 筆(~36%)。`gender` ∈ {"M","F",None}。
- 用 **`age_band`** 當分齡 cohort(對齊 AgeBoxplot;`MASTER`(15 筆)會被 n<20 自動濾掉)。

---

## File Structure

**新增(後端):** `scrapers/benchmarks.py`、`scrapers/build_benchmarks.py`、`scrapers/test_benchmarks.py`
**修改(後端整合):** `scrapers/build_manifest.py`(ENDPOINTS 加 benchmarks)、`scrapers/test_build_manifest.py`、`docs/API.md`
**新增(前端):** `web/src/lib/benchmark.ts`、`web/src/lib/benchmark.test.ts`、`web/src/components/benchmark/BenchmarkTool.tsx`、`web/src/pages/benchmark.astro`
**修改(前端):** `web/src/lib/data-load.ts`(`loadBenchmarks`)、`web/src/lib/types.ts`(benchmark 型別)、`web/src/layouts/Base.astro`(導覽連結)
**新增/修改(MCP):** `mcp-server/tw_cycling_data_mcp/query.py`(`hms_to_seconds`/`percentile_beaten`/`benchmark_lookup`)、`client.py`(`benchmarks()`)、`server.py`(`race_benchmark` tool)、`mcp-server/tests/`

---

## Task 1: 後端 benchmarks 資料產生

純函式 + 產生器,輸出 `benchmarks.json`。交付物:`build_benchmarks.py` 寫出檔案,純函式測試通過。

**Files:**
- Create: `scrapers/benchmarks.py`
- Create: `scrapers/build_benchmarks.py`
- Test: `scrapers/test_benchmarks.py`

**Interfaces:**
- Consumes: `common.iter_records`、`common.PUBLIC_DATA_DIR`。
- Produces:
  - `cohort_keys(row) -> list[tuple[str,str,str]]`(回 `(key, type, label)`)
  - `percentile_breakpoints(sorted_seconds: list[int]) -> list[int]`(長度 101)
  - `build_index(rows, min_n=20) -> dict`
  - `MIN_COHORT_N = 20`

- [ ] **Step 1: Write the failing test**

`scrapers/test_benchmarks.py`:

```python
import benchmarks as B


def test_percentile_breakpoints_length_and_monotonic():
    bp = B.percentile_breakpoints(list(range(1, 101)))  # 100 values 1..100
    assert len(bp) == 101
    assert bp == sorted(bp)                # monotonic non-decreasing
    assert bp[0] == 1 and bp[100] == 100   # fastest / slowest
    # single-value cohort -> all breakpoints equal
    assert B.percentile_breakpoints([42]) == [42] * 101


def test_cohort_keys_age_gender_cat_and_missing():
    row = {"age_band": "40-49", "gender": "M", "category_raw": "M / M40"}
    keys = {k for (k, _t, _l) in B.cohort_keys(row)}
    assert keys == {"all", "age:40-49", "age:40-49|g:M", "cat:M / M40"}
    # missing age/gender -> only all + cat
    row2 = {"age_band": None, "gender": None, "category_raw": "菁英組"}
    keys2 = {k for (k, _t, _l) in B.cohort_keys(row2)}
    assert keys2 == {"all", "cat:菁英組"}
    # types tagged correctly
    types = {k: t for (k, t, _l) in B.cohort_keys(row)}
    assert types["all"] == "all" and types["age:40-49"] == "age" and types["cat:M / M40"] == "cat"


def test_build_index_filters_small_cohorts_and_shapes_output():
    rows = []
    # 25 M 40-49 finishers of race R (seconds 3600..)
    for i in range(25):
        rows.append({"race_key": "R", "year": 2024, "age_band": "40-49", "gender": "M",
                     "category_raw": "M40", "finish_seconds": 3600 + i,
                     "race_name_canonical": "賽事R", "status": None})
    # 5 F finishers -> age:40-49|g:F has n=5 -> dropped; but they still count toward all + age:40-49
    for i in range(5):
        rows.append({"race_key": "R", "year": 2025, "age_band": "40-49", "gender": "F",
                     "category_raw": "F40", "finish_seconds": 4000 + i,
                     "race_name_canonical": "賽事R", "status": None})
    idx = B.build_index(rows, min_n=20)
    assert "R" in idx
    cohorts = idx["R"]["cohorts"]
    assert "all" in cohorts and cohorts["all"]["n"] == 30
    assert "age:40-49" in cohorts and cohorts["age:40-49"]["n"] == 30
    assert "age:40-49|g:M" in cohorts and cohorts["age:40-49|g:M"]["n"] == 25
    assert "age:40-49|g:F" not in cohorts        # n=5 < 20 dropped
    assert len(cohorts["all"]["bp"]) == 101
    assert idx["R"]["years"] == [2024, 2025]
    assert idx["R"]["rn"] == "賽事R"


def test_build_index_drops_race_without_enough_finishers():
    rows = [{"race_key": "TINY", "year": 2024, "age_band": None, "gender": None,
             "category_raw": None, "finish_seconds": 3600, "race_name_canonical": "小賽",
             "status": None}]
    assert "TINY" not in B.build_index(rows, min_n=20)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_benchmarks.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'benchmarks'`)

- [ ] **Step 3: Implement `benchmarks.py`**

```python
# -*- coding: utf-8 -*-
"""Pure helpers for the age/gender benchmark dataset. No I/O — unit-testable.
A cohort is `all`, an age band, an age band x gender, or a race category.
Each cohort stores 101 finish-second breakpoints (the time at each percentile)."""

MIN_COHORT_N = 20


def _age_label(ab):
    return ab if ab.startswith("U") else f"{ab} 歲"


def cohort_keys(row):
    """Return [(key, type, label)] for the cohorts this finisher belongs to."""
    out = [("all", "all", "全部完賽者")]
    ab = row.get("age_band")
    if ab:
        out.append((f"age:{ab}", "age", _age_label(ab)))
        g = row.get("gender")
        if g in ("M", "F"):
            out.append((f"age:{ab}|g:{g}", "age",
                        f"{_age_label(ab)} {'男' if g == 'M' else '女'}"))
    cat = row.get("category_raw")
    if cat:
        out.append((f"cat:{cat}", "cat", cat))
    return out


def percentile_breakpoints(sorted_seconds):
    """101 breakpoints: bp[p] = time at percentile p (0=fastest..100=slowest).
    Input must be ascending. Length always 101; monotonic non-decreasing."""
    n = len(sorted_seconds)
    if n == 0:
        return []
    return [sorted_seconds[int(round(p / 100 * (n - 1)))] for p in range(101)]


def _is_finisher(row):
    return row.get("status") in (None, "FIN")


def build_index(rows, min_n=MIN_COHORT_N):
    """Group finishers by race_key, accumulate per-cohort finish seconds, then
    emit only cohorts with n>=min_n. A race_key is kept only if its `all`
    cohort reaches min_n."""
    races = {}
    for r in rows:
        rk = r.get("race_key")
        fs = r.get("finish_seconds")
        if not rk or fs is None or not _is_finisher(r):
            continue
        try:
            fs = int(fs)
        except (TypeError, ValueError):
            continue
        race = races.setdefault(rk, {
            "rn": r.get("race_name_canonical") or r.get("race_name_raw") or rk,
            "years": set(), "cohorts": {}})
        if r.get("year") is not None:
            race["years"].add(r["year"])
        for key, ctype, label in cohort_keys(r):
            c = race["cohorts"].setdefault(key, {"type": ctype, "label": label, "_secs": []})
            c["_secs"].append(fs)

    out = {}
    for rk, race in races.items():
        cohorts = {}
        for key, c in race["cohorts"].items():
            if len(c["_secs"]) < min_n:
                continue
            secs = sorted(c["_secs"])
            cohorts[key] = {"n": len(secs), "type": c["type"], "label": c["label"],
                            "bp": percentile_breakpoints(secs)}
        if "all" not in cohorts:        # race itself too small
            continue
        out[rk] = {"rn": race["rn"], "years": sorted(race["years"]), "cohorts": cohorts}
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_benchmarks.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Implement `build_benchmarks.py`**

```python
# -*- coding: utf-8 -*-
"""Build /data/v1/benchmarks.json: per-race finish-time percentile breakpoints
by age/gender/category cohort. Reads master.public.json (only). Run before
build_manifest.py so the manifest's endpoint count/stats see it."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common      # noqa: E402
import benchmarks  # noqa: E402

IN = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "master.public.json")
OUT = os.path.join(common.PUBLIC_DATA_DIR, "benchmarks.json")


def main():
    idx = benchmarks.build_index(common.iter_records(IN))
    os.makedirs(common.PUBLIC_DATA_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, separators=(",", ":"))
    races = len(idx)
    cohorts = sum(len(r["cohorts"]) for r in idx.values())
    print(f"benchmarks: races={races} cohorts={cohorts} -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Generate the real file and sanity-check**

Run:
```bash
python scrapers/build_benchmarks.py
python -c "import json;d=json.load(open('web/public/data/v1/benchmarks.json',encoding='utf-8'));k=next(iter(d));print('races',len(d));print('sample',k,d[k]['rn'],d[k]['years'],list(d[k]['cohorts'])[:4]);import os;print('KB',os.path.getsize('web/public/data/v1/benchmarks.json')//1024)"
```
Expected: races 在數十~上百量級;某賽事有 `all` + 若干 `age:*`/`cat:*` cohort;檔案大小數百 KB 內(若 >1.5MB,於 report 記錄,後續可調 MIN_COHORT_N)。

- [ ] **Step 7: Commit**

```bash
git add scrapers/benchmarks.py scrapers/build_benchmarks.py scrapers/test_benchmarks.py web/public/data/v1/benchmarks.json
git commit -m "feat(benchmark): per-race age/gender finish-time percentile breakpoints (benchmarks.json)"
```

---

## Task 2: manifest + API.md 整合

把 benchmarks.json 納入公開 API 契約。交付物:manifest ENDPOINTS 含 benchmarks,API.md 有對應段落,測試更新。

**Files:**
- Modify: `scrapers/build_manifest.py`(ENDPOINTS)
- Modify: `scrapers/test_build_manifest.py`
- Modify: `docs/API.md`

**Interfaces:**
- Consumes: `build_manifest.ENDPOINTS`(Task from Feature 1)。

- [ ] **Step 1: Add the endpoint + update the manifest test (RED)**

在 `scrapers/test_build_manifest.py` 的端點斷言區(已有 `assert "race/{race_key}.json" in paths` 等)新增:

```python
    assert "benchmarks.json" in paths
```

Run: `python -m pytest scrapers/test_build_manifest.py -v`
Expected: FAIL（`benchmarks.json` 尚未加入 ENDPOINTS）

- [ ] **Step 2: Add benchmarks to `build_manifest.ENDPOINTS`**

在 `scrapers/build_manifest.py` 的 `ENDPOINTS` list 內(放在 `series.json` 之後)新增一筆:

```python
    {"path": "benchmarks.json", "kind": "index", "description": "Per-race finish-time percentile breakpoints by age/gender/category cohort."},
```

- [ ] **Step 3: Run the manifest test (GREEN)**

Run: `python -m pytest scrapers/test_build_manifest.py -v`
Expected: PASS

- [ ] **Step 4: Document the endpoint in `docs/API.md`**

在端點表(`series.json` 那列之後)加一列:

```markdown
| `benchmarks.json` | index | 各賽事(跨年)依分齡/性別/分組 cohort 的完賽時間百分位斷點 |
```

並在「主要欄位 schema」區後新增一段:

````markdown
## benchmarks.json

對標工具的資料。鍵為 `race_key`;每場跨所有年份彙整。

```jsonc
{
  "<race_key>": {
    "rn": "雙塔520",
    "years": [2022, 2023, 2024, 2025],
    "cohorts": {
      "all":           { "n": 831, "type": "all", "label": "全部完賽者",  "bp": [t0, …, t100] },
      "age:40-49":     { "n": 240, "type": "age", "label": "40-49 歲",    "bp": [...] },
      "age:40-49|g:M": { "n": 205, "type": "age", "label": "40-49 歲 男", "bp": [...] },
      "cat:男子菁英":   { "n": 88,  "type": "cat", "label": "男子菁英",     "bp": [...] }
    }
  }
}
```

- cohort key:`all` / `age:<band>` / `age:<band>|g:<M|F>` / `cat:<division>`;`type` ∈ {all, age, cat}。
- `bp` = 101 個完賽秒數斷點(各百分位時間,升冪;`bp[0]`=最快、`bp[50]`=中位、`bp[100]`=最慢)。
- 查百分位:「你贏過(比你慢的)%」= `bp` 中嚴格比你慢的比例 × 100。
- 僅收每 cohort `n>=20`、且該賽事有 `all` cohort 者。去識別化純聚合,無個資。
````

- [ ] **Step 5: Regenerate manifest end-to-end and commit**

Run:
```bash
python scrapers/build_benchmarks.py && python scrapers/build_manifest.py
python -c "import json;eps={e['path'] for e in json.load(open('web/public/data/v1/manifest.json',encoding='utf-8'))['endpoints']};print('benchmarks.json' in eps)"
```
Expected: `True`

```bash
git add scrapers/build_manifest.py scrapers/test_build_manifest.py docs/API.md web/public/data/v1/manifest.json
git commit -m "feat(api): document benchmarks.json in manifest + API.md"
```

---

## Task 3: 前端 benchmark 純函式

cohort 選擇邏輯 + 重用既有百分位。交付物:`benchmark.ts` + vitest。

**Files:**
- Create: `web/src/lib/benchmark.ts`
- Create: `web/src/lib/benchmark.test.ts`
- Modify: `web/src/lib/types.ts`(benchmark 型別)

**Interfaces:**
- Consumes: `format.percentileBeaten`、`format.hmsToSeconds`(`web/src/lib/format.ts`,已存在)。
- Produces:
  - 型別 `Cohort { n: number; type: "all"|"age"|"cat"; label: string; bp: number[] }`、`BenchmarkRace { rn: string; years: number[]; cohorts: Record<string, Cohort> }`、`BenchmarkFile = Record<string, BenchmarkRace>`。
  - `availableCohorts(race: BenchmarkRace) -> {key: string; cohort: Cohort}[]`(排序:age|gender → age → cat → all)
  - `pickDefaultCohort(race: BenchmarkRace) -> string`(回 cohort key;優先 age(無性別),否則 cat,否則 all)

- [ ] **Step 1: Add types to `web/src/lib/types.ts`**

於檔案末新增:

```ts
export interface Cohort { n: number; type: "all" | "age" | "cat"; label: string; bp: number[]; }
export interface BenchmarkRace { rn: string; years: number[]; cohorts: Record<string, Cohort>; }
export type BenchmarkFile = Record<string, BenchmarkRace>;
```

- [ ] **Step 2: Write the failing test**

`web/src/lib/benchmark.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { availableCohorts, pickDefaultCohort } from "./benchmark";
import type { BenchmarkRace } from "./types";

const race: BenchmarkRace = {
  rn: "賽事R", years: [2024, 2025],
  cohorts: {
    all: { n: 100, type: "all", label: "全部完賽者", bp: [] },
    "age:40-49": { n: 60, type: "age", label: "40-49 歲", bp: [] },
    "age:40-49|g:M": { n: 50, type: "age", label: "40-49 歲 男", bp: [] },
    "cat:菁英": { n: 30, type: "cat", label: "菁英", bp: [] },
  },
};

describe("benchmark cohort selection", () => {
  it("orders cohorts: age|gender, age, cat, all", () => {
    const keys = availableCohorts(race).map((c) => c.key);
    expect(keys).toEqual(["age:40-49|g:M", "age:40-49", "cat:菁英", "all"]);
  });
  it("defaults to a plain age cohort when present", () => {
    expect(pickDefaultCohort(race)).toBe("age:40-49");
  });
  it("falls back to cat then all", () => {
    const noAge: BenchmarkRace = { rn: "x", years: [2024],
      cohorts: { all: { n: 40, type: "all", label: "全部", bp: [] },
                 "cat:挑戰": { n: 25, type: "cat", label: "挑戰", bp: [] } } };
    expect(pickDefaultCohort(noAge)).toBe("cat:挑戰");
    const onlyAll: BenchmarkRace = { rn: "y", years: [2024],
      cohorts: { all: { n: 40, type: "all", label: "全部", bp: [] } } };
    expect(pickDefaultCohort(onlyAll)).toBe("all");
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd web && npx vitest run src/lib/benchmark.test.ts`
Expected: FAIL (cannot resolve `./benchmark`)

- [ ] **Step 4: Implement `web/src/lib/benchmark.ts`**

```ts
import type { BenchmarkRace } from "./types";

/** Cohorts a user can pick, most-specific first: age|gender, age, cat, all. */
export function availableCohorts(race: BenchmarkRace) {
  const rank = (key: string, type: string) =>
    type === "age" && key.includes("|g:") ? 0 : type === "age" ? 1 : type === "cat" ? 2 : 3;
  return Object.entries(race.cohorts)
    .map(([key, cohort]) => ({ key, cohort }))
    .sort((a, b) => rank(a.key, a.cohort.type) - rank(b.key, b.cohort.type)
      || b.cohort.n - a.cohort.n);
}

/** Default cohort key: a plain age band if present, else a category, else all. */
export function pickDefaultCohort(race: BenchmarkRace): string {
  const c = race.cohorts;
  const plainAge = Object.keys(c).find((k) => c[k].type === "age" && !k.includes("|g:"));
  if (plainAge) return plainAge;
  const cat = Object.keys(c).find((k) => c[k].type === "cat");
  if (cat) return cat;
  return "all";
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd web && npx vitest run src/lib/benchmark.test.ts`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add web/src/lib/benchmark.ts web/src/lib/benchmark.test.ts web/src/lib/types.ts
git commit -m "feat(benchmark): frontend cohort selection helpers + types"
```

---

## Task 4: 前端對標頁與元件

互動工具頁。交付物:`/benchmark` 可用,瀏覽器抽查正確。

**Files:**
- Create: `web/src/components/benchmark/BenchmarkTool.tsx`
- Create: `web/src/pages/benchmark.astro`
- Modify: `web/src/lib/data-load.ts`(`loadBenchmarks`)
- Modify: `web/src/layouts/Base.astro`(導覽連結)

**Interfaces:**
- Consumes: `loadBenchmarks()`、`availableCohorts`/`pickDefaultCohort`(Task 3)、`format.percentileBeaten`/`hmsToSeconds`/`secondsToHMS`。

- [ ] **Step 1: Add the loader to `web/src/lib/data-load.ts`**

仿照同檔既有 loader(用 `const API = `${base}/data/v1``,Feature 1 已建),在檔末新增:

```ts
export async function loadBenchmarks(): Promise<import("./types").BenchmarkFile> {
  const r = await fetch(`${API}/benchmarks.json`);
  if (!r.ok) throw new Error(`benchmarks.json ${r.status}`);
  return r.json();
}
```

- [ ] **Step 2: Implement `web/src/components/benchmark/BenchmarkTool.tsx`**

```tsx
import { useMemo, useState } from "react";
import type { BenchmarkFile } from "../../lib/types";
import { availableCohorts, pickDefaultCohort } from "../../lib/benchmark";
import { percentileBeaten, hmsToSeconds, secondsToHMS } from "../../lib/format";

export default function BenchmarkTool({ data }: { data: BenchmarkFile }) {
  // Race options sorted by latest year then size.
  const races = useMemo(
    () => Object.entries(data).sort(
      (a, b) => (b[1].years.at(-1) ?? 0) - (a[1].years.at(-1) ?? 0)
        || (b[1].cohorts.all?.n ?? 0) - (a[1].cohorts.all?.n ?? 0)),
    [data],
  );
  const [rk, setRk] = useState("");
  const [cohortKey, setCohortKey] = useState("");
  const [time, setTime] = useState("");

  const race = rk ? data[rk] : undefined;
  const cohorts = race ? availableCohorts(race) : [];
  const activeKey = cohortKey && race?.cohorts[cohortKey] ? cohortKey
    : race ? pickDefaultCohort(race) : "";
  const cohort = race?.cohorts[activeKey];
  const secs = hmsToSeconds(time);
  const beat = cohort && secs != null ? percentileBeaten(secs, cohort.bp) : null;

  const onPickRace = (v: string) => { setRk(v); setCohortKey(""); };

  return (
    <div className="space-y-4 text-sm">
      <label className="block">
        <span className="text-muted">① 選賽事</span>
        <select aria-label="選賽事" value={rk} onChange={(e) => onPickRace(e.target.value)}
          className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink">
          <option value="">選擇賽事…</option>
          {races.map(([k, r]) => (
            <option key={k} value={k}>{r.rn}（{r.years.at(0)}–{r.years.at(-1)}, {r.cohorts.all?.n ?? 0} 人）</option>
          ))}
        </select>
      </label>

      {race && (
        <label className="block">
          <span className="text-muted">② 選分組</span>
          <select aria-label="選分組" value={activeKey} onChange={(e) => setCohortKey(e.target.value)}
            className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink">
            {cohorts.map(({ key, cohort: c }) => (
              <option key={key} value={key}>
                {c.label}（{c.type === "age" ? "分齡" : c.type === "cat" ? "賽事分組" : "全部"}, {c.n} 人）
              </option>
            ))}
          </select>
        </label>
      )}

      {cohort && (
        <label className="block">
          <span className="text-muted">③ 你的完賽時間</span>
          <input value={time} onChange={(e) => setTime(e.target.value)} placeholder="HH:MM:SS"
            className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink outline-none focus:border-accent" />
        </label>
      )}

      {cohort && beat != null && (
        <div className="space-y-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-3 text-ink">
          <div>在「{cohort.label}」({cohort.n} 人),你贏過 <b className="num text-accent">{beat}%</b> 的人。</div>
          <div className="text-xs text-muted">
            最快 {secondsToHMS(cohort.bp[0])}・中位 {secondsToHMS(cohort.bp[50])}・最慢 {secondsToHMS(cohort.bp[100])}
          </div>
          {/* distribution bar: P0..P100 with your marker */}
          <div className="relative h-2 rounded bg-border">
            <div className="absolute top-0 h-2 w-0.5 bg-accent"
              style={{ left: `${Math.min(100, Math.max(0, 100 - beat))}%` }} aria-hidden />
          </div>
          {cohort.n < 50 && <div className="text-xs text-accent">樣本較少({cohort.n} 人),僅供參考。</div>}
        </div>
      )}
      {cohort && time && beat == null && <p className="text-accent">時間格式請用 HH:MM:SS 或 MM:SS。</p>}

      <p className="text-xs text-muted">
        以該賽事跨年所有完賽者的完賽時間為基準;分齡(age)用真實年齡組,賽事分組(cat)為報名組別。去識別化純聚合,僅供參考。
      </p>
    </div>
  );
}
```

- [ ] **Step 3: Implement `web/src/pages/benchmark.astro`**

```astro
---
import Base from "../layouts/Base.astro";
import BenchmarkTool from "../components/benchmark/BenchmarkTool.tsx";
import { loadBenchmarks } from "../lib/data-load";

const data = await loadBenchmarks();
---
<Base title="分齡對標 | 台灣公路車賽事成績儀表板">
  <h1 class="font-display text-3xl">分齡對標</h1>
  <p class="mt-2 mb-6 text-muted">選一場賽事、你的分齡/性別組,輸入完賽時間,看你在同組裡的位置。分齡組僅競技型賽事有,其餘以報名組別對標。</p>
  <BenchmarkTool data={data} client:only="react" />
</Base>
```

> 註:`loadBenchmarks()` 在 build 期(SSG)於 Node 端 fetch `${API}/benchmarks.json`。若本專案的島嶼頁慣例是 `client:only` 元件自行 fetch(而非頁面預載),改為元件內 `loadBenchmarks()` + loading 狀態,與 `InsightsApp` 等既有頁一致。實作時對齊既有頁的載入方式(看 `insights.astro`/`InsightsApp` 是頁面預載或元件自載),擇一即可,確保 build 與執行期都能取得資料。

- [ ] **Step 4: Add the nav link in `web/src/layouts/Base.astro`**

在導覽列(`<a href="/insights" …>洞察</a>` 之後)加入:

```astro
<a href="/benchmark" class="py-1 hover:text-accent">分齡對標</a>
```

- [ ] **Step 5: Build + browser-verify**

Run:
```bash
npm --prefix web run build
```
Expected: build 成功,`/benchmark/index.html` 產出。
瀏覽器抽查 `/benchmark`:選一場**有分齡**的競技賽 → 出現 `age:*` 分組、輸入時間得合理百分位;選一場**只有分組**的賽事 → 只出現 `cat:*`/`all`、百分位正確;格式錯誤時顯示提示。

- [ ] **Step 6: Commit**

```bash
git add web/src/components/benchmark/ web/src/pages/benchmark.astro web/src/lib/data-load.ts web/src/layouts/Base.astro
git commit -m "feat(benchmark): /benchmark interactive tool page + nav"
```

---

## Task 5: MCP `race_benchmark` tool

把對標也開成 MCP tool。交付物:MCP 8→9 tools,測試通過。

**Files:**
- Modify: `mcp-server/tw_cycling_data_mcp/query.py`(`hms_to_seconds`、`percentile_beaten`、`benchmark_lookup`)
- Modify: `mcp-server/tw_cycling_data_mcp/client.py`(`benchmarks()`)
- Modify: `mcp-server/tw_cycling_data_mcp/server.py`(`race_benchmark` tool + `_impl`)
- Test: `mcp-server/tests/test_query.py`、`mcp-server/tests/test_server.py`

**Interfaces:**
- Consumes: `ApiClient`(Feature 1)。
- Produces:
  - `query.hms_to_seconds(s) -> int|None`
  - `query.percentile_beaten(seconds, sorted_times) -> int`
  - `query.benchmark_lookup(benchmarks, race_key, seconds, age_band=None, gender=None) -> dict`
  - `client.ApiClient.benchmarks()`
  - `server.race_benchmark_impl(client, race_key, finish_time, age_band, gender)` + `@mcp.tool() race_benchmark`

- [ ] **Step 1: Write the failing query tests**

在 `mcp-server/tests/test_query.py` 末新增:

```python
def test_hms_to_seconds():
    assert query.hms_to_seconds("01:00:00") == 3600
    assert query.hms_to_seconds("10:30") == 630
    assert query.hms_to_seconds("90") == 90
    assert query.hms_to_seconds("nope") is None


def test_percentile_beaten_counts_strictly_slower():
    bp = [60, 70, 80, 90, 100]
    assert query.percentile_beaten(65, bp) == 80   # 4 of 5 slower
    assert query.percentile_beaten(60, bp) == 80   # tie not counted (4 strictly slower)
    assert query.percentile_beaten(50, bp) == 100  # faster than all
    assert query.percentile_beaten(100, bp) == 0   # slower than/equal all


def test_benchmark_lookup_picks_cohort_with_fallback():
    bm = {"R": {"rn": "賽事R", "years": [2024],
                "cohorts": {
                    "all": {"n": 100, "type": "all", "label": "全部完賽者", "bp": [60, 70, 80, 90, 100]},
                    "age:40-49": {"n": 60, "type": "age", "label": "40-49 歲", "bp": [50, 60, 70, 80, 90]},
                    "age:40-49|g:M": {"n": 50, "type": "age", "label": "40-49 歲 男", "bp": [40, 50, 60, 70, 80]},
                }}}
    # most specific available
    r = query.benchmark_lookup(bm, "R", 55, age_band="40-49", gender="M")
    assert r["cohort_label"] == "40-49 歲 男" and r["n"] == 50
    # gender absent in data -> fall back to age band
    r2 = query.benchmark_lookup(bm, "R", 55, age_band="40-49", gender="F")
    assert r2["cohort_label"] == "40-49 歲"
    # no age -> all
    r3 = query.benchmark_lookup(bm, "R", 75)
    assert r3["cohort_label"] == "全部完賽者" and "percentile_beat" in r3
    # unknown race
    assert "error" in query.benchmark_lookup(bm, "NOPE", 75)
```

Run: `cd mcp-server && python -m pytest tests/test_query.py -v`
Expected: FAIL (functions missing)

- [ ] **Step 2: Implement in `query.py`**

於 `query.py` 末新增:

```python
def hms_to_seconds(s):
    """Parse 'HH:MM:SS' / 'MM:SS' / plain seconds -> int, or None if unparseable."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        if ":" in s:
            parts = [int(p) for p in s.split(":")]
            if len(parts) == 3:
                h, m, sec = parts
            elif len(parts) == 2:
                h, m, sec = 0, parts[0], parts[1]
            else:
                return None
            return h * 3600 + m * 60 + sec
        return int(s)
    except (TypeError, ValueError):
        return None


def percentile_beaten(seconds, sorted_times):
    """Percent of the cohort strictly slower than `seconds` (ties not counted)."""
    if not sorted_times:
        return 0
    slower = sum(1 for t in sorted_times if t > seconds)
    return round(slower / len(sorted_times) * 100)


def benchmark_lookup(benchmarks, race_key, seconds, age_band=None, gender=None):
    """Pick the most-specific available cohort (age|gender -> age -> all) and
    return the percentile the given finish time beats."""
    race = benchmarks.get(race_key)
    if not race:
        return {"error": f"no benchmark for race_key '{race_key}'"}
    cohorts = race["cohorts"]
    candidates = []
    if age_band and gender:
        candidates.append(f"age:{age_band}|g:{gender}")
    if age_band:
        candidates.append(f"age:{age_band}")
    candidates.append("all")
    key = next((k for k in candidates if k in cohorts), None)
    if key is None:
        return {"error": f"no usable cohort for race '{race_key}'"}
    c = cohorts[key]
    return {
        "race_key": race_key, "rn": race["rn"], "years": race["years"],
        "cohort_label": c["label"], "cohort_type": c["type"], "n": c["n"],
        "percentile_beat": percentile_beaten(seconds, c["bp"]),
    }
```

Run: `cd mcp-server && python -m pytest tests/test_query.py -v`
Expected: PASS

- [ ] **Step 3: Add `benchmarks()` to `client.py`**

在 `ApiClient` 內(其他方法旁)新增:

```python
    def benchmarks(self):
        return self._get("benchmarks.json")
```

- [ ] **Step 4: Add the server tool (write test first)**

在 `mcp-server/tests/test_server.py` 的 `FakeClient` 加一個 `benchmarks()` 方法,並新增測試:

```python
    def benchmarks(self):
        return {"R": {"rn": "賽事R", "years": [2024], "cohorts": {
            "all": {"n": 100, "type": "all", "label": "全部完賽者", "bp": [60, 70, 80, 90, 100]}}}}


def test_race_benchmark_impl_and_registration():
    c = FakeClient()
    r = server.race_benchmark_impl(c, "R", "00:01:05", None, None)  # 65s
    assert r["percentile_beat"] == 80 and r["cohort_label"] == "全部完賽者"
```

並把既有 `test_server_registers_six_tools` 的預期集合改為包含 `race_benchmark`(7 tools);把該測試名與斷言更新為 7 個工具:

```python
    assert set(names) == {
        "dataset_overview", "search_athletes", "get_athlete",
        "list_races", "get_race", "get_team", "race_benchmark",
    }
```

Run: `cd mcp-server && python -m pytest tests/test_server.py -v`
Expected: FAIL（`race_benchmark` 未實作)

- [ ] **Step 5: Implement the tool in `server.py`**

加 `_impl` 與 tool(沿用 `_query_module` 別名;`_client` 已存在):

```python
def race_benchmark_impl(client, race_key, finish_time, age_band, gender):
    seconds = _query_module.hms_to_seconds(finish_time)
    if seconds is None:
        return {"error": f"could not parse finish_time '{finish_time}' (use HH:MM:SS / MM:SS / seconds)"}
    return _query_module.benchmark_lookup(client.benchmarks(), race_key, seconds, age_band, gender)


@mcp.tool()
def race_benchmark(race_key: str, finish_time: str, age_band: str = None, gender: str = None) -> dict:
    """Percentile a finish time beats within a race's age/gender/category cohort.
    finish_time accepts HH:MM:SS / MM:SS / seconds; age_band like '40-49'; gender 'M'/'F'.
    PDPA: aggregate only."""
    return race_benchmark_impl(_client, race_key, finish_time, age_band, gender)
```

- [ ] **Step 6: Run the MCP suite (GREEN)**

Run: `cd mcp-server && python -m pytest tests/ -v`
Expected: PASS（query + server + client;`race_benchmark` 註冊為第 7 個 tool)

- [ ] **Step 7: Commit**

```bash
git add mcp-server/
git commit -m "feat(mcp): race_benchmark tool over benchmarks.json (cohort percentile lookup)"
```

---

## Self-Review

**1. Spec coverage:** 資料模型/斷點/cohort 混合 → Task 1 ✅;n≥20 + race 需 all → Task 1 ✅;manifest+API.md → Task 2 ✅;前端 cohort 選擇 → Task 3 ✅;`/benchmark` 工具+導覽+誠實標示 → Task 4 ✅;MCP tool → Task 5 ✅;百分位定義(嚴格較慢、重用 percentileBeaten)→ Task 3/4(前端重用)+ Task 5(Python 對等)✅;PDPA 純聚合 → 全程 ✅;彙整單位 race_key 跨年 → Task 1 ✅。

**2. Placeholder scan:** 無 TBD;每個改碼步驟附完整程式。Task 4 Step 3 對「頁面預載 vs 元件自載」給了明確的對齊既有頁指示(非佔位,二擇一且都可行)。

**3. Type consistency:** `Cohort`/`BenchmarkRace`/`BenchmarkFile`(Task 3 定義)被 Task 4 沿用一致;`benchmark_lookup`/`percentile_beaten`/`hms_to_seconds` 簽名 Task 5 內一致;benchmarks.json 結構(rn/years/cohorts/{n,type,label,bp})在 Task 1 產生、Task 2 文件、Task 3 型別、Task 5 lookup 四處一致;cohort key 格式 `age:<band>|g:<G>` 在後端(Task 1)與 MCP lookup(Task 5)一致。

---

## 執行順序

Task 1 → 2 → 3 → 4 → 5。Task 1 必須先(產生 benchmarks.json 給 2/4/5);Task 3 在 4 之前(純函式先於 UI);MCP(5)可獨立於前端(3/4),但需 Task 1 的資料結構定案。
