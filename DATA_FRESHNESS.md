# 資料新鮮度週報

**產生時間 (UTC):** 2026-11-26 01:14 UTC  
**Coverage 更新時間:** 2026-11-06 13:20 +0800

---

> **⚠️ coverage 已過期 20 天：維護者 Mac 上的 launchd 排程可能沒跑或沒提交；請在 Mac 上跑 `scrapers/freshness_local.sh` 並提交 coverage.json（雲端無法代跑）**

---

## 資料摘要

| 項目 | 數值 |
|------|------|
| 完賽筆數（網站顯示） | **213,740** |
| 場次（race editions） | 320 |
| 年份範圍 | 2009–2026 |
| 收錄來源數 | 12 |

### 各來源筆數（coverage 快照，2026-11-06）

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
| **合計（完賽）** | **208,441** |

> 備註：manifest 顯示 213,740，coverage 快照 208,441；差距 5,299 筆為 coverage.json 產生後新增的成績（快照已過期 20 天）。

---

## 【NOT_INGESTED】已辦、往年有收、今年成績尚未收錄（最優先）

| 賽事 | 日期 | 來源預估 | 備註 |
|------|------|----------|------|
| 96聯賽苗栗站 仙山自行車登山賽 | 2026-10-18 | sport-result.com (Dynamic Intelligences) | 2026-11-06 查 sport-result.com 還沒有；96sporter.com 只有積分排名，無完賽時間。待 sport-result 出現後重跑爬蟲 |
| 115年全國自由車揪你123公路挑戰賽 | 2026-11-01 | cycling.org.tw / tsu | 往年由 Dynamic Intelligences 計時，成績應出現於 sport-result.com；2026-11-06 尚未公布 |

---

## 【HELD_UNCHECKED】已辦、成績未公布或找不到公開頁（優先）

| 賽事 | 年份 | 來源預估 | 備註 |
|------|------|----------|------|
| TWB台灣自行車協會 彰化騎福 | 2026 | twbike.org / score.focusline | 行事曆未寫日期；focusline / twbike.org / 網路搜尋 2026-11-06 均查無成績 |
| TIS崇越盃武嶺自行車挑戰賽（六月場次） | 2026 | bravelog.tw (e-better) | 伊貝特成績站保留 sn 6903+ (約 2026-08 以後)；6450–7120 全掃找不到，推定成績頁已下架。若主辦另公告 PDF 可補 |
| TIS石門環湖羅馬公路佛陀KOM自行車經典賽 | 2026 | bravelog.tw (e-better) | 同上，成績頁推定已下架 |
| 台灣登山大滿貫（雪巴）陽明山站 | 2026 | bravelog.tw (e-better) | 同上，成績頁推定已下架 |
| 台灣登山大滿貫（雪巴）太平山站 | 2026 | bravelog.tw (e-better) | 日期未確認；伊貝特 2026-08+ 範圍也沒有，可能已下架或今年未辦 |
| 台灣登山大滿貫（雪巴）大雪山站 | 2026 | bravelog.tw (e-better) | 同上 |
| LIVDAY 冬之湯旅 | 2026 | bravelog.tw (e-better) | 伊貝特成績頁推定已下架 |
| LIVDAY 初夏大山 | 2026 | bravelog.tw (e-better) | 同上 |
| 蘭陽百K | 2026 | focusline.com.tw | 2023/2025 由 focusline 計時已收錄；2026 年 focusline 尚無此場，往年 9 月舉辦，尚未確認是否舉辦 |
| Ciao! Wilier 2000 x Thermaltake Bicycle | 2026 | bravelog.tw (e-better) | 伊貝特成績頁推定已下架 |
| 瘋系列環台賽 | 2026 | bravelog.tw (e-better) | 同上 |
| 左營單車 挑戰百里快樂行 | 2026 | bravelog.tw (e-better) | 同上 |

---

## 【BLOCKED】有逐筆成績，但平台尚不支援

| 賽事 | 年份 | 平台 | 是否值得開爬蟲 |
|------|------|------|----------------|
| TBA第16屆雙主場輪霸西濱挑戰 | 2026 | bao-ming.com（有機器人驗證） | 值得評估（大型賽事）；2012–2015 舊成績是 taiwanbike.org 上的 xls/OneDrive 連結 |
| 台中春季繞圈賽 | 2026 | events.criterium.tw（Cloudflare 525） | 已有 criterium.tw 爬蟲；待平台恢復後重跑 |
| TCU三發國王盃中寮KOM單車挑戰賽 | 2026 | events.criterium.tw（Cloudflare 525） | 同上；TCU 2026 年成績改放此站 |
| 春季TCU台中城市繞圈賽 | 2026 | events.criterium.tw（Cloudflare 525） | 同上 |
| 全國公路錦標賽暨選拔賽(二)成績總表 | 2022 | cycling.org.tw PDF（僅每組前 8 名） | 需等協會補上完整成績冊 |
| 全國自由車公路菁英排名賽 | 2016 | cycling.org.tw PDF（僅總成績表） | 同上 |

---

## 【NOT_HELD 日期已過、該重新查】

下列條目狀態為 NOT_HELD 且 `date` 欄位已早於今日（2026-11-26），應重新確認是否已辦或成績是否公布：

| 賽事 | 日期 | 備註 |
|------|------|------|
| 96聯賽台東站 全國自由車公路錦標選拔賽 | 2026-10-31（行事曆）| 96sporter.com 官網顯示實際日期為 **2026-12-19**（報名至 11/9），行事曆日期疑有誤；辦完查 sport-result.com |
| 環騎5COOL 188K挑戰 | 2026-11-07 | 新出現於 RACE ON，辦完查驗 |
| 2026TBA四極620自行車認證 | 2026-11-13 | 往年成績在 taiwanbike.org（已有爬蟲），辦完重爬 |
| TBA 北高360/四極620/雙塔520 認證 | 2026-11-13 | 2025 年由伊貝特計時、taiwanbike.org 公布；辦完重爬 taiwanbike.org |

---

<details>
<summary>其餘項目（NOT_HELD 未來場次 / FOUND / NO_RANKING / NO_EDITION / OTHER_LEAGUE / EXCLUDED）</summary>

### NOT_HELD（預定未來場次）

| 賽事 | 預定日期 | 來源預估 |
|------|----------|----------|
| 115年全國自由車公路錦標賽暨選拔賽 | 往年 11 月下旬（2026 未確認） | cycling.org.tw |
| TWB 北高/雙塔/西三塔認證 | 往年 11 月中（2026 未確認） | twbike.org / score.focusline |
| TBA中華民國自行車協會 TBA 四極點620-超級認證（ensage） | 2026-11-13 起（ensage 行事曆） | taiwanbike.org |
| 騎士協會聯賽 S7 花蓮太平洋盃 | 2026-12-04~05 | cyclist.org.tw PDF |
| 鯉魚潭山光水色100K限時挑戰賽 | 2026-12-12 | bravelog.tw / cyclist / tsu |
| 戀戀197 | 2026-12-06 | bravelog.tw |
| 石門羅馬百K自行車挑戰賽 | 2026-12-20 | （往年 11–12 月） |
| 經典新玉門關 x EDWONDER 公路聯名賽 | 往年 11–12 月 | irunner.biji.co |
| 美利達盃單車嘉年華 | 往年 11–12 月 | irunner.biji.co |
| 輪躍台南單車嘉年華 | 往年 11–12 月 | irunner.biji.co |
| 秋季TCU台中城市繞圈賽 | 往年 11–12 月 | tsu.com.tw |
| 台中冬季繞圈賽 | 往年 11–12 月 | criterium.tw |
| 頂成ZIPP盃 府城Gravel Criterium | 往年 11–12 月 | tsu.com.tw |
| 2027瘋系列超級騎士挑戰賽 | 2027-01-01~02 | （瘋系列，恐無總排） |

### NO_RANKING（無逐筆排名，不收）

共 15 項休閒騎乘、群眾騎行或明示無總排之活動，包含：
時代騎輪節 Wheels Ride Festival、騎遊茂林輪轉山城、2027萬眾騎BIKE、屏東來義之心山嵐單車行、瘋系列白毛山巔峰騎跡、南投旅遊百K、友誼萬歲關子嶺鐵馬行（×2）、梅好騎跡咖啡探索、雙潭騎跡單車嘉義、瘋系列八卦山傳奇100K、瘋系列谷關雪見硬漢200K、明德競技樂遊騎跑、汐鴿騎行、樂遊苗栗一騎跑系列（×5）、aYa嚮導圓夢團、中央山脈極致挑戰。

### NO_EDITION（本年無此場次）

| 賽事 | 年份 | 說明 |
|------|------|------|
| 96聯賽桃竹站 | 2026 | 2026 年只有 4 站，無桃竹站 |
| 雲嘉南霸天濱海自行車賽 | 2026 | 推定停辦，iRunner 無 2026 場次 |
| GravelFundo 彰化員林 | 2026 | 2026 年系列無彰化員林站 |
| 臺灣KOM太平洋經典賽 | 2026 | 2026 年改回原賽「臺灣自行車登山王挑戰」，已收錄 |

### EXCLUDED（刻意不收）

| 賽事 | 年份 | 原因 |
|------|------|------|
| 2012輪轉花東單車嘉年華 | 2012 | 100K / 200K 名單完全相同，無法區分，暫不收 |
| 自由車公路賽國手選拔積分賽排名 | 2025 | 只有積分，無完賽時間 |
| 全國公路錦標賽暨選拔賽(二)成績總表 | 2022 | 僅每組前 8 名的總成績表（同 BLOCKED） |

</details>

---

*偵查（discover.py）與收錄（builders）都在維護者 Mac 上進行，由 launchd 排程每週一、四 08:30 台灣時間自動執行。coverage.json 由 `scrapers/freshness_local.sh` 更新後手動提交。本報告為唯讀盤點，不執行任何爬蟲或資料重建。*
