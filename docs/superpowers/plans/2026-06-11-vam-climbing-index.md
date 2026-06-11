# VAM Climbing Index — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a VAM (vertical ascent metres/hour) climbing index to `/climbs` — a single-race VAM leaderboard plus a cross-race「爬坡王」board — built on a curated per-race climb-profile table.

**Architecture:** A curated `climb_profiles.json` (race_key → dist/elev/grade/conf/src) is the single source of truth, read by BOTH the Python build and the frontend. Single-race VAM is computed client-side from race-detail times. The cross-race「爬坡王」board is computed at build time inside `build_athletes.py` (reusing its TCU/UCI/name identity groups) into `climb_vam.json`, so riders match reliably across climbs. UI mounts in the existing `ClimbsApp.tsx`.

**Tech Stack:** Astro 6 + React 19 islands, Tailwind v4, ECharts 6 (echarts-for-react), vitest; Python 3 (build_athletes.py), pytest.

Spec: `docs/superpowers/specs/2026-06-11-vam-climbing-index-design.md`

---

### Task 1: Types — `ClimbProfile` and `ClimbVamEntry`

**Files:**
- Modify: `web/src/lib/types.ts` (append)

- [ ] **Step 1: Add the types**

Append to `web/src/lib/types.ts`:

```typescript
export interface ClimbProfile {
  race_key: string; name: string;
  dist_km: number; elev_m: number; grade: number;  // grade = elev_m/(dist_km*1000)*100
  conf: "high" | "est"; src: string;
}
export interface ClimbVamEntry {
  id: string; nm: string; best_vam: number; best_wkg: number | null;
  climb: string; y: number | null; conf: "high" | "est"; g: "M" | "F" | null;
}
```

- [ ] **Step 2: Type-check**

Run: `cd web && npx astro check`
Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add web/src/lib/types.ts
git commit -m "feat(vam): add ClimbProfile + ClimbVamEntry types"
```

---

### Task 2: Pure VAM functions + tests — `web/src/lib/vam.ts`

**Files:**
- Create: `web/src/lib/vam.ts`
- Test: `web/src/lib/vam.test.ts`

- [ ] **Step 1: Write the failing test**

Create `web/src/lib/vam.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { vam, wkgEstimate, isPlausibleVam } from "./vam";

describe("vam", () => {
  it("vertical metres per hour = elev / hours", () => {
    expect(vam(3275, 3600 * 4)).toBe(819);        // 3275m in 4h
    expect(vam(2900, 9000)).toBe(1160);           // 2900m in 2.5h
  });
  it("null on bad input", () => {
    expect(vam(3000, 0)).toBeNull();
    expect(vam(3000, -5)).toBeNull();
    expect(vam(null as unknown as number, 3600)).toBeNull();
  });
});

describe("wkgEstimate", () => {
  it("Ferrari estimate from vam + grade", () => {
    // 1500 / (100*(2 + 5/10)) = 1500/250 = 6.0
    expect(wkgEstimate(1500, 5)).toBe(6);
    expect(wkgEstimate(null, 5)).toBeNull();
  });
});

describe("isPlausibleVam", () => {
  it("keeps 100..3000, drops outliers", () => {
    expect(isPlausibleVam(1200)).toBe(true);
    expect(isPlausibleVam(50)).toBe(false);
    expect(isPlausibleVam(5000)).toBe(false);
    expect(isPlausibleVam(null)).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test -- --run vam`
Expected: FAIL ("Cannot find module ./vam").

- [ ] **Step 3: Write the implementation**

Create `web/src/lib/vam.ts`:

```typescript
export const VAM_MIN = 100;
export const VAM_MAX = 3000;

/** Vertical ascent metres per hour = elev / (seconds/3600). null if invalid. */
export function vam(elevM: number, seconds: number | null): number | null {
  if (!elevM || !seconds || seconds <= 0) return null;
  return Math.round(elevM / (seconds / 3600));
}

/** Ferrari relative-power estimate (rough): vam / (100 * (2 + grade%/10)). */
export function wkgEstimate(vamValue: number | null, gradePct: number): number | null {
  if (vamValue == null || !gradePct) return null;
  return Math.round((vamValue / (100 * (2 + gradePct / 10))) * 10) / 10;
}

/** Reject timing-error / DNF outliers. */
export function isPlausibleVam(v: number | null): boolean {
  return v != null && v >= VAM_MIN && v <= VAM_MAX;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test -- --run vam`
Expected: PASS (3 suites).

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/vam.ts web/src/lib/vam.test.ts
git commit -m "feat(vam): vam/wkgEstimate/isPlausibleVam pure fns (+vitest)"
```

---

### Task 3: Curated climb-profile table — `web/public/data/climb_profiles.json`

**Files:**
- Create: `web/public/data/climb_profiles.json`

Curated from the 24 climb race_keys present in the data. Wuling (武嶺, summit 3275 m) routes split by start point; only well-known climbs included (寧缺勿填). `grade = elev_m/(dist_km*1000)*100`, rounded to 0.1.

- [ ] **Step 1: Write the file**

Create `web/public/data/climb_profiles.json`:

```json
[
 {"race_key":"臺灣自行車登山王挑戰","name":"臺灣KOM登山王挑戰","dist_km":105,"elev_m":3275,"grade":3.1,"conf":"high","src":"Taiwan KOM Challenge 官方路線 太魯閣→武嶺"},
 {"race_key":"臺灣KOM太平洋經典賽","name":"臺灣KOM太平洋經典賽","dist_km":105,"elev_m":3275,"grade":3.1,"conf":"est","src":"同 KOM 太魯閣→武嶺路線(估)"},
 {"race_key":"臺灣KOM登山王之路夏季","name":"臺灣KOM登山王之路-夏季","dist_km":105,"elev_m":3275,"grade":3.1,"conf":"est","src":"太魯閣→武嶺(估,梯次起點或異)"},
 {"race_key":"臺灣KOM登山王之路春季","name":"臺灣KOM登山王之路-春季","dist_km":105,"elev_m":3275,"grade":3.1,"conf":"est","src":"太魯閣→武嶺(估,梯次起點或異)"},
 {"race_key":"建大武嶺盃","name":"建大武嶺盃","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里地理中心碑→武嶺(估)"},
 {"race_key":"第14屆建大輪胎武嶺盃自行車大會師","name":"建大輪胎武嶺盃大會師","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"第五屆武嶺盃「鐵馬高峰會」國際自行車大賽","name":"武嶺盃鐵馬高峰會","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"TIS崇越盃武嶺自行車挑戰賽","name":"TIS崇越盃武嶺","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"TIS崇越盃武嶺自行車挑戰賽六月場次","name":"TIS崇越盃武嶺(六月)","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"TIS崇越盃武嶺自行車挑戰賽九月場次","name":"TIS崇越盃武嶺(九月)","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"崇越盃武嶺自行車挑戰賽","name":"崇越盃武嶺","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"96聯賽武嶺站挑戰組","name":"96聯賽武嶺站(挑戰)","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"96聯賽武嶺站競賽組及市民競賽組","name":"96聯賽武嶺站(競賽)","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"【96聯賽第四站】96CyclingRace武嶺","name":"96CyclingRace武嶺","dist_km":55,"elev_m":2900,"grade":5.3,"conf":"est","src":"埔里→武嶺(估)"},
 {"race_key":"扶輪盃大屯山自行車登山王","name":"扶輪盃大屯山登山王","dist_km":17,"elev_m":1050,"grade":6.2,"conf":"est","src":"大屯山鞍部 climb(估)"},
 {"race_key":"扶輪盃陽明山自行車登山王挑戰","name":"扶輪盃陽明山登山王挑戰","dist_km":20,"elev_m":1100,"grade":5.5,"conf":"est","src":"陽明山擎天崗(估)"},
 {"race_key":"扶輪盃陽明山自行車登山王","name":"扶輪盃陽明山登山王","dist_km":20,"elev_m":1100,"grade":5.5,"conf":"est","src":"陽明山擎天崗(估)"}
]
```

> Known gaps left uncurated (route uncertain): NeverStop武嶺、塔塔加(新中橫)、中寮KOM、石壁爬坡、石門佛陀KOM. These simply get no VAM until reliable profiles are sourced.

- [ ] **Step 2: Validate JSON**

Run: `python -c "import json; d=json.load(open('web/public/data/climb_profiles.json',encoding='utf-8')); print(len(d),'profiles')"`
Expected: `17 profiles`.

- [ ] **Step 3: Commit**

```bash
git add web/public/data/climb_profiles.json
git commit -m "feat(vam): curated climb-profile table (17 climbs, conf+src)"
```

---

### Task 4: `build_athletes.py` emits `climb_vam.json` (+pytest)

**Files:**
- Modify: `scrapers/build_athletes.py`
- Test: `scrapers/test_build_athletes.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `scrapers/test_build_athletes.py`:

```python
def test_vam_helpers():
    assert ba._vam(3275, 3600 * 4) == 819
    assert ba._vam(2900, 0) is None
    assert ba._wkg(1500, 5) == 6.0
    assert ba._plausible(1200) and not ba._plausible(50) and not ba._plausible(5000)


def test_build_climb_vam_best_per_athlete():
    profiles = {"climbA": {"name": "Climb A", "elev_m": 3000, "grade": 6.0, "conf": "high"}}
    # one athlete, two climbA results: faster time -> higher VAM is the one kept
    recs = [
        _rec("王大明", tsu="TCU-x", rk="climbA", year=2023, t=3600 * 3),   # 1000 VAM
        _rec("王大明", tsu="TCU-x", rk="climbA", year=2024, t=3600 * 2.5), # 1200 VAM (best)
        _rec("王大明", tsu="TCU-x", rk="other", year=2024, t=3600),         # not a climb
    ]
    rows = ba.build_climb_vam(recs, profiles)
    assert len(rows) == 1
    e = rows[0]
    assert e["best_vam"] == 1200 and e["y"] == 2024 and e["climb"] == "Climb A"
    assert e["conf"] == "high" and e["g"] == "M" and e["best_wkg"] is not None
    assert "id" in e and e["nm"] == "王○明"  # de-identified
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_build_athletes.py::test_build_climb_vam_best_per_athlete -q`
Expected: FAIL (`module 'build_athletes' has no attribute '_vam'`).

- [ ] **Step 3: Implement the helpers + builder**

In `scrapers/build_athletes.py`, add near the top (after imports):

```python
PROFILES_PATH = os.path.join(OUT, "climb_profiles.json")
VAM_MIN, VAM_MAX = 100, 3000


def _vam(elev_m, seconds):
    if not elev_m or not seconds or seconds <= 0:
        return None
    return round(elev_m / (seconds / 3600))


def _wkg(vam_value, grade_pct):
    if vam_value is None or not grade_pct:
        return None
    return round(vam_value / (100 * (2 + grade_pct / 10)), 1)


def _plausible(v):
    return v is not None and VAM_MIN <= v <= VAM_MAX


def load_profiles():
    if not os.path.exists(PROFILES_PATH):
        return {}
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return {p["race_key"]: p for p in json.load(f)}


def build_climb_vam(records, profiles):
    """Best VAM per athlete across profiled climb races. Uses the same identity
    grouping as build_athletes (tsu/UCI/name)."""
    keys = build_group_keys(records)
    groups = defaultdict(list)
    for k, r in zip(keys, records):
        if k not in ("n:", "u:", "t:"):
            groups[k].append(r)
    out = []
    for gk, recs in groups.items():
        best = None
        for r in recs:
            prof = profiles.get(r.get("race_key"))
            if not prof:
                continue
            v = _vam(prof["elev_m"], r.get("finish_seconds"))
            if not _plausible(v):
                continue
            if best is None or v > best["best_vam"]:
                best = {"best_vam": v, "best_wkg": _wkg(v, prof.get("grade")),
                        "climb": prof["name"], "y": r.get("year"),
                        "conf": prof.get("conf"), "g": r.get("gender")}
        if best is None:
            continue
        masked = Counter(r.get("name_masked") or common.mask_name(r.get("name_raw"))
                         for r in recs).most_common(1)[0][0]
        out.append({"id": athlete_id(gk), "nm": masked, **best})
    out.sort(key=lambda e: -e["best_vam"])
    return out
```

In `main()`, after the `athletes`/`detail` files are written, add:

```python
    profiles = load_profiles()
    climb_vam = build_climb_vam(records, profiles)
    with open(os.path.join(OUT, "climb_vam.json"), "w", encoding="utf-8") as f:
        json.dump(climb_vam, f, ensure_ascii=False, separators=(",", ":"))
    print(f"climb_vam={len(climb_vam)} (across {len(profiles)} profiled climbs)")
```

(Note: `OUT` in build_athletes already points to `web/public/data`; confirm by reading the file. If the constant is named differently, use that path.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_build_athletes.py -q`
Expected: PASS (all athlete tests).

- [ ] **Step 5: Regenerate + sanity-check**

Run: `python scrapers/build_athletes.py`
Expected: prints `athletes=15301 ...` and `climb_vam=<N> (across 17 profiled climbs)` with N in the thousands.

- [ ] **Step 6: Commit**

```bash
git add scrapers/build_athletes.py scrapers/test_build_athletes.py web/public/data/climb_vam.json
git commit -m "feat(vam): build_athletes emits climb_vam.json (cross-race 爬坡王, +pytest)"
```

---

### Task 5: Data loaders — `loadClimbProfiles` / `loadClimbVam`

**Files:**
- Modify: `web/src/lib/data-load.ts`

- [ ] **Step 1: Add loaders**

In `web/src/lib/data-load.ts`, extend the import and append two functions:

```typescript
// extend existing type import:
import type { SlimRecord, RaceIndex, DetailRow, AthleteIndexEntry, AthleteDetail, ClimbProfile, ClimbVamEntry } from "./types";
```

```typescript
export async function loadClimbProfiles(): Promise<ClimbProfile[]> {
  const r = await fetch(`${base}/data/climb_profiles.json`);
  if (!r.ok) throw new Error(`climb_profiles.json ${r.status}`);
  return r.json();
}
export async function loadClimbVam(): Promise<ClimbVamEntry[]> {
  const r = await fetch(`${base}/data/climb_vam.json`);
  if (!r.ok) throw new Error(`climb_vam.json ${r.status}`);
  return r.json();
}
```

- [ ] **Step 2: Type-check + commit**

Run: `cd web && npx astro check`  → 0 errors.

```bash
git add web/src/lib/data-load.ts
git commit -m "feat(vam): climb_profiles + climb_vam loaders"
```

---

### Task 6: `VamLeaderboard.tsx` — single-race VAM (client-side)

**Files:**
- Create: `web/src/components/climbs/VamLeaderboard.tsx`

- [ ] **Step 1: Write the component**

Create `web/src/components/climbs/VamLeaderboard.tsx`:

```tsx
import { useMemo } from "react";
import type { DetailRow, ClimbProfile } from "../../lib/types";
import { vam, wkgEstimate, isPlausibleVam } from "../../lib/vam";
import { secondsToHMS } from "../../lib/format";

export default function VamLeaderboard({ rows, profile }: { rows: DetailRow[]; profile: ClimbProfile }) {
  const ranked = useMemo(() => {
    const out = rows
      .map((r) => ({ r, v: vam(profile.elev_m, r.t) }))
      .filter((x) => isPlausibleVam(x.v))
      .sort((a, b) => (b.v as number) - (a.v as number));
    return out;
  }, [rows, profile]);

  const dropped = rows.filter((r) => r.t).length - ranked.length;

  return (
    <div>
      <p className="mb-2 text-xs text-muted">
        {profile.name} · {profile.dist_km}km · 爬升 {profile.elev_m}m · 均斜率 {profile.grade}%
        {profile.conf === "est" && " · 路線數據為估計"}({profile.src})
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="py-1 pr-3 num">#</th><th className="py-1 pr-3">選手</th>
              <th className="py-1 pr-3 num">VAM</th><th className="py-1 pr-3 num">推算 W/kg</th>
              <th className="py-1 pr-3 num">完賽</th><th className="py-1 pr-3">車隊</th>
            </tr>
          </thead>
          <tbody>
            {ranked.slice(0, 50).map((x, i) => (
              <tr key={i} className="border-t border-border/60">
                <td className="py-1.5 pr-3 num text-muted">{i + 1}</td>
                <td className="py-1.5 pr-3 text-ink">{x.r.name ?? "—"}</td>
                <td className="py-1.5 pr-3 num text-accent">{x.v}</td>
                <td className="py-1.5 pr-3 num text-muted">{wkgEstimate(x.v, profile.grade) ?? "—"}</td>
                <td className="py-1.5 pr-3 num text-muted">{secondsToHMS(x.r.t)}</td>
                <td className="py-1.5 pr-3 text-muted">{x.r.team ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {dropped > 0 && <p className="mt-2 text-xs text-muted">已濾除 {dropped} 筆時間異常(VAM 超出合理範圍)。</p>}
    </div>
  );
}
```

- [ ] **Step 2: Type-check + commit**

Run: `cd web && npx astro check`  → 0 errors.

```bash
git add web/src/components/climbs/VamLeaderboard.tsx
git commit -m "feat(vam): single-race VAM leaderboard component"
```

---

### Task 7: `ClimbKingBoard.tsx` — cross-race 爬坡王

**Files:**
- Create: `web/src/components/climbs/ClimbKingBoard.tsx`

- [ ] **Step 1: Write the component**

Create `web/src/components/climbs/ClimbKingBoard.tsx`:

```tsx
import { useMemo, useState } from "react";
import type { ClimbVamEntry } from "../../lib/types";

export default function ClimbKingBoard({ entries }: { entries: ClimbVamEntry[] }) {
  const [g, setG] = useState<"" | "M" | "F">("");
  const ranked = useMemo(
    () => entries.filter((e) => !g || e.g === g).slice(0, 50),
    [entries, g],
  );
  return (
    <div>
      <div className="mb-2 flex gap-2 text-sm">
        {([["", "全部"], ["M", "男"], ["F", "女"]] as const).map(([v, t]) => (
          <button key={v} onClick={() => setG(v)}
            className={`rounded-lg border px-2 py-1 ${g === v ? "border-accent text-accent" : "border-border text-muted hover:text-accent"}`}>
            {t}
          </button>
        ))}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="py-1 pr-3 num">#</th><th className="py-1 pr-3">選手</th>
              <th className="py-1 pr-3 num">最佳 VAM</th><th className="py-1 pr-3 num">推算 W/kg</th>
              <th className="py-1 pr-3">達成於</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((e, i) => (
              <tr key={e.id} className="border-t border-border/60">
                <td className="py-1.5 pr-3 num text-muted">{i + 1}</td>
                <td className="py-1.5 pr-3">
                  <a className="text-ink hover:text-accent" href={`${import.meta.env.BASE_URL.replace(/\/$/, "")}/athletes?id=${e.id}`}>{e.nm}</a>
                </td>
                <td className="py-1.5 pr-3 num text-accent">{e.best_vam}</td>
                <td className="py-1.5 pr-3 num text-muted">{e.best_wkg ?? "—"}</td>
                <td className="py-1.5 pr-3 text-muted">{e.y} {e.climb}{e.conf === "est" ? "*" : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-muted">* 路線數據為估計。選手身分以 TCU/UCI ID 為錨、姓名為輔,點名字看其生涯。</p>
    </div>
  );
}
```

- [ ] **Step 2: Type-check + commit**

Run: `cd web && npx astro check`  → 0 errors.

```bash
git add web/src/components/climbs/ClimbKingBoard.tsx
git commit -m "feat(vam): cross-race 爬坡王 board (links to athlete pages)"
```

---

### Task 8: `VamMethodology.tsx` — transparency card

**Files:**
- Create: `web/src/components/climbs/VamMethodology.tsx`

- [ ] **Step 1: Write the component**

Create `web/src/components/climbs/VamMethodology.tsx`:

```tsx
export default function VamMethodology() {
  return (
    <div className="space-y-1 text-xs text-muted">
      <p><b className="text-ink">VAM</b>(Vertical Ascent Metres/hour)= 總爬升公尺 ÷ 完賽時數,衡量純爬升速度,跨年跨賽可比。</p>
      <p><b className="text-ink">推算 W/kg</b> 用 Ferrari 公式 <span className="num">VAM /(100·(2+均斜率%/10))</span> 估計相對功率——<b>非實測</b>,無體重/功率計,僅供參考;低均斜率路線(如含長緩坡的 KOM)估值較不準。</p>
      <p>各爬坡賽的距離/爬升見排行榜標頭;標「估計」者路線數據為估算。VAM 僅取 100–3000 之間(濾除計時錯誤/未完賽)。</p>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/src/components/climbs/VamMethodology.tsx
git commit -m "feat(vam): methodology transparency card"
```

---

### Task 9: Mount in `ClimbsApp.tsx`

**Files:**
- Modify: `web/src/components/climbs/ClimbsApp.tsx`

- [ ] **Step 1: Wire profiles + VAM sections**

Edit `web/src/components/climbs/ClimbsApp.tsx`:

1. Extend imports:

```tsx
import { loadRaces, loadRaceDetail, loadClimbProfiles, loadClimbVam } from "../../lib/data-load";
import type { RaceIndex, DetailRow, ClimbProfile, ClimbVamEntry } from "../../lib/types";
import VamLeaderboard from "./VamLeaderboard";
import ClimbKingBoard from "./ClimbKingBoard";
import VamMethodology from "./VamMethodology";
```

2. Add state inside `ClimbsApp`:

```tsx
  const [profiles, setProfiles] = useState<Record<string, ClimbProfile>>({});
  const [vamRows, setVamRows] = useState<ClimbVamEntry[]>([]);
```

3. In the `useEffect`, after `loadRaces().then(...)`, also load the two new files (place alongside the existing load):

```tsx
    loadClimbProfiles().then((ps) => setProfiles(Object.fromEntries(ps.map((p) => [p.race_key, p])))).catch(() => {});
    loadClimbVam().then(setVamRows).catch(() => {});
```

4. In the render, inside the `{!detail ? ... : (...)}` block, ADD the VAM leaderboard as the FIRST card when the selected race has a profile (before「你贏過多少%」):

```tsx
              {sel && profiles[sel.rk] && (
                <Card title="爬坡指數 VAM 排行" hint="垂直爬升速度(公尺/小時),跨賽可比">
                  <VamLeaderboard rows={detail} profile={profiles[sel.rk]} />
                </Card>
              )}
```

5. After the whole `{sel && (...)}` block (at the end of the top-level returned `<div className="space-y-6">`), ADD the cross-race board + methodology:

```tsx
      {vamRows.length > 0 && (
        <Card title="🏔 跨賽爬坡王" hint="每位選手在所有有路線數據的爬坡賽中的最佳 VAM">
          <ClimbKingBoard entries={vamRows} />
        </Card>
      )}
      <Card title="方法論"><VamMethodology /></Card>
```

- [ ] **Step 2: Type-check**

Run: `cd web && npx astro check`
Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add web/src/components/climbs/ClimbsApp.tsx
git commit -m "feat(vam): mount VAM leaderboard + 爬坡王 + methodology in /climbs"
```

---

### Task 10: Verify end-to-end + push

- [ ] **Step 1: Full test suites**

Run: `python -m pytest scrapers/ -q && cd web && npm test -- --run`
Expected: all pytest pass (19+), all vitest pass (37+).

- [ ] **Step 2: Build**

Run: `cd web && npx astro check && npm run build`
Expected: 0 type errors; build completes; `/climbs` emitted.

- [ ] **Step 3: Browser-verify**

Run `npm run preview`, open the printed `http://localhost:<port>/climbs`. Confirm via snapshot/screenshot:
- A profiled climb (e.g. 臺灣自行車登山王挑戰) shows the「爬坡指數 VAM 排行」card with VAM + 推算 W/kg, descending.
- 「🏔 跨賽爬坡王」board renders, names link to `/athletes?id=...`, gender filter works.
- Methodology card present. No console errors.
Then stop the preview server and kill any zombie `astro preview` processes.

- [ ] **Step 4: Push**

```bash
git push
```
Expected: master updated; Vercel auto-deploys.

---

## Notes for the executor

- `build_athletes.py` already defines `OUT` (= `web/public/data`), `athlete_id`, `build_group_keys`, `common`, `Counter`, `defaultdict`, `json`, `os`. Reuse them; do NOT re-import or redefine.
- Masked names only — `climb_vam.json` and race-detail rows already carry `name_masked`/`nm`; never surface `name_raw`.
- Follow the existing Card/table styling already used in `ClimbsApp.tsx` (warm Claude tokens: `border-border`, `bg-surface`, `text-accent`, `num`).
- `climb_profiles.json` is the single source of truth, read by both Python (build) and the browser — do not duplicate the elevation data anywhere else.
