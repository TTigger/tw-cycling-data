# 台灣公路車賽事成績儀表板 — 設計文件 (Phase 2)

> 日期:2026-06-04 ｜ 狀態:設計待使用者確認
> 上游:Phase 1 master 資料集(`data/processed/master_2024_2026.public.json`,33,051 筆 / 47 場 / 20 系列 / 2024–2026)

## 1. 目標與對象

公開給**台灣公路車車友社群**的互動式成績探索儀表板。讓使用者依年份/系列/賽事/組別/性別/分齡組篩選,觀察**完賽時間、成績、組別、(分齡)年齡**的分布與趨勢,並提供幾個有原創性的洞察(競爭強度、跨年變化、爬坡全民分布、percentile 查詢)。

- **平台**:Vercel 純靜態網頁(零後端)。
- **裝置**:RWD,手機可用(社群多用手機)。
- **語言**:繁體中文為主。
- **質感**:Claude 暖色簡潔風(非一般 AI/SaaS 觀感)。

### 成功標準
1. 任一篩選組合下,所有圖在 <300ms 內於瀏覽器端重算更新。
2. 首頁首屏在 4G 手機 <3s 可互動(資料分檔 + lazy)。
3. 每張圖都誠實標註資料來源與涵蓋率,不誤導。
4. 個資合規:對外只用去識別化資料,姓名顯示 `李○○`。

## 2. 範圍

**In scope(Phase 2)**:下述 4 頁、12 個圖/視圖、全域篩選與圖表聯動、資料建置管線、視覺系統、RWD。
**Out of scope(後續)**:選手跨賽事歷年追蹤(Phase 3,需 UCI ID / 身分匹配)、歷史回填 2014–2023(Phase 1c)、cycling.org.tw 國家級源(Phase 1d)。儀表板資料層設計需**預留**這些擴充(見 §5、§9)。

## 3. 頁面結構與 12 個圖/視圖

### 頁 A — 總覽 (Overview)
- **KPI 卡**:總成績筆數、賽事數、系列數、涵蓋年份。
- **C9 賽季行事曆熱力圖**:月份 × 賽事數/人次。(date 100%;旺季 9/11/6 月,7–8 月低谷)
- **參賽人數趨勢**(核心圖 3):逐年 × 系列,折線/堆疊長條。
- **C10 女子參與度**:各系列女子佔比長條(L'Étape 24% vs 其他 ~10%)。
- **組別/性別組成**(核心圖 4):堆疊長條。

### 頁 B — 探索 (Explore) — 全域篩選 + 圖表聯動
- **核心圖 1 完賽時間分布**:直方圖(可切換 race_class/組別疊圖)。
- **核心圖 2 分齡組 vs 完賽時間**:箱型圖(標註「僅有分齡組的賽事,涵蓋 ~11%」)。
- **C7 賽事競爭強度/離散度**:每場「冠軍→中位數→末位」拉開倍數(蜂巢/箱型排行;排除認證型)。
- **C11 距離 vs 平均速度**:散點(用組別名抽出的距離,涵蓋 48%,標註)。
- 點任一圖元素 → 更新全域篩選 → 其他圖連動重算。

### 頁 C — 賽事詳情 (Race detail) — 選一場賽事
- **排行榜表**:名次/號碼/姓名(遮罩)/組別/性別/車隊/完賽時間,分頁、可依組別篩。
- **C5 percentile 查詢「你贏過多少%」**:輸入時間+組別 → 該場 percentile。
- **該場完賽時間分布** + **領獎台 podium**。
- **C6 同賽事跨年「變快了嗎」**:若該賽 race_key 有多年(9 場符合)→ 冠軍/中位數時間逐年折線。
- **C12 車隊戰力榜**:若為競技型(有 team,cyclist)→ 各車隊前十/領獎台次數。

### 頁 D — 招牌:傳奇爬坡 (Featured: 武嶺/KOM)
- **C8 武嶺/KOM 爬坡全民時間分布**:聚焦武嶺(3275m)等傳奇爬坡賽,全民完賽時間分布 + percentile widget。為對外亮點頁。

## 4. 互動與狀態

- **全域篩選器**:年份、系列、賽事、race_class(競賽/市民/挑戰/分齡/青少年/團體/電輔車)、性別、分齡組。
- **聯動**:單一共用篩選狀態(React context / 輕量 store);ECharts `click`/`brush` 事件 → 更新狀態 → 訂閱的圖重算。URL query 同步(可分享篩選後的視圖)。
- **空資料/低涵蓋**:篩選後若某圖資料不足(如分齡組為空)→ 顯示「此條件下無分齡資料」而非空白。

## 5. 資料層(關鍵)

master 原始 ~30MB,**不整包進瀏覽器**。建置時(Python,沿用現有 `scrapers/`)產出兩種檔:

1. **精簡視覺化資料集** `public/data/viz.json`(或 `.json.gz`):每筆只留圖表欄位,目標壓縮後 <1.5MB,瀏覽器載入後在記憶體即時篩選/聚合。
   欄位(短鍵):`rk`(race_key)`rn`(賽名)`y`(年)`mon`(月)`s`(系列)`rc`(race_class)`cat`(組別)`g`(性別)`ag`(分齡組)`t`(完賽秒)`rank`(名次)`dist`(km,可得時)`spd`(均速,可得時)`plat`(來源)`reg`(地區)。
2. **單場詳細檔** `public/data/race/<race_key>__<year>.json`:含 `name_masked`/`team`/`bib`/`splits`,供賽事詳情頁排行榜 lazy load。
3. **賽事索引** `public/data/races.json`:race_key、賽名、年份、系列、人數、是否多年、是否有 team — 供清單/路由。

> 新增建置腳本 `scrapers/build_viz.py`(讀 master.public → 產上述檔;含距離抽取、均速計算、月份)。`uci_id` 欄位預留(Phase 1d/3 接上)。

## 6. 技術棧(已選定)

- **Astro + React islands + Tailwind**(與 Tiglet 同棧;靜態為主,互動圖以 island 載入)。
- **ECharts**(`echarts-for-react`):canvas 渲染,33k 散點不卡,內建 zoom/brush/tooltip/聯動。
- **Vercel** 靜態部署。
- 狀態:輕量(React context 或 nanostores);URL 同步用原生 `URLSearchParams`。

## 7. 視覺系統(已選定:Claude 暖色簡潔)

- **配色**:底 `#FAF9F5`、卡片 `#FFFFFF`、暖灰邊 `#E8E3D9`、文字 `#1F1E1D` / 次要 `#6B6760`、重點(陶土珊瑚)`#D97757`;圖表副色:低彩藍灰 `#5B7B8A`、鼠尾草綠 `#7C8C6B`、暖灰階。
- **字體**(自架,Google Fonts/Fontshare):標題 **Fraunces**;內文 **Hanken Grotesk**;中文 **Noto Serif TC**(標題)+ **Noto Sans TC**(內文);數字 **Spline Sans Mono**。避開 Inter/Roboto/system 預設。
- **元件**:圓角卡片、充足留白、細暖灰分隔線、克制的動效。

## 8. RWD / 效能 / 無障礙 / 隱私

- **RWD**:手機篩選器收進抽屜;圖表單欄堆疊;表格橫向捲動;觸控友善 tooltip。
- **效能**:viz.json 壓縮 + 首屏只載總覽所需;ECharts 圖表 lazy mount(進視窗才 render);字體 subset(含常用中文)。
- **無障礙**:語意化、鍵盤可操作篩選器、色彩對比達標、圖表附文字摘要/資料表替代。
- **隱私(PDPA)**:只用 `*.public.json`(無 `name_raw`);顯示 `name_masked`;頁尾說明資料來源與下架聯絡方式。

## 9. 檔案結構(規劃)

```
web/                      (Astro 專案)
  src/pages/  index/explore/race/[key]/climbs
  src/components/  charts/(各 ECharts 封裝) filters/ cards/
  src/lib/  data-load.ts  filter-store.ts  format.ts(時間/percentile)
  src/styles/  tokens.css(色彩/字體 token)
  public/data/  viz.json  races.json  race/*.json
scrapers/build_viz.py     (master.public → web/public/data/*)
```

## 10. 資料限制(每圖標註)

- 性別:cyclist 83% / Bravelog 17%(多數市民賽不分組)。
- 分齡組:整體 11%(主要競技型)。→ 箱型圖明示涵蓋。
- 距離/均速:48% 可得;均速混合爬坡/平路,需分賽別解讀。
- 車隊:僅 cyclist(8%)。
- 地區:僅 Bravelog(縣市)。
- 認證型(TBA 雙塔/北高):無名次競賽意義,離散度圖排除。

## 11. 後續擴充(預留,不在本期)

- Phase 1c 歷史回填 2014–2023、Phase 1d cycling.org.tw(含 **UCI ID**)→ 同 schema 併入,圖自動涵蓋更長年份。
- Phase 3 選手歷年追蹤:以 UCI ID 為主鍵,新增「選手頁」(歷年成績曲線)。資料層已預留 `uci_id`。

## 12. 已定案決定

- **武嶺/KOM 傳奇爬坡 = 獨立頁(頁 D)**。(使用者確認 2026-06-04)
- **總覽 KPI 用「成績筆數/人次」**(非去重人頭,因無穩定選手 ID;Phase 3 接 UCI ID 後再加去重人數)。(使用者確認 2026-06-04)
- 專案以 `tw-cycling-data` 為根做 **git 版控**。(使用者確認 2026-06-04)
