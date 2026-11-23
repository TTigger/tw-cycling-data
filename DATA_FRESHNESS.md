# 資料新鮮度週報

> **產生時間 (UTC):** 2026-11-23 01:15 UTC  
> **coverage.json 更新時間:** 2026-11-06 05:20 UTC（最後 commit）

---

**⚠️ coverage 已過期 17 天：維護者 Mac 上的 launchd 排程可能沒跑或沒提交；請在 Mac 上跑 `scrapers/freshness_local.sh` 並提交 coverage.json（雲端無法代跑）**

---

## 摘要

| 項目 | 數值 |
|------|------|
| 完賽筆數（網站顯示） | **213,740** |
| 場次數（manifest.races） | 224 |
| 版本數（race_editions） | 320 |
| 年份範圍 | 2009–2026 |
| 來源數 | 12 |

### 各來源完賽筆數

| 來源 | 筆數 |
|------|------|
| bravelog.tw | 43,423 |
| irunner.biji.co | 42,441 |
| cyclist.org.tw | 36,885 |
| tsu.com.tw | 24,515 |
| taiwanbike.org | 18,204 |
| twbike.org | 15,404 |
| focusline.com.tw | 7,644 |
| atsport.com.tw | 7,385 |
| cycling.org.tw | 4,104 |
| e-better.com.tw | 4,074 |
| sport-result.com | 3,539 |
| criterium.tw | 823 |

---

## 缺漏清單

### 【NOT_INGESTED】已辦、往年有收、今年成績尚未進來 ⬅ 最優先（2 筆）

| 賽事 | 日期 | 推測來源 | 備註 |
|------|------|----------|------|
| 96聯賽苗栗站 仙山自行車登山賽 | 2026-10-18 | sport-result.com | 96聯賽 苗栗站已辦；計時 Dynamic Intelligences，sport-result.com 2026-11-06 尚未公布；出現後重跑 sport-result 爬蟲 |
| 115年全國自由車揪你123公路挑戰賽 | 2026-11-01 | cycling.org.tw / tsu | 2026-11-01 已辦；Dynamic Intelligences 計時，待 sport-result.com 公布 |

---

### 【HELD_UNCHECKED】已辦、成績尚未公布或找不到公開頁 ⬅ 優先（12 筆）

| 賽事 | 來源行事曆 | 備註 |
|------|-----------|------|
| TWB台灣自行車協會 彰化騎福 | ensage2026 | 無日期；twbike.org、score.focusline 及網路搜尋均查不到成績（2026-11-06）|
| TIS崇越盃武嶺自行車挑戰賽（六月場次） | known_races | 伊貝特成績站保留 sn 6903+ 以後場次，2026-06 場次頁已下架；主辦若另公告 PDF 可補 |
| TIS石門環湖羅馬公路佛陀KOM自行車經典賽 | known_races | 同上，伊貝特成績頁已下架 |
| 台灣登山大滿貫（雪巴）陽明山站 | known_races | 同上，伊貝特成績頁已下架 |
| 台灣登山大滿貫（雪巴）太平山站 | known_races | 往年在 Bravelog（伊貝特計時）；2026 日期未確認，伊貝特全掃找不到 |
| 台灣登山大滿貫（雪巴）大雪山站 | known_races | 同上 |
| LIVDAY 冬之湯旅 | known_races | 伊貝特成績頁已下架 |
| LIVDAY 初夏大山 | known_races | 伊貝特成績頁已下架 |
| 蘭陽百K | known_races | 2023/2025 由 focusline 計時已收；2026 年 focusline 尚未列出，未確認是否舉辦 |
| Ciao! Wilier 2000 x Thermaltake Bicycle | known_races | 伊貝特成績頁已下架 |
| 瘋系列環台賽 | known_races | 伊貝特成績頁已下架 |
| 左營單車 挑戰百里快樂行 | known_races | 伊貝特成績頁已下架 |

---

### 【BLOCKED】有逐筆成績、但平台尚不支援（6 筆）

| 賽事 | 平台 | 值得開爬蟲？ |
|------|------|------------|
| TBA中華民國自行車協會 第16屆雙主場輪霸西濱挑戰 | bao-ming.com（有機器人驗證，不繞過）| 值得：TBA 官方大型賽事，2012–2015 舊成績是 taiwanbike.org xls/OneDrive |
| 台中春季繞圈賽 | events.criterium.tw（Cloudflare 525，2026-11-06 仍連不上）| 值得：criterium 主站已恢復，待 events 子域恢復後重跑 criterium 爬蟲 |
| TCU三發國王盃中寮KOM單車挑戰賽 | events.criterium.tw（同上）| 同上 |
| 春季TCU台中城市繞圈賽 | events.criterium.tw（同上）| 同上 |
| 全國公路錦標賽暨選拔賽（二）2022 | cyclist.org.tw 下載區 PDF（1 頁總成績，每組前 8 名）| 待協會補上完整成績冊 |
| 全國自由車公路菁英排名賽 2016 | cyclist.org.tw 下載區 PDF（1 頁總成績）| 待協會補上完整成績冊 |

---

### 【NOT_HELD 日期已過】行事曆日期已過，應重新查詢（4 筆）

| 賽事 | 行事曆日期 | 備註 |
|------|-----------|------|
| 96聯賽台東站 全國自由車公路錦標選拔賽 | 2026-10-31 | ⚠️ 96sporter.com 官網標示實際日期為 2026-12-19（報名至 11/9）；可能行事曆日期有誤，請確認 |
| 環騎5COOL 188K挑戰 | 2026-11-07 | 新出現於 RACE ON，辦完查驗 |
| 2026TBA四極620自行車認證 | 2026-11-13 | 往年成績在 taiwanbike.org（已有爬蟲），辦完重爬 |
| TBA 北高360/四極620/雙塔520 認證 | 2026-11-13 | 同上（known_races 重複條目）|

---

<details>
<summary>其餘項目（NOT_HELD 未來場次、NO_RANKING、NO_EDITION、EXCLUDED）</summary>

### NOT_HELD（尚未辦，辦完再查）

| 賽事 | 預計日期 | 來源 |
|------|---------|------|
| TBA中華民國自行車協會 TBA 四極點620-超級認證（ensage2026）| 2026-11-13 起 | taiwanbike.org |
| TWB 北高/雙塔/西三塔認證 | 往年 11 月中 | twbike.org / score.focusline |
| 115年全國自由車公路錦標賽暨選拔賽 | 往年 11 月下旬 | cycling.org.tw |
| 騎士協會聯賽 S7 花蓮太平洋盃 | 2026-12-04~05 | cyclist.org.tw PDF |
| 鯉魚潭山光水色100K限時挑戰賽 | 2026-12-12 | Bravelog / cyclist / tsu |
| 戀戀197 | 2026-12-06 | bravelog.tw |
| 石門羅馬百K自行車挑戰賽 | 2026-12-20 | — |
| 經典新玉門關 x EDWONDER 公路自行車聯名賽 | 往年 11–12 月 | irunner.biji.co |
| 美利達盃單車嘉年華 | 往年 11–12 月 | irunner.biji.co |
| 輪躍台南單車嘉年華 | 往年 11–12 月 | irunner.biji.co |
| 秋季TCU台中城市繞圈賽 | 往年 11–12 月 | tsu.com.tw |
| 台中冬季繞圈賽 | 往年 11–12 月 | criterium.tw |
| 頂成ZIPP盃 府城Gravel Criterium | 往年 11–12 月 | tsu.com.tw |
| 2027瘋系列超級騎士挑戰賽 | 2027-01-01~02 | — |
| 2027萬眾騎BIKE | 2027-03-20 | — |
| TBA 北高360/四極620/雙塔520 認證 | 2026-11-13 | taiwanbike.org |

### NO_RANKING（無逐筆排名，不收）

2026時代騎輪節 Wheels Ride Festival、騎遊茂林 輪轉山城自行車活動、屏東來義之心山嵐單車行、瘋系列 白毛山巔峰騎跡、南投旅遊百 K 挑戰、友誼萬歲〜關子嶺鐵馬行、雲林單車遊-梅好騎跡 咖啡探索之旅、友誼萬歲 關子嶺鐵馬行、雙潭騎跡 單車嘉義、瘋系列 八卦山傳奇100K限時挑戰賽、瘋系列 第二屆台灣瘋系列 谷關雪見硬漢200K限時挑戰賽、明德競技 環湖饗宴-樂遊騎跑啟航、Lydia & 欣欣「探索汐鴿」E起騎!、樂遊苗栗一騎跑系列（aYa、VJ、Doris、Tracy 等多場次）、中央山脈極致挑戰、aYa 西進武嶺圓夢團（共約 15 筆）

### NO_EDITION（2026 無此站次）

96聯賽桃竹站、雲嘉南霸天濱海自行車賽、GravelFundo 彰化員林、臺灣KOM太平洋經典賽

### EXCLUDED（刻意不收）

| 賽事 | 年份 | 原因 |
|------|------|------|
| 2012 輪轉花東單車嘉年華 | 2012 | ATSport 100K 與 200K 兩組返回完全相同名單，無法分辨 |
| 自由車公路賽國手選拔積分賽排名 | 2025 | 只有積分、無完賽時間 |
| 全國公路錦標賽暨選拔賽（二）成績總表 | 2022 | 1 頁僅每組前 8 名，無逐人成績 |

</details>

---

## 說明

偵查（freshness_local.sh → discover.py）與成績收錄（scrapers/）**均在維護者 Mac 上進行**，本雲端代理只整理已提交的 coverage.json 並開 PR 提醒。若需更新 coverage 資料，請在 Mac 上執行 `bash scrapers/freshness_local.sh` 後提交 `web/public/data/v1/coverage.json`。
