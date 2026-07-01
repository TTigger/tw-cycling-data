# Phase 2b-2:/benchmark 分布稜線 + 你的綠點 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 /benchmark 的扁平分布條換成重用 `DistributionRidge` 的完賽時間分布稜線,並把使用者時間標成松綠點;順帶為 `RidgeMarker` 加選填 `labelColor`。

**Architecture:** `DistributionRidge`(2b-1)的 `RidgeMarker` 加 `labelColor?`(markLine 標籤色);`BenchmarkTool` 用 `cohort.bp` 餵 `DistributionRidge`,markers = 中位(琴珀)+ 你(松綠、標籤也綠),移除舊扁平條。

**Tech Stack:** Astro + React islands + ECharts。

## Global Constraints

- `RidgeMarker` 加 `labelColor?: string`;markLine 標籤色 = `m.labelColor ?? colors.ink`(既有 /race 未帶 → 行為不變)。
- /benchmark 分布稜線資料 = `cohort.bp`(101 斷點,近似該 cohort 完賽時間分布);markers:中位 `bp[50]` = `colors.secondary`(cohort 一選就顯示)、你 = `secs`(輸入有效時間時)= `colors.accent` + `labelColor: colors.accent`。
- 顏色由 `useChartColors()` 於 render body 取用(翻色)。
- 只動 `DistributionRidge.tsx` + `BenchmarkTool.tsx`;不改資料、`densityRidge` 不動、不動其他頁。
- build 成功;既有 vitest 綠。

## 執行順序
單一 task(labelColor 與其唯一用途緊耦合)→ controller 收尾。

---

## Task 1: `RidgeMarker.labelColor` + /benchmark 分布稜線

**Files:** Modify `web/src/components/charts/DistributionRidge.tsx`, `web/src/components/benchmark/BenchmarkTool.tsx`

**Interfaces:** Consumes `DistributionRidge`/`RidgeMarker`(2b-1)、`useChartColors`。

- [ ] **Step 1: `DistributionRidge.tsx` 加 `labelColor`**

- `RidgeMarker` 介面加一欄:
  ```ts
  export interface RidgeMarker { value: number; label: string; color?: string; labelColor?: string; }
  ```
- markLine 的 `data.map` 內,把標籤色由固定 `colors.ink` 改為 `m.labelColor ?? colors.ink`。即該處:
  ```tsx
  label: { formatter: m.label, color: m.labelColor ?? colors.ink, position: "insideEndTop" as const },
  ```
  (`lineStyle.color: m.color ?? colors.secondary` 與其餘不動。)

- [ ] **Step 2: `BenchmarkTool.tsx` — import + colors + markers**

- 在頂部 import 區加:
  ```ts
  import DistributionRidge from "../charts/DistributionRidge";
  import { useChartColors } from "../../lib/chart-colors";
  ```
- 在 `function Tool({ data })` 的 render body(現有 `const secs = …`、`const beat = …` 附近,early return 之前)加:
  ```ts
  const colors = useChartColors();
  const ridgeMarkers = cohort ? [
    { value: cohort.bp[50], label: "中位", color: colors.secondary },
    ...(secs != null && beat != null
      ? [{ value: secs, label: "你", color: colors.accent, labelColor: colors.accent }]
      : []),
  ] : [];
  ```

- [ ] **Step 3: `BenchmarkTool.tsx` — 插入稜線、移除扁平條**

- 在「你的完賽時間」輸入的 `</label>` 區塊之後(即 `{cohort && (<label>…{stepTime} 你的完賽時間…</label>)}` 之後)插入:
  ```tsx
  {cohort && (
    <DistributionRidge values={cohort.bp} height={200} markers={ridgeMarkers} />
  )}
  ```
- 在結果框內**移除**扁平分布條那段(整段刪掉):
  ```tsx
        {/* distribution bar: P0..P100 with your marker */}
        <div className="relative h-2 rounded bg-border">
          <div className="absolute top-0 h-2 w-0.5 bg-accent"
            style={{ left: `${Math.min(100, Math.max(0, 100 - beat))}%` }} aria-hidden />
        </div>
  ```
  (結果框其餘:「你贏過 X%」、「最快…中位…最慢…」、小樣本警示,全部保留。)

- [ ] **Step 4: build + 瀏覽器抽查**

Run: `npm --prefix web run build 2>&1 | tail -2`(成功)。
瀏覽器 /benchmark 選賽事→組別→cohort **深/淺各一輪**:
- cohort 一選 → 分布稜線 + 中位(琴珀虛線)顯示;扁平條已不在。
- 輸入有效時間 → 出現**綠色「你」marker(標籤也綠)**,位置隨時間左右移、與「你贏過 X%」方向一致(時間越快越靠左)。
- 切換 🌙/☀️ → 稜線與 markers 翻色。

- [ ] **Step 5: Commit**

```bash
git add web/src/components/charts/DistributionRidge.tsx web/src/components/benchmark/BenchmarkTool.tsx
git commit -m "feat(ridge): /benchmark cohort distribution ridge with your-time marker"
```

---

## Controller 收尾(合併前)

- [ ] `cd web && npx vitest run`(既有全綠;含 densityRidge)。
- [ ] `npm --prefix web run build`(成功)。
- [ ] `grep -n "h-2 rounded bg-border" web/src/components/benchmark/BenchmarkTool.tsx`(應空——扁平條已移除)。
- [ ] 瀏覽器:/benchmark 深/淺稜線+你的綠點正常;/race 分布(2b-1)未受 labelColor 改動影響(markers 仍正常、中性標籤)。

## Self-Review

**1. Spec coverage:** DistributionRidge 取代扁平條 → Step 3 ✅;資料 = cohort.bp → Step 3 ✅;中位+你 markers → Step 2 ✅;RidgeMarker 加 labelColor 且 /race 不變 → Step 1(`?? colors.ink`)✅;移除扁平條 → Step 3 ✅;只動 2 檔 → Files ✅;翻色 → useChartColors render body ✅。

**2. Placeholder scan:** 無 TBD;labelColor 改法、markers 組法、插入/移除位置皆給具體程式與定位錨點。

**3. Type consistency:** `RidgeMarker {value,label,color?,labelColor?}`(Step 1)被 `ridgeMarkers`(Step 2)一致建構;`DistributionRidge` values 吃 `cohort.bp`(number[])符合既有簽名;`useChartColors`/`secs`/`beat`/`cohort` 皆既有。
