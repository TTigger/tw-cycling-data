# /coverage 來源站名 + 連結 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/coverage` 的「已收錄的來源」改為準確的 8 來源(由 master 算),並顯示人類可讀站名 + 連結,而非僅網域。

**Architecture:** 後端 `build_overview` 在 overview.json 加 `by_source`(準確 8 來源筆數)。前端 `sources.ts` curated 站名/連結對照;CoverageApp 來源 Card 改讀 `overview.by_source` + 對照表顯示站名(連結)+ 筆數,並把頂部 KPI 數字一併改用 overview.kpi(避免與準確來源清單矛盾)。

**Tech Stack:** Python(build_viz)、Astro + React + TypeScript + vitest。

## Global Constraints

- 來源清單與筆數來自 master(`overview.by_source`,8 來源),不依賴過期的 coverage.json。
- 站名對照(已確認,逐字):`bravelog.tw`→Bravelog 運動趣;`irunner.biji.co`→iRunner(biji 運動社群);`tsu.com.tw`→運動筆記;`taiwanbike.org`→中華民國自行車協會(TBA);`twbike.org`→中華民國登山車協會;`cyclist.org.tw`→自行車騎士協會;`criterium.tw`→criterium.tw(TCU 城市繞圈賽);`cycling.org.tw`→中華民國自由車協會。
- 未知網域 fallback:站名=網域、url 空(不顯示連結)。
- 純前端 + 一個 build 欄位;不動 coverage.json 的 gaps 部分。
- 既有測試:`pytest scrapers/` + `vitest` 綠;astro build 成功。

## 已確認的現況

- `build_overview(viz)` 迴圈 `for r in viz:` 已蒐集 `sources_seen.add(r.get("plat"))`(`plat`=source_platform 網域);return 含 `kpi/heat/trend/women/composition/genderTrend/ageTrend`。`build_viz` 已 `from collections import defaultdict, Counter`。
- `CoverageApp.tsx`:`Promise.all([loadCoverage(), loadRaces()])`;來源 Card `Object.entries(s.by_source).map(([src,n]) => <span>{src} {n}</span>)`(s=cov.summary)。頂部 KPI 用 `s.rows/s.races/s.y0/s.y1/s.overseas`(coverage.json,過期)。
- `loadOverview()` 已存在(data-load.ts)。`OverviewData`(overview.ts)目前無 `by_source`。

---

## File Structure

**修改(後端):** `scrapers/build_viz.py`(`build_overview` 加 by_source)、`scrapers/test_build_viz.py`(斷言)
**新增(前端):** `web/src/lib/sources.ts`、`web/src/lib/sources.test.ts`
**修改(前端):** `web/src/lib/overview.ts`(`OverviewData` 加 `by_source`)、`web/src/components/coverage/CoverageApp.tsx`

---

## Task 1: 後端 `overview.by_source`

準確的 8 來源筆數。交付物:overview.json 帶 by_source,測試通過。

**Files:**
- Modify: `scrapers/build_viz.py`(`build_overview`)
- Test: `scrapers/test_build_viz.py`

**Interfaces:**
- Produces:`build_overview` 回傳新增 `by_source: dict[str,int]`(source_platform → count,降序)。

- [ ] **Step 1: Write the failing test**

在 `scrapers/test_build_viz.py` 追加:

```python
def test_build_overview_by_source_counts():
    rows = ([_viz(s="S", plat="bravelog.tw") for _ in range(3)]
            + [_viz(s="S", plat="tsu.com.tw") for _ in range(2)]
            + [_viz(s="S", plat=None)])          # None excluded
    ov = BV.build_overview(rows)
    assert ov["by_source"] == {"bravelog.tw": 3, "tsu.com.tw": 2}
```

(若既有測試的 `_viz(...)` helper 無 `plat` 參數,該 helper 的 base dict 已含 `"plat": "p"`,可用 `plat=` 覆寫;確認 helper 支援。)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_build_viz.py::test_build_overview_by_source_counts -v`
Expected: FAIL(`KeyError: 'by_source'`)

- [ ] **Step 3: Add `by_source` in `build_overview`**

在 `build_overview` 既有累計 `sources_seen` 的同一迴圈(`for r in viz:`)旁,新增來源計數;在 return 加 `by_source`。

於迴圈內(`sources_seen.add(r.get("plat"))` 附近)新增:

```python
        if r.get("plat"):
            src_counts[r["plat"]] += 1
```

於迴圈前初始化(與 `sources_seen` 一起):

```python
    src_counts = Counter()
```

於 return dict 加一鍵(放在 genderTrend/ageTrend 旁):

```python
            "by_source": dict(src_counts.most_common()),
```

(`Counter` 已於 build_viz 頂部 import。)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_build_viz.py::test_build_overview_by_source_counts -v`
Expected: PASS

- [ ] **Step 5: Rebuild overview + sanity-check + full suite**

Run:
```bash
python scrapers/build_viz.py
python -c "import json;o=json.load(open('web/public/data/v1/overview.json',encoding='utf-8'));print(o['by_source'])"
python -m pytest scrapers/ -q
```
Expected: `by_source` 印出 8 個來源(bravelog.tw、irunner.biji.co、tsu.com.tw、taiwanbike.org、twbike.org、cyclist.org.tw、criterium.tw、cycling.org.tw)及筆數;pytest 全綠。

- [ ] **Step 6: Commit**

```bash
git add scrapers/build_viz.py scrapers/test_build_viz.py web/public/data/v1/overview.json
git commit -m "feat(coverage): per-source counts (by_source) in overview from master"
```

---

## Task 2: 前端站名對照 + CoverageApp 來源 Card

站名 + 連結 + 準確來源。交付物:/coverage 來源區塊顯示站名(連結)+ 筆數;頂部 KPI 改用 overview。

**Files:**
- Create: `web/src/lib/sources.ts`
- Create: `web/src/lib/sources.test.ts`
- Modify: `web/src/lib/overview.ts`(`OverviewData` 加 `by_source`)
- Modify: `web/src/components/coverage/CoverageApp.tsx`

**Interfaces:**
- Consumes: `loadOverview`(data-load)、`OverviewData.by_source`、`OverviewData.kpi`。
- Produces:`SOURCE_INFO: Record<string,{name:string;url:string}>`、`sourceInfo(domain:string)->{name:string;url:string}`。

- [ ] **Step 1: Add `by_source` to `OverviewData` in `web/src/lib/overview.ts`**

把 `OverviewData` 介面加一欄:

```ts
export interface OverviewData { kpi: Kpi; heat: Heat; trend: Trend; women: WomenShare[]; composition: Composition; genderTrend: GenderTrend; ageTrend: AgeTrend; by_source: Record<string, number>; }
```

- [ ] **Step 2: Write the failing test**

`web/src/lib/sources.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { sourceInfo } from "./sources";

describe("sourceInfo", () => {
  it("maps known domains to site name + url", () => {
    expect(sourceInfo("tsu.com.tw").name).toBe("運動筆記");
    expect(sourceInfo("twbike.org").name).toBe("中華民國登山車協會");
    expect(sourceInfo("bravelog.tw").url).toBe("https://www.bravelog.tw/");
  });
  it("falls back to the domain with empty url for unknown sources", () => {
    expect(sourceInfo("unknown.example")).toEqual({ name: "unknown.example", url: "" });
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd web && npx vitest run src/lib/sources.test.ts`
Expected: FAIL(cannot resolve `./sources`)

- [ ] **Step 4: Implement `web/src/lib/sources.ts`**

```ts
/** Curated human-readable name + link for each scraped source platform. */
export const SOURCE_INFO: Record<string, { name: string; url: string }> = {
  "bravelog.tw": { name: "Bravelog 運動趣", url: "https://www.bravelog.tw/" },
  "irunner.biji.co": { name: "iRunner(biji 運動社群)", url: "https://irunner.biji.co/" },
  "tsu.com.tw": { name: "運動筆記", url: "https://www.tsu.com.tw/" },
  "taiwanbike.org": { name: "中華民國自行車協會(TBA)", url: "https://taiwanbike.org/" },
  "twbike.org": { name: "中華民國登山車協會", url: "https://twbike.org/" },
  "cyclist.org.tw": { name: "自行車騎士協會", url: "https://www.cyclist.org.tw/" },
  "criterium.tw": { name: "criterium.tw(TCU 城市繞圈賽)", url: "https://criterium.tw/" },
  "cycling.org.tw": { name: "中華民國自由車協會", url: "https://cycling.org.tw/" },
};

/** Look up a source domain; unknown -> the domain itself with no link. */
export function sourceInfo(domain: string): { name: string; url: string } {
  return SOURCE_INFO[domain] ?? { name: domain, url: "" };
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd web && npx vitest run src/lib/sources.test.ts`
Expected: PASS

- [ ] **Step 6: Update `CoverageApp.tsx`**

(a) import 加上 `loadOverview`、`sourceInfo`、型別:

```tsx
import { loadCoverage, loadRaces, loadOverview } from "../../lib/data-load";
import type { Coverage, RaceIndex } from "../../lib/types";
import type { OverviewData } from "../../lib/overview";
import { sourceInfo } from "../../lib/sources";
```

(b) state + 載入加 overview:

```tsx
  const [ov, setOv] = useState<OverviewData | null>(null);
  // ...
  useEffect(() => {
    Promise.all([loadCoverage(), loadRaces(), loadOverview()])
      .then(([c, rs, o]) => { setCov(c); setRaces(rs); setOv(o); })
      .catch((e) => setErr(String(e)));
  }, []);
```

(c) gating 等 overview:把 `if (!cov) return <Skeleton cards={3} />;` 改為 `if (!cov || !ov) return <Skeleton cards={3} />;`

(d) 頂部 KPI 改用 overview.kpi(海外仍用 coverage),把該 4 格陣列改為:

```tsx
        {[["成績筆數", ov.kpi.records.toLocaleString()], ["賽事", ov.kpi.races],
          ["年份", `${ov.kpi.minYear}–${ov.kpi.maxYear}`],
          ["海外賽(另計)", s.overseas.toLocaleString()]].map(([k, v]) => (
```

(e) 來源 Card 改讀 `ov.by_source` + 站名連結:

```tsx
      <Card title="✅ 已收錄的來源" hint="有公開成績系統的競技賽事,大多已收齊">
        <div className="flex flex-wrap gap-2 text-sm">
          {Object.entries(ov.by_source).map(([src, n]) => {
            const info = sourceInfo(src);
            return (
              <span key={src} className="rounded-lg border border-border bg-bg px-3 py-1">
                {info.url
                  ? <a href={info.url} target="_blank" rel="noopener" className="text-ink hover:text-accent">{info.name}</a>
                  : <span className="text-ink">{info.name}</span>}
                <span className="num ml-1 text-muted">{n.toLocaleString()}</span>
                <span className="ml-1 text-xs text-muted">{src}</span>
              </span>
            );
          })}
        </div>
      </Card>
```

- [ ] **Step 7: Build + browser-verify**

Run: `npm --prefix web run build`
Expected: 成功。瀏覽器抽查 `/coverage`:來源區塊顯示 **8 個來源**、各為**站名(可點連結)+ 筆數 + 灰字網域**;頂部「成績筆數/賽事/年份」與來源總和一致(來自 overview)。

- [ ] **Step 8: Commit**

```bash
git add web/src/lib/sources.ts web/src/lib/sources.test.ts web/src/lib/overview.ts web/src/components/coverage/CoverageApp.tsx
git commit -m "feat(coverage): show source site names + links (8 sources from overview)"
```

---

## Self-Review

**1. Spec coverage:** 準確 8 來源 → Task 1(by_source from master)+ Task 2(讀 ov.by_source)✅;站名+連結 → sources.ts + Card render ✅;未知 fallback → sourceInfo ✅;站名逐字 → SOURCE_INFO ✅;頂部數字一致 → 改用 overview.kpi ✅;不動 gaps → 未碰 ✅。

**2. Placeholder scan:** 無 TBD;每步附完整程式。

**3. Type consistency:** `OverviewData.by_source`(Task 2 overview.ts)由 Task 1 後端產生、CoverageApp 取用一致;`sourceInfo` 回 `{name,url}` 在 sources.ts 定義、Card 取用一致;`ov.kpi.records/races/minYear/maxYear` 為既有 Kpi 欄位。

---

## 執行順序
Task 1(後端 by_source)→ Task 2(前端對照 + Card)。Task 1 先,Task 2 需 overview.by_source 存在。
