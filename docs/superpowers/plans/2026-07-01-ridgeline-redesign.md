# Ridgeline 改版 實作計畫(Phase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把首頁與全站視覺語言改成方案 C「Ridgeline/稜線」——深/淺雙色 token、招牌稜線元件、首頁全改、圖表換色。

**Architecture:** 沿用既有 token 機制(`tokens.css` 的 `@theme inline + var() fallback + html.dark`)、既有主題切換(Base.astro 的 no-flash inline script + `themechange` 事件 + `EChart.tsx key={theme}`)。只換 token 值、加招牌色 `--summit`、加型別/間距 helper class,新增純幾何 `ridgeline.ts` + `Ridgeline.tsx` 元件 + 建置產物 `home_ridgeline.json`,重繪 `echarts-theme.ts`,重排 `index.astro` 與 `Base.astro` chrome。內頁自動繼承新色/字,不重排。

**Tech Stack:** Astro + React islands + Tailwind v4 + ECharts + vitest;Python(建置 home_ridgeline)+ pytest。

## Global Constraints

- **深色 token(terrain)**:`--bg #0E1315` · `--surface #161D20` · `--border #2A3538` · `--ink #ECEFEC` · `--muted #84908A` · `--accent(flamme) #EC3A2B` · `--summit #F2B84B`。
- **淺色 token(cool paper)**:`--bg #EFF1EE` · `--surface #FFFFFF` · `--border #D2D8D3` · `--ink #12181A` · `--muted #5A6560` · `--accent(flamme) #D23120` · `--summit #C98A1E`。
- 沿用既有機制:淺色值放 `@theme inline` 的 `var()` fallback + `html { --x }` 區塊;深色值放 `html.dark { --x }`。**CSS 註解不得含撇號**(Tailwind v4 parser 會炸)。
- **字體分工**:Mono(Spline Sans Mono)為招牌數據字;Fraunces 只在 hero/章節引言;內文 Hanken/Noto。字體檔案與 `@font-face` 不改(變數軸已含所需字重)。
- **深/淺皆一等公民**;切換沿用既有 `html.dark` + `themechange`;圖表顏色只能由 theme 驅動,**不得**在 chart options 內寫死。
- **不動**:資料管線、master/dataset、API 結構、內頁資料邏輯與版面。
- 驗證回歸:build 後 dist CSS 必須**同時**含 `#0E1315` 與 `#EFF1EE`(防 Tailwind v4 token stripping)。
- Hero 統計用即時 `manifest.json` 的 `stats`;Hero 稜線資料為建置產物 `home_ridgeline.json`(誠實標「峰高 = 中位完賽時間」)。

## File Structure

- `web/src/styles/tokens.css` — 換 palette、加 `--summit`、加型別/間距 helper。
- `web/src/lib/echarts-theme.ts` — `claude`/`claude-dark` 換 terrain/flamme。
- `web/src/lib/ridgeline.ts`(新)— 純幾何 `ridgelinePath()`。
- `web/src/lib/ridgeline.test.ts`(新)— vitest。
- `web/src/components/site/Ridgeline.tsx`(新)— 稜線元件(4 variant)。
- `scrapers/build_home_ridgeline.py`(新)+ `scrapers/home_ridgeline.py`(新純函式)— 產出 `web/public/data/v1/home_ridgeline.json`。
- `scrapers/test_home_ridgeline.py`(新)— pytest。
- `web/src/lib/data-load.ts` — 加 `loadHomeRidgeline()`。
- `web/src/layouts/Base.astro` — header wordmark/mono + 稜線進度 + footer mono。
- `web/src/pages/index.astro` — 首頁全改(hero + sections;OverviewApp 留在下方)。

## 執行順序
Task 1(token)→ 2(圖表色)→ 3(幾何)→ 4(元件)→ 5(建置資料+loader)→ 6(chrome)→ 7(首頁)→ controller 收尾驗證。

---

## Task 1: 設計 token(雙色 palette + 型別/間距 helper)

**Files:** Modify `web/src/styles/tokens.css`

**Interfaces:**
- Produces CSS custom properties/utilities used site-wide: `--bg/--surface/--border/--ink/--muted/--accent/--summit`(翻色)、`--font-display/body/mono`(不變)、helper class `.section` `.eyebrow` `.display-xl` `.stat` `.hairline`。

- [ ] **Step 1: 換 palette + 加 --summit**

把 `tokens.css` 的 `html {…}`、`html.dark {…}`、`@theme inline {…}` 三段換成(保留 `--series-blue/--series-sage` 名稱但改值以配新盤;新增 `--summit`):

```css
html {
  --bg: #EFF1EE;
  --surface: #FFFFFF;
  --border: #D2D8D3;
  --ink: #12181A;
  --muted: #5A6560;
  --accent: #D23120;
  --summit: #C98A1E;
  --series-blue: #3F6B78;
  --series-sage: #5C7355;
}
html.dark {
  --bg: #0E1315;
  --surface: #161D20;
  --border: #2A3538;
  --ink: #ECEFEC;
  --muted: #84908A;
  --accent: #EC3A2B;
  --summit: #F2B84B;
  --series-blue: #7FA9B6;
  --series-sage: #9BB089;
}
html { color-scheme: light; }
html.dark { color-scheme: dark; }

@theme inline {
  --color-bg: var(--bg, #EFF1EE);
  --color-surface: var(--surface, #FFFFFF);
  --color-border: var(--border, #D2D8D3);
  --color-ink: var(--ink, #12181A);
  --color-muted: var(--muted, #5A6560);
  --color-accent: var(--accent, #D23120);
  --color-summit: var(--summit, #C98A1E);
  --color-series-blue: var(--series-blue, #3F6B78);
  --color-series-sage: var(--series-sage, #5C7355);
}
```
(保留其下的 `@theme { --font-* }`、`html { background… }`、`h1,h2,h3,.display`、`.num`、`.scroll-x` 區塊不動,但把 `.scroll-x` 內兩處寫死 `#fff` 的 fallback 換成 `var(--surface, #fff)` 已是現況——確認即可。)

- [ ] **Step 2: 加型別/間距 helper(接在 `.num` 規則後)**

```css
/* Ridgeline design language: type scale + section rhythm helpers. */
.section { padding-block: clamp(4rem, 10vh, 8rem); }
.display-xl { font-family: var(--font-display); font-weight: 600; letter-spacing: -0.02em; line-height: 1.02; font-size: clamp(2.75rem, 6vw, 5.5rem); }
.eyebrow { font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.8125rem; color: var(--muted, #5A6560); }
.stat { font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-size: clamp(2.5rem, 5vw, 4rem); line-height: 1; }
.hairline { border: none; height: 1px; background: var(--border, #D2D8D3); }
```

- [ ] **Step 3: build + 雙色回歸驗證**

Run:
```bash
python scrapers/build_fonts.py >/dev/null 2>&1 || true   # fonts unchanged; safe no-op if sources absent
npm --prefix web run build 2>&1 | tail -2
grep -rl "0E1315" web/dist/_astro/*.css >/dev/null && echo "DARK ok"
grep -rl "EFF1EE" web/dist/_astro/*.css >/dev/null && echo "LIGHT ok"
```
Expected: build 成功;印出 `DARK ok` 與 `LIGHT ok`(兩色都在 bundle → token stripping 未回歸)。

- [ ] **Step 4: Commit**

```bash
git add web/src/styles/tokens.css
git commit -m "feat(redesign): terrain/paper dual-mode tokens + type-scale helpers"
```

---

## Task 2: ECharts 主題換色(terrain/flamme)

**Files:** Modify `web/src/lib/echarts-theme.ts`

**Interfaces:** Consumes 無;Produces `claude`/`claude-dark` 主題(名稱不變,`EChart.tsx` 已依 `useDark()` 選用)。

- [ ] **Step 1: 換 `claude`(淺色)主題色**

把 `registerTheme("claude", {…})` 內的色值換成新盤(flamme 領頭、cool-paper 格線/文字):

```js
echarts.registerTheme("claude", {
  color: ["#D23120", "#3F6B78", "#5C7355", "#C98A1E", "#8A6D9C", "#A0564B"],
  backgroundColor: "transparent",
  animationDuration: 700, animationEasing: "cubicOut",
  textStyle: { fontFamily: "Spline Sans Mono, Hanken Grotesk, Noto Sans TC, system-ui, sans-serif", color: "#12181A" },
  title: { textStyle: { color: "#12181A", fontFamily: "Fraunces, Noto Serif TC, serif" } },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#D2D8D3" } }, axisTick: { lineStyle: { color: "#D2D8D3" } },
    axisLabel: { color: "#5A6560", fontFamily: "Spline Sans Mono, monospace" }, splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false },
    axisLabel: { color: "#5A6560", fontFamily: "Spline Sans Mono, monospace" },
    splitLine: { lineStyle: { color: "#D2D8D3", type: "dashed" } },
  },
  legend: { textStyle: { color: "#5A6560" } },
  radar: {
    axisName: { color: "#5A6560" }, splitArea: { show: false },
    axisLine: { lineStyle: { color: "#D2D8D3" } }, splitLine: { lineStyle: { color: "#D2D8D3" } },
  },
  tooltip: {
    backgroundColor: "#FFFFFF", borderColor: "#D2D8D3",
    textStyle: { color: "#12181A", fontFamily: "Spline Sans Mono, Hanken Grotesk, sans-serif" },
  },
});
```

- [ ] **Step 2: 換 `claude-dark`(深色)主題色**

```js
echarts.registerTheme("claude-dark", {
  color: ["#EC3A2B", "#7FA9B6", "#9BB089", "#F2B84B", "#B597BA", "#C2766A"],
  backgroundColor: "transparent",
  animationDuration: 700, animationEasing: "cubicOut",
  textStyle: { fontFamily: "Spline Sans Mono, Hanken Grotesk, Noto Sans TC, system-ui, sans-serif", color: "#ECEFEC" },
  title: { textStyle: { color: "#ECEFEC", fontFamily: "Fraunces, Noto Serif TC, serif" } },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#2A3538" } }, axisTick: { lineStyle: { color: "#2A3538" } },
    axisLabel: { color: "#84908A", fontFamily: "Spline Sans Mono, monospace" }, splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false },
    axisLabel: { color: "#84908A", fontFamily: "Spline Sans Mono, monospace" },
    splitLine: { lineStyle: { color: "#222B2E", type: "dashed" } },
  },
  legend: { textStyle: { color: "#84908A" } },
  radar: {
    axisName: { color: "#84908A" }, splitArea: { show: false },
    axisLine: { lineStyle: { color: "#2A3538" } }, splitLine: { lineStyle: { color: "#2A3538" } },
  },
  tooltip: {
    backgroundColor: "#161D20", borderColor: "#2A3538",
    textStyle: { color: "#ECEFEC", fontFamily: "Spline Sans Mono, Hanken Grotesk, sans-serif" },
  },
});
```

- [ ] **Step 3: build + commit**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。
```bash
git add web/src/lib/echarts-theme.ts
git commit -m "feat(redesign): recolor ECharts themes to terrain/flamme + mono axes"
```

---

## Task 3: 稜線幾何純函式 `ridgeline.ts`

**Files:** Create `web/src/lib/ridgeline.ts`, `web/src/lib/ridgeline.test.ts`

**Interfaces:** Produces:
```ts
export interface RidgeNode { label?: string; x: number; y: number; meta?: Record<string, unknown>; }
export interface RidgelineGeometry {
  width: number; height: number; d: string; area: string;
  nodes: { cx: number; cy: number; node: RidgeNode }[];
}
export function ridgelinePath(points: RidgeNode[], width: number, height: number, pad?: number): RidgelineGeometry;
```
- `x` 依給定值線性映射到 `[pad, width-pad]`(若所有 x 相同則等距);`y` 值**越大峰越高**(cy 越小),線性映射到 `[pad, height-pad]`。
- `d` = 平滑折線(Catmull-Rom→貝茲);`area` = `d` 再連到底邊封閉(供淡填色);`nodes` = 每點的 `cx/cy`。

- [ ] **Step 1: 寫失敗測試 `web/src/lib/ridgeline.test.ts`**

```ts
import { describe, it, expect } from "vitest";
import { ridgelinePath } from "./ridgeline";

describe("ridgelinePath", () => {
  const pts = [
    { x: 0, y: 10, label: "A" },
    { x: 1, y: 30, label: "B" },
    { x: 2, y: 20, label: "C" },
  ];
  it("maps x across the padded width and returns a node per point", () => {
    const g = ridgelinePath(pts, 300, 100, 10);
    expect(g.nodes).toHaveLength(3);
    expect(g.nodes[0].cx).toBeCloseTo(10);        // first at left pad
    expect(g.nodes[2].cx).toBeCloseTo(290);       // last at width - pad
  });
  it("puts the highest y value at the smallest cy (tallest peak)", () => {
    const g = ridgelinePath(pts, 300, 100, 10);
    const cyB = g.nodes[1].cy, cyA = g.nodes[0].cy;
    expect(cyB).toBeLessThan(cyA);                // y=30 peaks above y=10
    expect(g.nodes[1].cy).toBeCloseTo(10);        // max y -> top pad
    expect(g.nodes[0].cy).toBeCloseTo(90);        // min y -> bottom pad
  });
  it("returns an svg path starting with a move and a closed area", () => {
    const g = ridgelinePath(pts, 300, 100, 10);
    expect(g.d.startsWith("M")).toBe(true);
    expect(g.area.startsWith("M")).toBe(true);
    expect(g.area.trimEnd().endsWith("Z")).toBe(true);
  });
  it("handles a single point without NaN", () => {
    const g = ridgelinePath([{ x: 0, y: 5 }], 100, 40, 8);
    expect(g.nodes[0].cx).toBeCloseTo(50);        // single -> centered
    expect(Number.isNaN(g.nodes[0].cy)).toBe(false);
  });
});
```

Run: `cd web && npx vitest run src/lib/ridgeline.test.ts` → FAIL(module 不存在)。

- [ ] **Step 2: 實作 `web/src/lib/ridgeline.ts`**

```ts
export interface RidgeNode { label?: string; x: number; y: number; meta?: Record<string, unknown>; }
export interface RidgelineGeometry {
  width: number; height: number; d: string; area: string;
  nodes: { cx: number; cy: number; node: RidgeNode }[];
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Deterministic ridgeline geometry: data points -> smoothed SVG path + node
 * coordinates. Higher y renders as a taller peak (smaller cy). Pure, no DOM. */
export function ridgelinePath(points: RidgeNode[], width: number, height: number, pad = 8): RidgelineGeometry {
  const n = points.length;
  const xs = points.map((p) => p.x), ys = points.map((p) => p.y);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const spanX = xMax - xMin || 1, spanY = yMax - yMin || 1;
  const left = pad, right = width - pad, top = pad, bottom = height - pad;

  const nodes = points.map((p, i) => {
    const cx = n === 1 ? width / 2 : lerp(left, right, (p.x - xMin) / spanX);
    const cy = n === 1 ? (top + bottom) / 2 : lerp(bottom, top, (p.y - yMin) / spanY);
    return { cx, cy, node: p };
  });

  if (n === 1) {
    const { cx, cy } = nodes[0];
    const d = `M ${cx.toFixed(2)} ${cy.toFixed(2)}`;
    return { width, height, d, area: `${d} L ${cx.toFixed(2)} ${bottom.toFixed(2)} Z`, nodes };
  }

  // Catmull-Rom -> cubic bezier for a smooth ridgeline.
  const pt = nodes.map((p) => [p.cx, p.cy] as const);
  let d = `M ${pt[0][0].toFixed(2)} ${pt[0][1].toFixed(2)}`;
  for (let i = 0; i < pt.length - 1; i++) {
    const p0 = pt[i - 1] ?? pt[i], p1 = pt[i], p2 = pt[i + 1], p3 = pt[i + 2] ?? p2;
    const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C ${c1x.toFixed(2)} ${c1y.toFixed(2)}, ${c2x.toFixed(2)} ${c2y.toFixed(2)}, ${p2[0].toFixed(2)} ${p2[1].toFixed(2)}`;
  }
  const area = `${d} L ${right.toFixed(2)} ${bottom.toFixed(2)} L ${left.toFixed(2)} ${bottom.toFixed(2)} Z`;
  return { width, height, d, area, nodes };
}
```

Run: `cd web && npx vitest run src/lib/ridgeline.test.ts` → PASS(4 tests)。

- [ ] **Step 3: Commit**

```bash
git add web/src/lib/ridgeline.ts web/src/lib/ridgeline.test.ts
git commit -m "feat(redesign): ridgelinePath pure geometry + tests"
```

---

## Task 4: 稜線元件 `Ridgeline.tsx`

**Files:** Create `web/src/components/site/Ridgeline.tsx`

**Interfaces:** Consumes `ridgelinePath`, `RidgeNode`(Task 3);Produces default export `Ridgeline` with props `{ variant?: "hero"|"divider"|"inline"; data?: RidgeNode[]; height?: number; className?: string; ariaLabel?: string }`.

- [ ] **Step 1: 實作元件**

`web/src/components/site/Ridgeline.tsx`:

```tsx
import { useEffect, useId, useRef, useState } from "react";
import { ridgelinePath, type RidgeNode } from "../../lib/ridgeline";

const VIEW_W = 1000;

/** The site signature: one continuous line that is both decoration and data.
 * variant "hero" draws on load and labels peaks; "divider" is a hairline;
 * "inline" is a compact profile for cards. Respects reduced-motion. */
export default function Ridgeline({
  variant = "hero",
  data = [],
  height = variant === "divider" ? 24 : 220,
  className = "",
  ariaLabel = "賽事完賽時間剖面",
}: {
  variant?: "hero" | "divider" | "inline";
  data?: RidgeNode[];
  height?: number;
  className?: string;
  ariaLabel?: string;
}) {
  const gid = useId().replace(/:/g, "");
  const pad = variant === "divider" ? 2 : 14;
  const pts = data.length ? data : [{ x: 0, y: 0.5 }, { x: 1, y: 0.5 }];
  const g = ridgelinePath(pts, VIEW_W, height, pad);
  const pathRef = useRef<SVGPathElement>(null);
  const [drawn, setDrawn] = useState(false);

  useEffect(() => {
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce || variant !== "hero") { setDrawn(true); return; }
    const el = pathRef.current;
    if (!el) return;
    const len = el.getTotalLength();
    el.style.strokeDasharray = String(len);
    el.style.strokeDashoffset = String(len);
    // next frame -> transition to 0
    const r = requestAnimationFrame(() => {
      el.style.transition = "stroke-dashoffset 1200ms cubic-bezier(.22,.61,.36,1)";
      el.style.strokeDashoffset = "0";
      setDrawn(true);
    });
    return () => cancelAnimationFrame(r);
  }, [variant, g.d]);

  return (
    <svg className={className} viewBox={`0 0 ${VIEW_W} ${height}`} preserveAspectRatio="none"
      role="img" aria-label={ariaLabel} style={{ width: "100%", height, display: "block" }}>
      {variant !== "divider" && (
        <path d={g.area} fill={`url(#${gid})`} opacity={0.12} />
      )}
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
      <path ref={pathRef} d={g.d} fill="none"
        stroke={variant === "divider" ? "var(--border)" : "var(--accent)"}
        strokeWidth={variant === "divider" ? 1 : 2}
        strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      {variant === "hero" && drawn && g.nodes.map((nd, i) => (
        <g key={i}>
          <circle cx={nd.cx} cy={nd.cy} r={3.5} fill="var(--bg)" stroke="var(--accent)" strokeWidth={2}
            vectorEffect="non-scaling-stroke" />
        </g>
      ))}
    </svg>
  );
}
```
> 註:峰點文字標籤因 `preserveAspectRatio="none"` 會被拉伸,故標籤改在 Task 7 首頁以 HTML 疊放(不放 SVG 內)。此元件只負責線與點。

- [ ] **Step 2: build 驗證**

Run: `npm --prefix web run build 2>&1 | tail -2`
Expected: 成功(元件尚未被引用也應編譯過;若 tree-shake 未納入,Task 7 引用後再現於 bundle)。

- [ ] **Step 3: Commit**

```bash
git add web/src/components/site/Ridgeline.tsx
git commit -m "feat(redesign): Ridgeline SVG component (hero/divider/inline, reduced-motion)"
```

---

## Task 5: Hero 稜線資料 `home_ridgeline.json` + loader

**Files:** Create `scrapers/home_ridgeline.py`, `scrapers/build_home_ridgeline.py`, `scrapers/test_home_ridgeline.py`; Modify `web/src/lib/data-load.ts`

**Interfaces:**
- Produces `select_ridgeline(benchmarks: dict, n=8) -> list[{"label","x","y","median","finishers"}]`(x=0..n-1;y=中位秒數 min–max 正規化到 0..1;label=賽事名 rn)。
- Produces `web/public/data/v1/home_ridgeline.json` = `{ "unit": "median_finish_seconds_normalized", "nodes": [...] }`。
- Produces `loadHomeRidgeline(): Promise<{unit:string; nodes: RidgeNode[]}>`。

- [ ] **Step 1: 寫失敗測試 `scrapers/test_home_ridgeline.py`**

```python
import home_ridgeline as H


def _bm():
    # {race_key: {rn, groups: {g: {cohorts: {all: {n, bp}}}}}}
    def race(rn, n, median):
        bp = list(range(median - 50, median + 51))  # 101 pts, bp[50] == median
        return {"rn": rn, "groups": {"A": {"years": [2024], "cohorts": {"all": {"n": n, "bp": bp}}}}}
    return {
        "r1": race("小賽", 30, 3600),
        "r2": race("大賽", 500, 9000),
        "r3": race("中賽", 120, 6000),
    }


def test_select_ridgeline_picks_top_by_finishers_and_sorts_by_median():
    nodes = H.select_ridgeline(_bm(), n=2)
    # top-2 by finishers = 大賽(500), 中賽(120); sorted by median ascending
    assert [nd["label"] for nd in nodes] == ["中賽", "大賽"]
    assert [nd["x"] for nd in nodes] == [0, 1]
    assert nodes[0]["median"] == 6000 and nodes[1]["median"] == 9000
    # y normalized 0..1 across the selected set (min->0, max->1)
    assert nodes[0]["y"] == 0.0 and nodes[1]["y"] == 1.0


def test_select_ridgeline_single_race_y_is_zero_no_div_by_zero():
    nodes = H.select_ridgeline({"r": {"rn": "唯一", "groups": {"A": {"cohorts": {"all": {"n": 40, "bp": [100]*101}}}}}}, n=8)
    assert len(nodes) == 1 and nodes[0]["y"] == 0.0
```

Run: `cd scrapers && python -m pytest test_home_ridgeline.py -v` → FAIL。

- [ ] **Step 2: 實作 `scrapers/home_ridgeline.py`**

```python
"""Pick flagship races for the homepage ridgeline from the built benchmarks.
Each race contributes one node: peak height = normalized median finish time."""


def _largest_all(race):
    """The race's biggest distance/event group's `all` cohort (n, median)."""
    best = None
    for g in race.get("groups", {}).values():
        allc = g.get("cohorts", {}).get("all")
        if not allc:
            continue
        if best is None or allc["n"] > best["n"]:
            best = allc
    if best is None:
        return None
    bp = best.get("bp") or []
    median = bp[len(bp) // 2] if bp else 0
    return {"n": best["n"], "median": median}


def select_ridgeline(benchmarks, n=8):
    rows = []
    for race in benchmarks.values():
        a = _largest_all(race)
        if a is None:
            continue
        rows.append({"label": race.get("rn", ""), "median": int(a["median"]), "finishers": int(a["n"])})
    rows.sort(key=lambda r: r["finishers"], reverse=True)
    rows = rows[:n]
    rows.sort(key=lambda r: r["median"])
    meds = [r["median"] for r in rows]
    lo, hi = (min(meds), max(meds)) if meds else (0, 1)
    span = (hi - lo) or 1
    return [{"label": r["label"], "x": i, "y": round((r["median"] - lo) / span, 4),
             "median": r["median"], "finishers": r["finishers"]} for i, r in enumerate(rows)]
```

Run: `cd scrapers && python -m pytest test_home_ridgeline.py -v` → PASS。

- [ ] **Step 3: 實作 `scrapers/build_home_ridgeline.py`(讀已建置的 benchmarks.json → 寫 json)**

```python
import json, os
import home_ridgeline

HERE = os.path.dirname(__file__)
BM = os.path.join(HERE, "..", "web", "public", "data", "v1", "benchmarks.json")
OUT = os.path.join(HERE, "..", "web", "public", "data", "v1", "home_ridgeline.json")


def main():
    with open(BM, encoding="utf-8") as f:
        benchmarks = json.load(f)
    nodes = home_ridgeline.select_ridgeline(benchmarks, n=8)
    payload = {"unit": "median_finish_seconds_normalized", "nodes": nodes}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print(f"home_ridgeline.json: {len(nodes)} nodes")


if __name__ == "__main__":
    main()
```

Run:
```bash
cd scrapers && python build_home_ridgeline.py
python -c "import json;d=json.load(open('../web/public/data/v1/home_ridgeline.json',encoding='utf-8'));print(d['unit'], len(d['nodes']), d['nodes'][0])"
```
Expected: 印出 8 個節點與第一筆(label/x/y/median/finishers)。

- [ ] **Step 4: 加 loader `web/src/lib/data-load.ts`**

在 `data-load.ts`(私有 `const API = \`${base}/data/v1\``;所有 loader 皆 `async/await` 風格)加一個同風格 loader:

```ts
export interface HomeRidgeline { unit: string; nodes: { label: string; x: number; y: number; median: number; finishers: number }[]; }
export async function loadHomeRidgeline(): Promise<HomeRidgeline> {
  const r = await fetch(`${API}/home_ridgeline.json`);
  if (!r.ok) throw new Error(`home_ridgeline.json ${r.status}`);
  return r.json();
}
```

- [ ] **Step 5: 測試 + build + commit**

Run:
```bash
cd scrapers && python -m pytest test_home_ridgeline.py -q && cd ..
npm --prefix web run build 2>&1 | tail -2
```
Expected: pytest 綠;build 成功。
```bash
git add scrapers/home_ridgeline.py scrapers/build_home_ridgeline.py scrapers/test_home_ridgeline.py web/src/lib/data-load.ts web/public/data/v1/home_ridgeline.json
git commit -m "feat(redesign): home_ridgeline build (flagship races by median) + loader"
```

---

## Task 6: 全站 chrome(Base.astro header/footer 重繪)

**Files:** Modify `web/src/layouts/Base.astro`

**Interfaces:** Consumes token/font(Task 1);切換與 nav script 已存在(保留)。

- [ ] **Step 1: header wordmark 改 mono + eyebrow 感**

把 header 內的品牌連結(現為 `class="font-display text-lg…"`)改為 mono、字距、大寫感:
```astro
<a href="/" class="font-mono text-sm font-medium uppercase tracking-[0.12em] text-ink sm:text-base">TW·CYCLING·DATA</a>
```
把 `themeToggle` 按鈕文字維持既有 script 控制的 `🌙/☀️`,但 class 對齊新樣式(邊框 `border-border`、hover `text-accent` 已符合;不需改邏輯)。

- [ ] **Step 2: header 底加稜線 divider**

在 `</header>` 之前、`</nav>` 之後,加一條靜態稜線 hairline(純視覺,不需 JS 進度):
```astro
<div class="mt-2 h-px w-full bg-border"></div>
```
> 進度型稜線(隨捲動)列為 Phase 2;此處先用靜態 hairline 呼應母題,避免捲動監聽的額外複雜度(YAGNI)。

- [ ] **Step 3: footer 改 mono/座標感 + 補來源**

把 `<footer>` 內容改為(mono eyebrow + 既有三段說明保留;加 API/GitHub 連結行):
```astro
<footer class="mt-16 border-t border-border px-4 py-8 text-xs text-muted sm:px-6">
  <div class="mx-auto max-w-6xl space-y-2">
    <p class="font-mono uppercase tracking-[0.08em] text-muted">TW·CYCLING·DATA · 2009–2026 · CC BY 4.0</p>
    <p>資料來源:中華民國自行車騎士協會(cyclist.org.tw)、Bravelog 運動趣(bravelog.tw)、中華民國自由車協會(cycling.org.tw)等公開賽事成績。</p>
    <p>選手姓名已去識別化(僅顯示首尾字,如 林○宇)。本站為非營利之資料整理與視覺化;當事人如欲下架,請與本站聯絡。</p>
    <p>成績僅供參考,實際以各主辦單位公告為準。</p>
    <p class="font-mono">
      <a class="hover:text-accent" href="/api">API</a> ·
      <a class="hover:text-accent" href="/coverage">資料涵蓋</a> ·
      <a class="hover:text-accent" href="https://github.com/TTigger/tw-cycling-data">GitHub</a>
    </p>
  </div>
</footer>
```

- [ ] **Step 4: build + 瀏覽器抽查(深/淺)+ commit**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。瀏覽器開首頁,深/淺各看一次:wordmark 為 mono、footer 座標感、切換正常。
```bash
git add web/src/layouts/Base.astro
git commit -m "feat(redesign): mono wordmark + ridgeline hairline + coordinate-style footer"
```

---

## Task 7: 首頁全改 `index.astro`

**Files:** Modify `web/src/pages/index.astro`; Create `web/src/components/home/HomeHero.tsx`

**Interfaces:** Consumes `Ridgeline`(Task 4)、`loadHomeRidgeline`/`loadManifest`(Task 5 / 既有)、`OverviewApp`(既有,保留於下方)。

- [ ] **Step 1: HomeHero 島(稜線 + thesis + CTA + 即時統計 + 峰點標籤)**

`web/src/components/home/HomeHero.tsx`(自載入 island;統計來自 manifest,稜線來自 home_ridgeline;峰點 label 用 HTML 疊放於 SVG 上):

```tsx
import { useEffect, useState } from "react";
import Ridgeline from "../site/Ridgeline";
import { loadHomeRidgeline, loadManifest, type HomeRidgeline } from "../../lib/data-load";

export default function HomeHero() {
  const [rl, setRl] = useState<HomeRidgeline | null>(null);
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  useEffect(() => {
    loadHomeRidgeline().then(setRl).catch(() => setRl({ unit: "", nodes: [] }));
    loadManifest().then((m) => setStats(m.stats)).catch(() => setStats(null));
  }, []);
  const nodes = rl?.nodes ?? [];
  const fmt = (n: number) => n.toLocaleString("en-US");
  return (
    <section className="relative">
      <div className="relative h-[240px] w-full sm:h-[300px]">
        <Ridgeline variant="hero" data={nodes} height={300} ariaLabel="旗艦賽事中位完賽時間剖面" />
        {/* peak labels overlaid in HTML so text is not stretched by the SVG */}
        <div className="pointer-events-none absolute inset-0">
          {nodes.map((nd) => (
            <span key={nd.label}
              className="absolute -translate-x-1/2 translate-y-1 font-mono text-[11px] text-muted"
              style={{ left: `${(nd.x / Math.max(nodes.length - 1, 1)) * 100}%`, bottom: 0 }}>
              {nd.label}
            </span>
          ))}
        </div>
      </div>
      <p className="eyebrow mt-6">TAIWAN ROAD CYCLING · 完賽數據</p>
      <h1 className="display-xl mt-2 text-ink">台灣公路賽事,<br />十七年的完賽數據</h1>
      <p className="mt-4 max-w-[46ch] text-lg text-muted">
        查你的成績落在同齡第幾、這場多年來變快了嗎,並自由取用整份開放資料。
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <a href="/race" className="rounded-lg bg-accent px-5 py-2.5 font-medium text-bg hover:opacity-90">探索賽事 →</a>
        <a href="/api" className="rounded-lg border border-ink px-5 py-2.5 font-medium text-ink hover:border-accent hover:text-accent">取用開放資料</a>
      </div>
      {stats && (
        <p className="mt-6 font-mono text-sm tabular-nums text-muted">
          {fmt(stats.records)} 完賽 · {fmt(stats.races)} 賽事 · {stats.year_min}–{stats.year_max} · {stats.sources} 來源
        </p>
      )}
    </section>
  );
}
```
> `loadManifest` 與 `loadHomeRidgeline` 都在 `web/src/lib/data-load.ts` 匯出(同一處 import)。`manifest.stats` 型別見 `types.ts` 的 `Manifest`。CTA 主鈕用 `text-bg`(在 flamme 上為淺字)確保對比。

- [ ] **Step 2: 重排 `web/src/pages/index.astro`(hero + 3 卡 + API 帶 + 保留 OverviewApp)**

```astro
---
import Base from "../layouts/Base.astro";
import HomeHero from "../components/home/HomeHero.tsx";
import OverviewApp from "../components/overview/OverviewApp.tsx";

const cards = [
  { t: "我這場成績在同齡排第幾?", href: "/benchmark", k: "分齡對標" },
  { t: "這場賽事多年來變快了嗎?", href: "/trends", k: "長期趨勢" },
  { t: "這場難度有多高?", href: "/climbs", k: "傳奇爬坡" },
];
---
<Base>
  <HomeHero client:load />

  <hr class="hairline my-12" />

  <section>
    <p class="eyebrow">你可以…</p>
    <div class="mt-4 grid gap-4 sm:grid-cols-3">
      {cards.map((c) => (
        <a href={c.href} class="group rounded-xl border border-border bg-surface p-6 hover:border-accent">
          <p class="font-mono text-xs uppercase tracking-[0.08em] text-muted">{c.k}</p>
          <p class="mt-2 text-lg text-ink">{c.t}</p>
          <span class="mt-4 inline-block text-accent">→</span>
        </a>
      ))}
    </div>
  </section>

  <hr class="hairline my-12" />

  <section class="rounded-2xl border border-border bg-surface p-6 sm:p-8">
    <p class="eyebrow">自由取用</p>
    <h2 class="mt-2 font-display text-2xl text-ink">開放資料 · 唯讀 API · CC BY 4.0</h2>
    <p class="mt-2 max-w-[52ch] text-muted">帶 CORS 的版本化 JSON,可直接跨網域 fetch;附 Python MCP server 與可下載資料集。</p>
    <pre class="scroll-x mt-4 rounded-lg bg-bg p-3 font-mono text-xs text-ink">fetch("https://<your-domain>/data/v1/races.json").then(r =&gt; r.json())</pre>
    <div class="mt-4 flex flex-wrap gap-3 font-mono text-sm">
      <a class="text-accent hover:underline" href="/api">API 文件 →</a>
      <a class="text-accent hover:underline" href="/coverage">資料涵蓋 →</a>
    </div>
  </section>

  <hr class="hairline my-12" />

  <section>
    <p class="eyebrow">完整總覽</p>
    <div class="mt-4"><OverviewApp client:only="react" /></div>
  </section>
</Base>
```
> OverviewApp 保留在最下方 → 不損失既有總覽功能;它會自動吃新 token 翻色。

- [ ] **Step 3: build + 瀏覽器抽查(深/淺)**

Run: `npm --prefix web run build 2>&1 | tail -2`
Expected: 成功。瀏覽器開首頁:
- 深/淺各一輪:hero 稜線描繪、峰點標籤對齊、統計即時數字、CTA 對比清楚、三卡、API 帶、下方 OverviewApp 圖表翻色。
- `prefers-reduced-motion` 開啟 → 稜線靜態出現。

- [ ] **Step 4: Commit**

```bash
git add web/src/pages/index.astro web/src/components/home/HomeHero.tsx
git commit -m "feat(redesign): homepage ridgeline hero + problem cards + open-data band"
```

---

## Controller 收尾驗證(合併前)

- [ ] `npm --prefix web run build`;`grep -rl 0E1315 web/dist/_astro/*.css && grep -rl EFF1EE web/dist/_astro/*.css`(雙色都在 → 無 token stripping 回歸)。
- [ ] `cd web && npx vitest run`(ridgeline + 既有全綠);`cd scrapers && python -m pytest test_home_ridgeline.py -q`。
- [ ] 瀏覽器:**首頁深/淺各一輪**(hero 描繪、切換連動圖表翻色、無 FOUC);**至少一內頁(/race 與 /benchmark)**確認新 token 下不破版、圖表翻色、無寫死顏色殘留。
- [ ] a11y 抽查:鍵盤 focus 可見(flamme)、hero 稜線 `reduced-motion` 靜態、CTA 對比 AA。

## Self-Review

**1. Spec coverage:** 雙色 token → T1 ✅;字級/間距 helper → T1 ✅;ECharts 換色 → T2 ✅;稜線幾何 → T3 ✅;稜線元件(hero/divider/inline + reduced-motion)→ T4 ✅;hero 真實資料 + loader → T5 ✅;chrome(wordmark mono/hairline/footer 座標)→ T6 ✅;首頁全改(hero/卡/API 帶/保留 OverviewApp)→ T7 ✅;深/淺一等公民 + 切換連動圖表 → 既有機制 + T2/T7 驗證 ✅;Tailwind v4 雙色 grep 回歸 → T1/收尾 ✅;內頁不重排只驗證 → 收尾 ✅;字重免改(變數軸)→ Global Constraints 說明 ✅。progress variant 延到 Phase 2(spec 允許,YAGNI)——T6 用靜態 hairline 呼應母題,不算缺口。

**2. Placeholder scan:** 無 TBD;token/echarts/geometry/build/loader 給完整程式;元件與首頁給完整 JSX + 明確 class/token 名。`loadManifest` import 來源在 T7 註明備援。

**3. Type consistency:** `RidgeNode {x,y,label?,meta?}`(T3)被 `Ridgeline`(T4)、`HomeRidgeline.nodes`(T5 loader)、HomeHero(T7)一致使用;`ridgelinePath` 簽名一致;`select_ridgeline` 輸出鍵(label/x/y/median/finishers)與 loader 型別 `HomeRidgeline.nodes` 一致;token 名(bg/surface/border/ink/muted/accent/summit)在 T1 定義、T2/T6/T7 引用一致。
