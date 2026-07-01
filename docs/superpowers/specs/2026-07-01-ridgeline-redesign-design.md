# Ridgeline 改版 — 設計 spec(Phase 1:token + 首頁 + 稜線元件)

**日期**:2026-07-01
**狀態**:已核可方向,待寫實作計畫
**範圍(Phase 1)**:建立新設計語言(深/淺雙色 token、字級 scale、間距節奏)+ 招牌「稜線 Ridgeline」元件 + **首頁全改** + 全站導覽/頁尾/深淺切換 + ECharts 主題換色。內頁(race/benchmark/trends/athletes/coverage)**自動繼承新 token(顏色/字體會翻)**,但其版面重排**不在本階段**,只需確認不破版。

## 背景與目標

現況被使用者評為「太樸素、字體套用不佳、缺留白」。診斷:字型檔本身可用(Fraunces/Hanken/Spline Mono/Noto TC),病灶在**套用**——字級落差平、字重弱、章節間距緊,且「暖奶油 `#FAF9F5` + 襯線」正是公認的 AI 生成三大預設之一。

方向(已與使用者定案):**方案 C「Ridgeline/稜線」**——以自行車自己的視覺母語(爬升/完賽剖面線、等高線)為招牌,深/淺雙色皆一等公民,數字交給等寬字,一條「既是裝飾也是資訊」的稜線貫穿全站。

**主體/受眾/首頁任務**:台灣公路賽事資料;車友 + 數據愛好者 + API 開發者;首頁要讓人 30 秒看懂「查我的成績 vs 全場、跨年變化、並自由取用資料」。

## 已核可決策

1. **深/淺切換按鈕**:兩種模式都是一等公民(淺色有完整配色,非附屬)。沿用既有 `html.dark` 機制。
2. **稜線母題** OK。
3. **字體分工**:保留三套字體;**Spline Sans Mono 升格為招牌字體**(數據/座標感),**Fraunces 只在少數編輯亮點**(hero 與章節引言),Hanken/Noto 內文。
4. 推進**分階段**:Phase 1 = token + 首頁 + 稜線元件 + 全站導覽/頁尾/切換 + 圖表換色;內頁版面重排留待後續階段。

## 設計語言(Design tokens)

沿用既有 `web/src/styles/tokens.css` 機制(`@theme inline { --color-*: var(--x, <light>) }` + `html { --x: <light> }` +`html.dark { --x: <dark> }` 做翻轉;字體放一般 `@theme`)。**只換值、加 token**,不改機制。CSS 註解**不得含撇號**(Tailwind v4 parser 會炸)。

### 配色

**深色(主場,terrain)**

| token | hex | 用途 |
|---|---|---|
| `--bg` | `#0E1315` | 頁面底 |
| `--surface` | `#161D20` | 面板/卡片 |
| `--line` | `#2A3538` | 等高線/邊框/分隔 1px |
| `--ink` | `#ECEFEC` | 主要文字 |
| `--muted` | `#84908A` | 次要/標籤/說明 |
| `--accent`(flamme) | `#EC3A2B` | 唯一 accent:活數據線、CTA、marker |
| `--summit` | `#F2B84B` | 極少用:紀錄/山頂高亮 |

**淺色(冷紙,一等公民)**

| token | hex | 用途 |
|---|---|---|
| `--bg` | `#EFF1EE` | 頁面底(冷灰,非奶油) |
| `--surface` | `#FFFFFF` | 面板/卡片 |
| `--line` | `#D2D8D3` | 等高線/邊框 |
| `--ink` | `#12181A` | 主要文字 |
| `--muted` | `#5A6560` | 次要/標籤 |
| `--accent`(flamme) | `#D23120` | 深一階以維持淺底對比(AA) |
| `--summit` | `#C98A1E` | 紀錄/高亮 |

既有 token 名(bg/ink/surface/border/accent/muted…)沿用並映射到上表;新增 `--summit`。現有頁面因此**自動翻新配色**。

### 字體(角色重分工,檔案不變)

| 角色 | 字體 | 處理 |
|---|---|---|
| Display / thesis | `--font-display`= Fraunces + Noto Serif TC | 僅 hero + 章節引言;weight 600;字距 −0.02em |
| **招牌:數據/標籤/eyebrow** | `--font-mono`= Spline Sans Mono | 全站數字 `font-variant-numeric: tabular-nums`;標籤大寫 + 字距 +0.04em |
| 內文 | `--font-body`= Hanken Grotesk + Noto Sans TC | 行高 1.7 |

**新增字重需求**:Fraunces 600 + Spline Mono 500/600 必須在 `scrapers/build_fonts.py` 子集輸出涵蓋(否則假粗)。build_fonts 重跑後確認 woff2 覆蓋。

### 字級 scale(fluid,新增 utilities 或 token)

| 級 | 值 | 用途 |
|---|---|---|
| display-xl | `clamp(2.75rem, 6vw, 5.5rem)` | hero thesis |
| h1 | `clamp(1.75rem, 3vw, 2.75rem)` | 章節大標 |
| h2 | `1.5rem` | 次標 |
| body | `1.0625rem` / lh 1.7 | 內文 |
| label | `0.8125rem`(mono, +0.04em, 大寫) | 標籤/eyebrow |
| stat | `clamp(2.5rem, 5vw, 4rem)`(mono tabular) | 大數字 |

### 間距節奏

4px 基準。章節上下 `clamp(4rem, 10vh, 8rem)`(補足呼吸感)。內容 `max-width: 1200px`;純文字段落 `68ch`。卡片內距 24–32px。定義 section rhythm utility(如 `.section`)供首頁與後續頁沿用;注意 Tailwind v4 選擇器 specificity,避免 `.section` 與元素選擇器互相抵銷 padding。

## 招牌元件:Ridgeline(稜線)

一條連續 SVG 折線/平滑曲線,**裝飾即資訊**。純幾何與呈現分離,可測。

### 幾何純函式(可 vitest)
`ridgelinePath(points: {x:number,y:number}[], width, height, opts?) -> { d: string, nodes: {cx,cy,...}[] }`
- 正規化到 viewport;平滑(monotone/Catmull-Rom);回 SVG path `d` 與節點座標。
- 純函式、無 DOM,vitest 對已知輸入斷言 path 起訖點與節點座標、正規化邊界。

### React/Astro 元件 `Ridgeline`
- Props:`variant: 'hero' | 'divider' | 'progress' | 'inline'`、`data: RidgelineNode[]`、`height`、`interactive?`、`labels?`。
- `hero`:flamme 描邊 + 節點圓點 + 真實賽事標籤;載入時 `stroke-dashoffset` 由左至右描繪、節點依序點亮。
- `divider`:單條 `--line` 細等高線,取代生硬 `<hr>`。
- `progress`:header 底的細稜線,寬度隨捲動百分比填成 flamme。
- `inline`:嵌在卡片/圖表旁的小剖面(如 benchmark 你的紅點)。
- `prefers-reduced-motion` → 不描繪、直接靜態;`interactive` 時 hover 節點顯示該賽事 tooltip(鍵盤可聚焦)。

### hero 資料來源(真實、誠實)
新增 build 步驟輸出 `web/public/data/v1/home_ridgeline.json`:挑選 N(約 6–10)場**旗艦賽事**(依完賽數排序取代表性賽事),每場一個節點,`x` = 依序索引、`y` = 該賽事**正規化中位完賽時間**(各賽事中位秒數,min–max 正規化到 0–1),UI 明標「峰高 = 中位完賽時間(越高越久)」。線 = 這些賽事串起的「地形」。純建置期產物,不動 master/dataset。

### 等高線紋理(克制)
大數字背後極淡 `--line` 等高線(CSS repeating-gradient 或輕量 SVG),透明度低;**只點綴,不滿版**(避免落回戶外品牌俗套)。

## 首頁版面(全改)

```
┌────────────────────────────────────────────────────────────┐
│ TW·CYCLING·DATA   賽事 選手 對標 趨勢 API 資料   ☾/☀  GitHub │  Header
│ ╌╌╌╌╌ Ridgeline variant=progress(捲動進度)╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌ │
├────────────────────────────────────────────────────────────┤
│  台灣公路賽事·十七年的完賽數據          ╱╲   ╱╲╱╲            │  Hero
│  查你的成績落在同齡第幾、這場多年變快了嗎  ●武嶺 ●日月潭 ●…    │  (Ridgeline hero)
│  [探索賽事→(flamme)] [取用開放資料(ghost)]                  │
│  147,600 完賽 · 126 賽事 · 2009–2026 · 8 來源  (mono 一行)   │
├──── Ridgeline divider ─────────────────────────────────────┤
│  你可以…(問題導向 3 卡:分齡對標 / 長期趨勢 / 難度)          │  Section 2
├────────────────────────────────────────────────────────────┤
│  ▸ 試玩:挑一場賽事 [武嶺▾][130K挑戰▾] → 該組冠軍/中位 + 小剖面│  Section 3(展示正規化)
├────────────────────────────────────────────────────────────┤
│  ▸ 趨勢一瞥:女性完賽佔比 / 分齡組成                          │  Section 4
├────────────────────────────────────────────────────────────┤
│  ▓ 自由取用 ▓(全寬深帶):fetch 範例 + CC BY 4.0             │  Section 5
│  [API 文件] [MCP server] [下載資料集]                        │
├────────────────────────────────────────────────────────────┤
│  footer(mono 座標感):8 來源 · 授權 · GitHub · PDPA         │  Footer
└────────────────────────────────────────────────────────────┘
```

- **Hero thesis**:不用「大數字+小標」模板;主角是 Ridgeline hero(線即內容)。文案主動語氣、問題導向。
- **Section 3** 直接用既有分組正規化資料(races + race_crossyear),秀「同賽事不同距離的冠軍/中位」——把最近做的正規化當賣點。
- **Section 5** 呼應 /api,深色全寬帶。

## 全站導覽 / 頁尾 / 切換

- **Header**:左 wordmark(mono);中導覽(賽事/選手/對標/趨勢/API/資料);右 **深淺切換(沿用既有 🌙,重繪為 ☾/☀)** + GitHub;底 Ridgeline progress。手機收合為漢堡。
- **切換**:沿用既有 `html.dark` + no-flash;確認首屏無 FOUC(必要時保留/加 inline 前置腳本)。切換要連動 ECharts 主題(既有 `themechange` 事件 + `EChart.tsx` `key={theme}`)。
- **Footer**:mono、座標風;來源站名+連結(呼應 /coverage)、授權、API/MCP、隱私 PDPA。

## 元件皮膚慣例(本階段先套首頁,全站可用)

- **表格**:無斑馬紋;列間 1px `--line`;數字 mono tabular 右對齊;表頭 mono 大寫小字。
- **卡片**:`--surface` + 1px `--line`,**無重陰影**;hover 才浮 flamme 細邊。
- **按鈕**:主 = flamme 實心;次 = ink ghost 外框;focus 用 flamme 外框(鍵盤可見)。
- **ECharts**:更新 `web/src/lib/echarts-theme.ts` 的 `claude`/`claude-dark`——active line = flamme、格線 = `--line`、文字 = `--ink`、軸字型 = mono。**不得**在 chart options 內寫死顏色(否則不翻)。

## 範圍邊界(YAGNI / 誠實)

- **Phase 1 交付**:tokens(雙色)+ 字級/間距 + Ridgeline 元件(+ home_ridgeline build)+ 首頁全改 + header/footer/切換 + ECharts 換色 + build_fonts 補字重。
- **不在本階段**:race/benchmark/trends/athletes/coverage 的**版面重排**(它們自動繼承新配色/字體,但 bespoke 佈局後續階段再做)。
- **不動**:資料管線、master/dataset、API 結構、頁面資料邏輯。
- 內頁只需**驗證不破版**(深/淺都要看)。

## 測試(照 dev-workflow)

- **vitest**:`ridgelinePath` 幾何純函式(已知點 → path 起訖/節點座標/正規化邊界);首頁若有互動純函式(如 hero 節點挑選)一併測。
- **build + token 驗證**:astro build 成功;`grep` dist CSS **同時**含淺底 `#EFF1EE` 與深底 `#0E1315`(沿用既有雙色存在檢查,防 Tailwind v4 stripping 回歸)。
- **瀏覽器抽查**:首頁**深/淺各一輪**(hero 稜線描繪、切換連動圖表翻色、無 FOUC);至少一個內頁(如 /race)確認新 token 下不破版、圖表翻色。
- **a11y**:鍵盤 focus 可見(flamme)、對比 AA(尤其淺色 flamme/muted)、`prefers-reduced-motion` 稜線靜態、圖表有數字表替代。

## 風險與緩解

- **Tailwind v4 token stripping 回歸**:嚴格沿用 `@theme inline + var() fallback + html.dark` 三段式;dist CSS 雙色 grep 把關。CSS 註解不得含撇號。
- **主題閃爍(FOUC)**:確認/補首屏 inline 腳本在 paint 前設 `html.dark`。
- **字重子集**:build_fonts 未含 Fraunces 600 / Mono 500–600 會假粗;重跑並抽查 woff2。
- **Ridgeline 資料誠實**:hero 節點語意(中位時間 or 難度)須在 UI 標明,勿誤導;純建置產物。
- **等高線過度**:只當 hairline/極淡背景,避免滿版壁紙俗套。
- **內頁色彩回歸**:少數頁可能寫死顏色 → 換 token 後不翻;逐頁深/淺抽查。

## 未來階段(不在本 spec)

- Phase 2+:race/benchmark/trends/athletes/coverage 各自套 Ridgeline 版面(單場剖面、你的紅點、多稜線堆疊、個人成績稜線、來源圖例)。
- 進階:scrollytelling 敘事(The Pudding 風);hero 稜線 3D/互動深化。
