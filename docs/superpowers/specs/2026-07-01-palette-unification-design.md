# Phase 2a:配色統一 + theme-aware 圖表 — 設計 spec

**日期**:2026-07-01
**狀態**:已核可方向,待寫實作計畫
**範圍**:把新 accent 從 flamme 紅換成**松綠**,並讓所有內頁圖表與分享卡不再寫死舊橘 `#D97757`——改由「隨主題回色」的 JS 來源驅動,使整站(不只首頁/chrome)配色一致且深/淺可翻。Ridgeline 改版 Phase 2 的第一步(2a);各頁稜線版面重排是 2b(不在本 spec)。

## 背景與動機

Phase 1 的 flamme 紅(深 `#EC3A2B`/淺 `#D23120`)是暖色打在冷柏油底上,對比最強、偏警示感,使用者覺得太搶眼。已定案換成**與冷底類比、更沉穩**的松綠。

同時 Phase 1 終審發現:約 18 個內頁圖表元件 + `share-card.ts` 在 ECharts series options 內**寫死舊 accent `#D97757`**(與舊次色 `#5B7B8A` 等)。ECharts canvas **讀不到 CSS 變數**,所以這些顏色刻意寫死;但它們**覆蓋主題、不會隨切換翻色**,換 accent 後會與新綠不一致。需給圖表一個「隨主題回色」的 JS 來源。

## 已核可決策

1. **accent = 松綠**:深 `#3DBB7A` / 淺 `#1E8A56`(淺色深一階以保 AA)。
2. **次色 = 晴曉琴珀 amber**:深 `#F2B84B`(即現有 `--summit`)/ 淺 `#B8791C`。用於雙數列圖(winner/median、A/B)與強調。
3. **heatmap 綠系漸層**:深 `#12201A → #256B48 → #3DBB7A → #7FE0AE`;淺 `#EAF3EC → #8FCDA9 → #3DBB7A → #1E8A56`。
4. **機制**:新增 `chart-colors.ts`,以共用 `useDark()` + `useChartColors()` 供 canvas 圖表取用;不在 canvas 內用 CSS 變數。
5. **share-card** 基礎 palette 換新色;**獎牌 tier 色(白金/金/銀/銅)保留不動**(那是排名色,非品牌 accent)。
6. **不動**資料管線、不改頁面版面(版面是 2b)。

## 調色盤(深/淺)

| 角色 | 深色 | 淺色 | 用途 |
|---|---|---|---|
| accent(松綠) | `#3DBB7A` | `#1E8A56` | 主數列、稜線、CTA、marker、token `--accent` |
| secondary(琴珀) | `#F2B84B` | `#B8791C` | 次數列、對比第二色 |
| muted / neutral | `#84908A` | `#5A6560` | 平手/中性(取自 `--muted`) |
| grid / axis | `#2A3538` | `#D2D8D3` | 格線/軸(取自 `--border`) |
| ink | `#ECEFEC` | `#12181A` | 圖上文字(取自 `--ink`) |
| heat ramp | `#12201A,#256B48,#3DBB7A,#7FE0AE` | `#EAF3EC,#8FCDA9,#3DBB7A,#1E8A56` | 序列熱圖(如季節 heatmap) |

多數列圖(≥3 系)沿用 `echarts-theme.ts` 的 `color[]`,領頭改為 accent(綠)→ secondary(琴珀)→ 其餘保留可辨色相。

## 架構

### `web/src/lib/chart-colors.ts`(新)
- `useDark(): boolean` — 訂閱 `themechange` 事件、讀 `document.documentElement.classList.contains("dark")`。**把目前藏在 `EChart.tsx` 內的私有 `useDark` 抽成單一來源**;`EChart.tsx` 改 import 此版(移除私有複本)。
- `chartColors(dark: boolean): ChartColors` — 純函式,回上表對應模式的 `{ accent, secondary, muted, grid, ink, heat: string[] }`。可 vitest。
- `useChartColors(): ChartColors` — `chartColors(useDark())`;元件用它取色,`themechange` 時重繪 → ECharts option 重算 → 顏色翻。

### 圖表元件遷移(18 個)
`athletes/`:AthleteCompare、AthleteProgression、AthleteRadar、CalibratedProgress。
`charts/`:AgeBoxplot、CompetitivenessSpread、FinishTimeBand、FinishTimeHistogram。
`insights/`:AgeCurve、GeoHotspots。
`overview/`:CompositionByClass、SeasonHeatmap、WomenParticipation。
`race/`:RaceDna、RaceTimeHistogram、TeamStrength。
`trends/`:AgeCompositionTrend、GenderShareTrend。

**映射規則**(把寫死 hex 換成 `useChartColors()` 的值):
- `#D97757`(舊 accent)→ `colors.accent`;`#5B7B8A`(舊次色)→ `colors.secondary`;`#6B6760`→ `colors.muted`;`#1F1E1D`/`#E8E3D9`(ink/border)→ `colors.ink`/`colors.grid`。
- heatmap 的 `inRange.color` 舊暖 ramp → `colors.heat`。
- 每個元件把取色移到 render/`useMemo(deps 含 colors)`,確保 `themechange` 重算;若元件目前 `useMemo` 未含主題相依,加入。

### `tokens.css`
- `--accent`:深 `#3DBB7A`、淺 `#1E8A56`(取代 flamme)。其餘 token 不動。首頁/CTA/chrome/Ridgeline(用 `var(--accent)`)**自動變綠**。

### `echarts-theme.ts`
- `claude`/`claude-dark` 的 `color[]` 領頭改 `[綠, 琴珀, …]`(淺:`["#1E8A56","#B8791C",…]`;深:`["#3DBB7A","#F2B84B",…]`),其餘保留可辨色相。軸/格線/文字沿用 terrain(Phase 1 已改)。

### `share-card.ts`
- line 208 的 `C = { paper, accent, ink, muted, border }` 換新色(淺底 OG 卡:`paper` 冷紙、`accent` 淺綠 `#1E8A56`、`ink`/`muted`/`border` 對齊淺色 token)。**tier 色不動。**

## 範圍邊界(YAGNI)

- 只做配色統一 + theme-aware 機制;**不改資料、不改頁面版面/佈局**(各頁稜線版面是 Phase 2b)。
- 不新增圖表;不改 ECharts 之外的視覺。
- `--summit` 已存在;次色淺色值 `#B8791C` 為新增(供 chart-colors 使用,不必新增 CSS token)。

## 測試(照 dev-workflow)

- **vitest**:`chartColors(true)`/`chartColors(false)` 回正確調色盤(accent 綠、secondary 琴珀、heat 陣列長度與端點)。
- **build**:astro build 成功;dist CSS 仍同含深底 `#0E1315` 與淺底 `#EFF1EE`(token 機制未回歸)。
- **瀏覽器抽查**:首頁(hero/CTA 變綠)+ 至少 race、trends、athletes、insights、overview 各一個含圖表的頁,**深/淺各一輪**——圖表主色為綠、次色琴珀、heatmap 綠系,且**切換 🌙/☀️ 時翻色**(不再卡舊橘)。
- **share-card**:若有產生腳本則重產一張抽查;否則檢視 `C` 值正確。

## 風險與緩解

- **元件未隨 themechange 重算**:若某元件的 `useMemo` 未含 colors 相依,顏色不會翻 → 遷移時確保取色在重繪路徑上(colors 進 deps)。
- **useDark 抽出破壞 EChart**:`EChart.tsx` 改 import 共用 `useDark` 後行為需與原本一致(同樣訂閱 `themechange`)——保持邏輯相同。
- **對比(AA)**:淺色 accent `#1E8A56`、次色 `#B8791C` 需在冷紙底達 AA;heatmap 端點在兩模式可讀。
- **share-card 為淺底**:OG 卡維持淺色(不需深色版),只換 palette。
- **色盲友善**:綠 vs 琴珀在紅綠色盲下仍可分(明度差足夠);雙數列另以線型/位置輔助既有設計。

## 未來(Phase 2b,不在本 spec)

- 各頁套稜線版面:單場完賽剖面、benchmark 你的綠點、多稜線堆疊趨勢、選手生涯稜線。
- header 隨捲動的稜線進度條。
