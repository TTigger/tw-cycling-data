# ① 爬坡指數 VAM — 設計 spec

> 日期:2026-06-11 ｜ 階段:原創分析功能(第 1 個,共 4+bonus)
> 範圍決策:**共用基礎(climb-profile 對照表)+ ① VAM**。其餘功能(②巔峰年齡曲線 ③對戰網絡 ④爬坡手vs平路手雷達 + bonus)各自一輪 spec→plan→開發。
> 前置:master 80,904 筆 / 2009–2026 / 4 來源;選手身分以 TCU/UCI ID 為錨、姓名為輔(15,301 位可追蹤);`/climbs` 傳奇爬坡頁與 `climbs.ts isClimbRace` 已存在;每場 race detail 已有遮罩名+完賽秒數。

## 目標

把不同年份、不同爬坡賽的選手放到**同一把垂直爬升的尺**上比較。核心指標 **VAM(Vertical Ascent Metres/hour,公尺/小時)= 總爬升 ÷ 完賽時數**,跨賽跨年可比;次要附「推算 W/kg」(明確標示為估計)。掛在現有 `/climbs` 頁,不開新頁、不新增 Python 管線。

## 非目標(YAGNI)

- **不做** race-type 全分類(climb/criterium/road)——那是 ④ 雷達的前置,屆時再設計。
- **不新增獨立 Python 管線檔**——單場 VAM 純前端即時算;跨賽爬坡王因需可靠選手身分,**附掛於既有 `build_athletes.py`** 產出一個小檔 `climb_vam.json`(不另開 build_climbs.py)。
- **不做** 真實功率(無 GPS/功率計/體重);W/kg 僅為公式推算。
- **不涵蓋** 沒有 profile 的爬坡賽——它們維持現有 `/climbs` 呈現。

## 身分識別取捨(關鍵)

單場 VAM 排行只需該場時間+profile,純前端即可。但**跨賽「爬坡王」必須跨賽串同一位選手**,而 `/climbs` 載入的 race detail 只有遮罩名(同名會誤併)。因此跨賽榜在 **build 時**算:`build_athletes.py` 已用 TCU/UCI ID 為錨、姓名為輔把每位選手的歷年成績歸好群——直接在該步驟 join `climb_profiles` 算每位選手在各 profile 爬坡賽的 VAM,輸出 `climb_vam.json`。如此跨賽榜用的是與選手頁同一套可靠身分,而非遮罩名。

## A. 共用基礎:climb-profile 對照表

- 檔案:`web/public/data/climb_profiles.json`(策展靜態檔,純前端載入)。
- 結構,key = `race_key`(年份無關,一條覆蓋該賽所有年份):
  ```json
  { "race_key": "<key>", "name": "臺灣KOM登山王之路",
    "dist_km": 105, "elev_m": 3275, "grade": 3.1,
    "conf": "high|est", "src": "主辦官方路線/Strava 段落" }
  ```
  - `grade`(平均斜率 %)= `elev_m / (dist_km*1000) * 100`,建表時一併算入(W/kg 公式要用)。
  - `conf`:`high`=官方/公認路線數據;`est`=由起終點海拔與里程估算(UI 註明)。
  - `src`:每條註明來源(誠實揭露)。
- 涵蓋 ~15–20 條,以本資料集實際存在的爬坡 race_key 為準(資料中有 24 條爬坡 race_key)。**不同「武嶺」分開**:
  - 臺灣KOM登山王之路(花蓮七星潭→武嶺,~105km/~3275m,conf high)
  - 臺灣KOM登山王之路-春季 / -夏季(同/部分路段,逐條核對里程,conf 視情況)
  - (TIS)崇越盃武嶺(埔里地理中心碑→武嶺,~55km/~2900m,est)
  - NeverStop武嶺 99.9K / 96聯賽武嶺站(各自核對)
  - 太平山王(宜蘭太平山)、(扶輪盃)大屯山登山王、TCU中寮KOM、塔塔加/大禹嶺等
- 海拔數字於實作時逐條以公開路線資料策展,每條標 conf+src;查無可靠數據者寧缺勿填(該賽就不算 VAM)。

## B. 計算

**B1. 純函式 `web/src/lib/vam.ts`(前後端共用邏輯,前端用 TS 版、Python 端等價實作)**
- `vam(elevM, seconds)` → 公尺/小時 = `elevM / (seconds/3600)`;`seconds<=0` 或缺 elev → null。
- `wkgEstimate(vamValue, gradePct)` → Ferrari `vam / (100 * (2 + gradePct/10))`;呼叫端負責標「推算」。
- 合理性過濾:VAM 僅保留 `100 ≤ VAM ≤ 3000`(剔除計時錯誤/未完賽異常值)。

**B2. 單場 VAM(前端即時)**:`/climbs` 選定 profile 爬坡賽 → 載入該場 race detail → 對每位完賽者套 `vam()` + `wkgEstimate()` → 排序。無需身分。

**B3. 跨賽爬坡王(build 時,`build_athletes.py` 附帶)**:對每位已歸群選手,掃其歷年成績中屬 profile 爬坡賽者,算 VAM,取最佳;輸出 `web/public/data/climb_vam.json`:
  ```json
  [{ "id": "<athlete_id>", "nm": "李○明", "best_vam": 1623, "best_wkg": 5.4,
     "climb": "臺灣KOM登山王之路", "y": 2024, "conf": "high", "g": "M" }]
  ```
  僅收 best_vam 通過合理性過濾者;`g` 供分性別排行。

## C. UI(掛 `/climbs`,新增區塊)

1. **單場 VAM 排行榜**:選一場有 profile 的爬坡賽 → 表格(遮罩名 · VAM · 推算W/kg · 完賽時間 · 車隊),預設按 VAM 降序;標頭顯示該 climb 的 dist/elev/grade/conf/src。
2. **跨賽「爬坡王」榜(主亮點)**:載入 `climb_vam.json`,每位選手跨所有 profile 爬坡賽的**最佳 VAM**,同一把尺排名(顯示在哪場/哪年達成);可選分性別(用 `g`)。身分來自 build 時的 TCU/UCI/姓名歸群(與選手頁一致)。
3. **方法論小卡**:VAM 定義、W/kg Ferrari 公式與假設、各 climb 的 conf 與 src、合理性過濾說明。
- 風格沿用 Claude 暖色 + ECharts(VAM 長條/排行),遮罩名沿用現有去識別化。

## D. 邊界與測試

- `vam.ts` 三個純函式各有 vitest(VAM 計算、W/kg 估計、bestVamByAthlete 聚合、過濾邊界)。
- profile 表載入失敗 → VAM 區塊顯示「資料準備中」不影響其餘 `/climbs`。
- 隱私:全程遮罩名,VAM 由公開完賽時間推導,無新增個資風險。

## 元件清單

- `web/public/data/climb_profiles.json`(策展資料,我策展含 conf+src)
- `scrapers/build_athletes.py`:附帶 join climb_profiles → 輸出 `web/public/data/climb_vam.json`(+ `scrapers/climb_profiles.json` 或讀 web 端同檔);+pytest 覆蓋 VAM 計算與過濾
- `web/src/lib/vam.ts`(+ `vam.test.ts`):`vam()`、`wkgEstimate()`、合理性過濾、單場排序輔助
- `web/src/lib/data-load.ts`:`loadClimbProfiles()`、`loadClimbVam()`
- `web/src/lib/types.ts`:`ClimbProfile`、`ClimbVamEntry` 型別
- `web/src/components/climbs/`:`VamLeaderboard.tsx`(單場)、`ClimbKingBoard.tsx`(跨賽)、`VamMethodology.tsx`;掛入既有 `ClimbsApp.tsx`

## 開放項(實作時定)

- `climb_profiles.json` 該由 `scrapers/` 或 `web/public/data/` 為單一真實來源(Python build 與前端都要讀)——傾向放 `web/public/data/climb_profiles.json`,Python build 直接讀同檔,避免兩份。
- 各 climb 的精確 dist/elev 與 conf 分級於策展時逐條定並註 src。
