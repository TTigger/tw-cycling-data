# 分析層分組化(難度係數 + DNA 兩軸)實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 難度係數改 (race_key, result_label) 組內計算(修跨年校正與嚴苛度的混組污染);DNA 的 `sel` 改組內 CoV 加權、`women` 加 known-gender 覆蓋門檻。

**Architecture:** `build_difficulty.race_difficulty()` 改輸出巢狀 groups(每組自己 baseline/coeff);`difficulty.ts` 改嚴格查組(`h.label ?? "全部"`,未覆蓋跳過)+ 新 `dominantGroup`;嚴苛度讀最大組並回傳 `group`。`build_race_dna.raw_axes()` 內 `sel`/`women` 兩處公式改;缺值沿用既有「正規化中性 50」慣例(climb 先例)。前端兩元件補說明字。

**Tech Stack:** Python + pytest;Astro/React + vitest;ECharts 不動。

## Global Constraints

- **難度形狀**:`{rk: {name, groups: {group_label: {baseline, years: {y: {median, coeff, n}}}}}}`;`group_label` = `result_label` 或 `全部`;**每組每年 ≥20 timed**(MIN_FINISHERS)、**每組 ≥2 年**;race 保留須 ≥1 組;`name` 在頂層。
- **校正嚴格**:`calibratedSeries` 以 `h.label ?? "全部"` 查 `diff.groups[g]?.years[String(h.y)]`;查無 → 跳過該年;**不做跨組 fallback**。同年多筆仍取最快。
- **嚴苛度**:`dominantGroup(diff)` = 跨年 Σn 最大的組鍵;`raceSeverity`/`raceSeverityAll` 讀該組 years;回傳物件加 `group: string`。verdict 門檻(-20%/+5%)不變。
- **DNA `sel`** = 各組(組內 timed n ≥10)CoV 的 n 加權平均;無合格組 → None(→ 正規化中性 50)。
- **DNA `women`**:known(M/F)/總完賽 < 0.30 → None(→ 中性 50);≥0.30 沿用 F/known×100。其他軸不動。
- 重算後**量測回報**:可校正賽事數 vs 原 31、coeff 年間擺動 >1.5×/>2× 場數 vs 原 8/4。
- 不動 dataset/master、benchmarks/crossyear、騎乘分身、`RaceDna.tsx`;manifest/API.md 無此二端點,無文件更新。
- pytest + vitest + build 全綠。

## 執行順序
Task 1(build_difficulty)→ Task 2(build_race_dna)→ Task 3(difficulty.ts + types + vitest)→ Task 4(元件註記 + 重建 + 量測)→ controller 收尾。

---

## Task 1: `build_difficulty` 分組

**Files:** Modify `scrapers/build_difficulty.py`;Test `scrapers/test_build_difficulty.py`

**Interfaces:** Produces `race_difficulty(records, min_finishers=20) -> {rk: {name, groups: {g: {baseline, years: {y: {median, coeff, n}}}}}}`。

- [ ] **Step 1: 寫失敗測試(更新/追加到 test_build_difficulty.py;既有 flat 斷言改巢狀)**

```python
def _row(rk, y, sec, label):
    return {"race_key": rk, "year": y, "finish_seconds": sec, "result_label": label,
            "race_name_canonical": rk}


def test_race_difficulty_groups_by_result_label():
    rows = []
    # group 50K: 2023 median 3600, 2024 median 3960 (coeff 1.1 vs baseline 3780)
    rows += [_row("R", 2023, 3600 + i, "50K") for i in range(-10, 10)]
    rows += [_row("R", 2024, 3960 + i, "50K") for i in range(-10, 10)]
    # group 130K: slower times, own baseline — must NOT blend with 50K
    rows += [_row("R", 2023, 18000 + i, "130K") for i in range(-10, 10)]
    rows += [_row("R", 2024, 18000 + i, "130K") for i in range(-10, 10)]
    d = BD.race_difficulty(rows, min_finishers=20)
    g50 = d["R"]["groups"]["50K"]
    assert g50["baseline"] == 3780
    assert g50["years"]["2023"]["coeff"] == round(3600 / 3780, 4)
    assert d["R"]["groups"]["130K"]["years"]["2023"]["coeff"] == 1.0
    assert d["R"]["name"] == "R"


def test_race_difficulty_drops_thin_group_year_and_single_year_group():
    rows = [_row("R", 2023, 3600 + i, "A") for i in range(-10, 10)]      # A: only 1 valid year
    rows += [_row("R", 2024, 3700, "A")] * 5                              # 2024 <20 -> dropped
    rows += [_row("R", 2023, 900 + i, None) for i in range(-10, 10)]     # 全部: 2 years ok
    rows += [_row("R", 2024, 950 + i, None) for i in range(-10, 10)]
    d = BD.race_difficulty(rows, min_finishers=20)
    assert set(d["R"]["groups"]) == {"全部"}


def test_race_difficulty_drops_race_with_no_qualifying_group():
    rows = [_row("S", 2023, 3600 + i, "A") for i in range(-10, 10)]
    assert "S" not in BD.race_difficulty(rows, min_finishers=20)
```
(檔內既有測試若用 flat `d[rk]["years"]` 斷言,改為 `d[rk]["groups"]["全部"]["years"]` 等對應。)

Run: `python -m pytest scrapers/test_build_difficulty.py -v` → FAIL。

- [ ] **Step 2: 改寫 `race_difficulty`(整個函式替換;docstring 一併更新)**

```python
def race_difficulty(records, min_finishers=MIN_FINISHERS):
    """{race_key: {name, groups: {group_label: {baseline, years}}}} — coefficients
    are computed WITHIN each (race_key, result_label) group so year-to-year
    group-mix shifts (e.g. more 130K finishers one year) never read as
    difficulty changes. group_label falls back to 全部 for unlabeled rows.
    A group needs >=2 years each with >=min_finishers timed finishers."""
    by_rgy = defaultdict(list)   # (race_key, group, year) -> [finish_seconds]
    names = {}
    for r in records:
        sec = r.get("finish_seconds")
        rk, y = r.get("race_key"), r.get("year")
        if not rk or not y or not sec or sec <= 0:
            continue
        g = r.get("result_label") or "全部"
        by_rgy[(rk, g, y)].append(sec)
        names.setdefault(rk, r.get("race_name_canonical") or r.get("race_name_raw"))

    year_med = defaultdict(lambda: defaultdict(dict))  # rk -> g -> {y: (median, n)}
    for (rk, g, y), secs in by_rgy.items():
        if len(secs) >= min_finishers:
            year_med[rk][g][y] = (statistics.median(secs), len(secs))

    out = {}
    for rk, groups in year_med.items():
        gout = {}
        for g, ym in groups.items():
            if len(ym) < 2:
                continue
            baseline = statistics.median([m for m, _ in ym.values()])
            if baseline <= 0:
                continue
            gout[g] = {"baseline": round(baseline), "years": {
                str(y): {"median": round(m), "coeff": round(m / baseline, 4), "n": n}
                for y, (m, n) in sorted(ym.items())}}
        if gout:
            out[rk] = {"name": names.get(rk), "groups": gout}
    return out
```
`main()` 的統計 print 改遍歷 groups:`total_years = sum(len(g["years"]) for d in diff.values() for g in d["groups"].values())`。模組 docstring 的「Tradeoffs」段改述分組理由(移除「ALL timed finishers」句)。

- [ ] **Step 3: 跑測試 + commit**

Run: `python -m pytest scrapers/test_build_difficulty.py -q`(PASS)→ `python -m pytest scrapers/ -q`(全綠)。
```bash
git add scrapers/build_difficulty.py scrapers/test_build_difficulty.py
git commit -m "feat(analytics): difficulty coefficients computed per (race_key, result_label) group"
```

---

## Task 2: `build_race_dna` 的 sel/women 修

**Files:** Modify `scrapers/build_race_dna.py`;Test `scrapers/test_build_race_dna.py`

**Interfaces:** `raw_axes` 簽名不變;`sel`/`women` 語意改(見 Global Constraints)。新模組常數 `SEL_GROUP_MIN = 10`、`GENDER_KNOWN_MIN = 0.30`。

- [ ] **Step 1: 寫失敗測試(追加)**

```python
def test_sel_is_group_weighted_cov_not_blended():
    # two tight groups with very different scales: blended CoV would be huge,
    # weighted per-group CoV stays small
    rows = ([_rec("R", 2024, 3600 + i, label="50K") for i in range(-10, 10)]
            + [_rec("R", 2024, 18000 + i, label="130K") for i in range(-10, 10)])
    gks = ["g%d" % i for i in range(len(rows))]
    raw = RD.raw_axes(rows, gks, min_finishers=20)
    sel = raw[("R", 2024)]["sel"]
    import statistics
    blended = statistics.pstdev([r["finish_seconds"] for r in rows]) / statistics.mean(
        [r["finish_seconds"] for r in rows])
    assert sel is not None and sel < blended / 10   # grouped CoV ~0.16%, blended ~67%


def test_sel_none_when_no_group_reaches_min():
    rows = [_rec("R", 2024, 3600 + i, label=("A" if i % 3 == 0 else "B" if i % 3 == 1 else "C"))
            for i in range(21)]  # 21 finishers split 7/7/7 — no group >=10
    gks = ["g%d" % i for i in range(len(rows))]
    raw = RD.raw_axes(rows, gks, min_finishers=20)
    assert raw[("R", 2024)]["sel"] is None


def test_women_none_below_known_gender_coverage():
    rows = [_rec("R", 2024, 3600 + i) for i in range(20)]
    for i in range(5):                      # 25% known (<30%) -> None
        rows[i]["gender"] = "F" if i < 2 else "M"
    gks = ["g%d" % i for i in range(len(rows))]
    raw = RD.raw_axes(rows, gks, min_finishers=20)
    assert raw[("R", 2024)]["women"] is None
    for i in range(5, 7):                   # now 35% known -> computed
        rows[i]["gender"] = "M"
    raw = RD.raw_axes(rows, gks, min_finishers=20)
    assert raw[("R", 2024)]["women"] == round(2 / 7 * 100, 10) or abs(raw[("R", 2024)]["women"] - 2/7*100) < 1e-6
```
(`_rec` 沿用該測試檔既有的 record fixture helper;若其無 `label`/`gender` 參數,擴充該 helper。既有 sel/women 斷言若與新語意衝突,依新語意更新。)

Run: `python -m pytest scrapers/test_build_race_dna.py -v` → FAIL。

- [ ] **Step 2: 改 `raw_axes` 內兩處(其他軸與結構不動)**

模組常數區(`MIN_FINISHERS` 旁)加:
```python
SEL_GROUP_MIN = 10        # a distance/event group needs this many timed rows for its CoV
GENDER_KNOWN_MIN = 0.30   # women axis needs known-gender coverage of at least this share
```
迴圈內(`secs = [...]` 之後)把 `sel` 與 `women` 的計算改為:
```python
        # selectivity: n-weighted mean of WITHIN-group CoV, so mixed-distance
        # races do not read as selective merely for mixing 50K with 130K
        group_secs = defaultdict(list)
        for r, _ in items:
            s = r.get("finish_seconds")
            if s and s > 0:
                group_secs[r.get("result_label") or "全部"].append(s)
        covs = []
        for v in group_secs.values():
            if len(v) >= SEL_GROUP_MIN:
                c = _cov(v)
                if c is not None:
                    covs.append((c, len(v)))
        sel = (sum(c * w for c, w in covs) / sum(w for _, w in covs)) if covs else None
```
以及 `out[(rk, y)]` 前:
```python
        # women share only when enough of the field carries a gender at all —
        # below that the axis reads source coverage, not participation
        women = (sum(1 for g in genders if g == "F") / len(genders) * 100
                 if genders and len(genders) / n >= GENDER_KNOWN_MIN else None)
```
`out` dict 內 `"sel": _cov(secs)` → `"sel": sel`;`"women": ...` 原式 → `"women": women`。(缺值 → 既有 `build_race_dna` 正規化的中性 50 慣例,climb 先例;不改該機制。)

- [ ] **Step 3: 跑測試 + commit**

Run: `python -m pytest scrapers/test_build_race_dna.py -q`(PASS)→ `python -m pytest scrapers/ -q`(全綠)。
```bash
git add scrapers/build_race_dna.py scrapers/test_build_race_dna.py
git commit -m "feat(analytics): DNA sel = within-group weighted CoV; women axis gated on gender coverage"
```

---

## Task 3: `difficulty.ts` 分組查表 + types + vitest

**Files:** Modify `web/src/lib/types.ts`、`web/src/lib/difficulty.ts`;Test `web/src/lib/difficulty.test.ts`

**Interfaces:** Produces
```ts
export interface DifficultyGroup { baseline: number; years: Record<string, YearDifficulty>; }
export interface RaceDifficulty { name: string | null; groups: Record<string, DifficultyGroup>; }
export function dominantGroup(diff: RaceDifficulty | undefined): string | null;
// RaceSeverity 介面加 group: string;raceSeverity/raceSeverityAll 讀 dominant group
// calibratedSeries 以 h.label ?? "全部" 嚴格查組
```

- [ ] **Step 1: types**

`web/src/lib/types.ts` 把
```ts
export interface RaceDifficulty {
  name: string | null; baseline: number; years: Record<string, YearDifficulty>;
}
```
改為
```ts
export interface DifficultyGroup { baseline: number; years: Record<string, YearDifficulty>; }
export interface RaceDifficulty { name: string | null; groups: Record<string, DifficultyGroup>; }
```
(`YearDifficulty` 不動;`RaceDifficultyFile` 不動。)

- [ ] **Step 2: 寫失敗測試(difficulty.test.ts 既有 fixture 改巢狀 + 追加)**

```ts
import { calibratedSeries, dominantGroup, raceSeverity } from "./difficulty";
import type { RaceDifficulty, AthleteHistoryRow } from "./types";

const diff: RaceDifficulty = {
  name: "R",
  groups: {
    "50K":  { baseline: 3780, years: { "2023": { median: 3600, coeff: 0.9524, n: 30 },
                                       "2024": { median: 3960, coeff: 1.0476, n: 25 } } },
    "130K": { baseline: 18000, years: { "2023": { median: 18000, coeff: 1.0, n: 120 },
                                        "2024": { median: 18900, coeff: 1.05, n: 110 } } },
  },
};
const h = (y: number, t: number, label: string | null): AthleteHistoryRow =>
  ({ y, rk: "R", rn: "R", cat: null, g: null, ag: null, team: null,
     rank: null, t, label, d: null, field: null });

describe("group-aware difficulty", () => {
  it("calibrates against the row's own group", () => {
    const s = calibratedSeries([h(2023, 4000, "50K"), h(2024, 4000, "50K")], "R", diff);
    expect(s.map((p) => p.coeff)).toEqual([0.9524, 1.0476]);
  });
  it("strictly skips years the row's group does not cover", () => {
    const s = calibratedSeries([h(2023, 4000, "77K"), h(2024, 20000, "130K")], "R", diff);
    expect(s).toHaveLength(1);
    expect(s[0].y).toBe(2024);
  });
  it("dominantGroup = largest total n", () => {
    expect(dominantGroup(diff)).toBe("130K");   // 230 vs 55
    expect(dominantGroup(undefined)).toBeNull();
  });
  it("severity reads the dominant group and reports it", () => {
    const sev = raceSeverity(diff, 2024);
    expect(sev?.group).toBe("130K");
    expect(sev?.coeff).toBe(1.05);
    expect(sev?.n).toBe(110);
  });
});
```
(檔內既有測試的 flat fixture 改為 `groups: { "全部": {...} }` 並在 history rows 用 `label: null`,其行為等價。)

Run: `cd web && npx vitest run src/lib/difficulty.test.ts` → FAIL。

- [ ] **Step 3: 改 `difficulty.ts`**

- `calibratedSeries` 迴圈內把
  ```ts
  const yd = diff.years[String(h.y)];
  ```
  改為
  ```ts
  const g = h.label ?? "全部";
  const yd = diff.groups[g]?.years[String(h.y)];
  ```
  (docstring 補「依該筆成績所屬距離/組別查各自係數;該組未覆蓋的年跳過」。其餘同年取最快邏輯不動。)
- 新增:
  ```ts
  /** The race's largest group (by total finishers across covered years) —
   * severity reads this one series so its composition stays stable. */
  export function dominantGroup(diff: RaceDifficulty | undefined): string | null {
    if (!diff) return null;
    let best: string | null = null, bestN = -1;
    for (const [g, grp] of Object.entries(diff.groups)) {
      const n = Object.values(grp.years).reduce((a, y) => a + y.n, 0);
      if (n > bestN) { best = g; bestN = n; }
    }
    return best;
  }
  ```
- `RaceSeverity` 介面加 `group: string;`。
- `raceSeverity`:開頭改
  ```ts
  if (!diff || year == null) return null;
  const gk = dominantGroup(diff);
  const grp = gk ? diff.groups[gk] : undefined;
  const yd = grp?.years[String(year)];
  if (!gk || !grp || !yd) return null;
  ```
  其後 `diff.years` 全改 `grp.years`;回傳物件加 `group: gk`。
- `raceSeverityAll`:`Object.keys(diff.years)` 改為
  ```ts
  const gk = dominantGroup(diff);
  const grp = gk ? diff.groups[gk] : undefined;
  if (!grp) return [];
  return Object.keys(grp.years). ...
  ```
- `calibratableRaces` 不改碼(吃 `calibratedSeries` 自動變嚴格)。

- [ ] **Step 4: 跑測試 + commit**

Run: `cd web && npx vitest run src/lib/difficulty.test.ts`(PASS,含既有改巢狀者)。
```bash
git add web/src/lib/types.ts web/src/lib/difficulty.ts web/src/lib/difficulty.test.ts
git commit -m "feat(analytics): group-aware calibration lookup + dominant-group severity"
```

---

## Task 4: 元件註記 + 重建 + 量測回報

**Files:** Modify `web/src/components/athletes/CalibratedProgress.tsx`、`web/src/components/race/RaceSeverity.tsx`;Regenerate `web/public/data/v1/race_difficulty.json`、`race_dna.json`

- [ ] **Step 1: CalibratedProgress 說明字**

該卡的說明 `<p className="mb-2 text-xs text-muted">`(line ~68)句尾補:`依你所屬距離/組別各自校正;該組未覆蓋的年份不顯示。`(讀現檔接在既有說明後,不動其他。)

- [ ] **Step 2: RaceSeverity 標明所依組**

verdict 徽章那行(`<span className={...VERDICT_STYLE...}>{sev.verdict}</span>`)之後加:
```tsx
{sev.group !== "全部" && (
  <span className="ml-2 text-xs text-muted">(以「{sev.group}」組為準)</span>
)}
```

- [ ] **Step 3: 重建 + 量測**

Run:
```bash
python scrapers/build_difficulty.py
python scrapers/build_race_dna.py
python - <<'PY'
import json
rd = json.load(open("web/public/data/v1/race_difficulty.json", encoding="utf-8"))
races = len(rd)
swings = []
for k, v in rd.items():
    for g, grp in v["groups"].items():
        cs = [y["coeff"] for y in grp["years"].values()]
        if len(cs) >= 2:
            swings.append(max(cs) / min(cs))
print(f"calibratable races={races} (was 31); group-series={len(swings)}; "
      f"swing>1.5x={sum(1 for s in swings if s > 1.5)} (was 8); "
      f">2x={sum(1 for s in swings if s > 2)} (was 4)")
PY
```
把輸出記入報告(spec 的量測回報義務)。若 races < 15,不自行調門檻——回報數字由 controller 呈給 owner 決定。

- [ ] **Step 4: build + 瀏覽器抽查**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。
瀏覽器深/淺各一輪:
- /athletes 多距離常客選手:校正卡曲線合理、說明字含「依你所屬距離/組別」。
- /race 混距離賽事:嚴苛度徽章 +(非「全部」時)「以 X 組為準」小字;DNA 雷達仍 6 軸(sel 對混距賽事應下降、低性別覆蓋賽事 women 讀中性)。

- [ ] **Step 5: Commit**

```bash
git add web/src/components/athletes/CalibratedProgress.tsx web/src/components/race/RaceSeverity.tsx web/public/data/v1/race_difficulty.json web/public/data/v1/race_dna.json
git commit -m "feat(analytics): group-aware calibration/severity UI notes + rebuilt difficulty/DNA data"
```

---

## Controller 收尾(合併前)

- [ ] `python -m pytest scrapers/ -q` + `cd web && npx vitest run` + `npm --prefix web run build`(全綠)。
- [ ] 量測數字(Task 4 Step 3)呈報 owner:可校正場數與大擺動變化;分組後仍 >1.5× 的組列出(候選「真難度事件」)。
- [ ] `grep -n "ALL timed finishers" scrapers/build_difficulty.py`(應空——舊 tradeoff 註解已改)。

## Self-Review

**1. Spec coverage:** 巢狀 groups + 門檻 → T1 ✅;嚴格查組(label ?? 全部、跳過、不 fallback)→ T3 ✅;dominantGroup + severity 讀最大組 + 回傳 group → T3 ✅;UI 標組/說明字 → T4 ✅;sel n 加權組內 CoV(SEL_GROUP_MIN=10)→ T2 ✅;women 覆蓋門檻 0.30 → T2 ✅;缺值=中性 50 既有慣例(對齊 spec 意圖)→ T2 註明 ✅;量測回報(31/8/4 對照)→ T4+收尾 ✅;manifest/API.md 無此端點免更新 → Global Constraints ✅;不動 dataset/分身/RaceDna.tsx ✅。

**2. Placeholder scan:** 無 TBD;兩個後端函式、difficulty.ts 三處、量測腳本、元件兩處皆給碼;test fixture helper 擴充有指示。

**3. Type consistency:** `RaceDifficulty {name, groups: Record<string, DifficultyGroup>}`(T3)= T1 輸出形狀;`dominantGroup(diff): string | null` 被 raceSeverity/raceSeverityAll 用;`RaceSeverity.group: string` 被 RaceSeverity.tsx(T4)讀;`h.label`(AthleteHistoryRow 既有欄)為查組鍵;`YearDifficulty {median,coeff,n}` 沿用。
