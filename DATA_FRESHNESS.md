# 🩺 資料新鮮度週報

**產生時間（UTC）：2026-07-06 01:05 UTC**
**coverage.json 最後更新：2026-06-30 04:28 UTC**（距今約 **6 天**，新鮮度正常）

---

## 涵蓋摘要

### 已收錄成績（coverage.json）

| 項目 | 數值 |
|------|------|
| 已收錄成績筆數 | **118,501** |
| 場次數（races） | **130** |
| 年份範圍 | 2009 – 2026 |
| 海外賽事筆數 | 8,724 |

| 來源平台 | 筆數 |
|----------|------|
| bravelog.tw | 46,553 |
| irunner.biji.co | 32,862 |
| tsu.com.tw | 24,515 |
| cyclist.org.tw | 12,265 |
| criterium.tw | 1,957 |
| cycling.org.tw | 349 |

### 全資料集（master_summary.json，含 twbike.org / taiwanbike.org）

| 項目 | 數值 |
|------|------|
| 資料庫總筆數 | **147,609** |
| 不同場次數 | **161** |
| 年份 | 2009 – 2026 |

額外平台（未納入 coverage tracking）：twbike.org **15,405** 筆、taiwanbike.org **18,204** 筆

---

## 缺漏清單總覽（共 44 場）

| 分類 | 場數 | 說明 |
|------|------|------|
| 🔍 **尚未調查** | **0** | 全部已調查 |
| 🚧 **BLOCKED（有成績·平台待支援）** | **7** | 可行動的潛在新資料源 |
| ⏳ NOT_HELD | 5 | 尚未舉辦，辦完再查 |
| ❌ NO_RANKING | 30 | 確認無逐筆排名，不可爬 |
| 🔀 OTHER_LEAGUE | 2 | 行事曆誤標為其他聯賽 |

---

## 【尚未調查】— 0 場

> 本週全數調查完畢，無待查場次。

---

## 🚧【BLOCKED — 有成績，平台待支援】— 7 場

這些賽事**有逐筆名次與成績**，但成績儲存在目前本站尚未支援的平台，是最值得評估開新爬蟲的線索。

### 平台一：twbike.org PDF + score.focusline（5 場）

| 賽事 | 行事曆 | 備註 |
|------|--------|------|
| TWB台灣自行車協會 第4屆東三塔550 | ensage2026 | twbike.org PDF + score.focusline |
| TWB台灣自行車協會 第4屆東雙塔470 | ensage2026 | twbike.org PDF + score.focusline |
| TWB台灣自行車協會 彰化騎福 | ensage2026 | twbike.org PDF + score.focusline |
| TWB台灣自行車協會 北高360 | ensage2026 | twbike.org PDF + score.focusline |
| TWB東三塔＆雙塔 | ensage2026 | twbike.org PDF + score.focusline |

**評估建議：**
- `score.focusline` 為獨立計時平台，需確認是否有可爬取的 HTML 成績頁。若有，可開新 scraper。
- twbike.org 已部分支援（北高360、雙塔等舊年度已收錄），但新賽季成績若以 PDF 發布則需 `pdfplumber` 解析。
- 此 5 場屬同一主辦（TWB台灣自行車協會），批次爬取效益高。

### 平台二：taiwanbike.org Google Sheets（2 場）

| 賽事 | 行事曆 | 備註 |
|------|--------|------|
| TBA中華民國自行車協會 第16屆雙主場輪霸西濱挑戰 | ensage2026 | taiwanbike.org Google Sheets |
| 輪霸西濱 五大重點 降低雨天騎乘風險 | ensage2026 | taiwanbike.org Google Sheets |

**評估建議：**
- taiwanbike.org 已支援（18,204 筆），但此兩場以 Google Sheets 公開成績，格式不同。
- 若 Sheets 公開，可用 `/export?format=csv` 或 Sheets API 匯出解析，無需新平台 scraper，僅需擴充 ingest 邏輯。
- 兩場為同一系列（輪霸西濱），**值得支援**（西濱挑戰規模大，往年有數百筆）。

---

## ⏳【NOT_HELD — 尚未舉辦】— 5 場

<details>
<summary>展開查看（辦完後再調查）</summary>

| 賽事 | 行事曆 | 預定日期 | 備註 |
|------|--------|----------|------|
| 瘋系列 無眠征途 夜騎日月潭限時挑戰賽 | raceon2026 | 2026-07-18 | 瘋系列限時挑戰，完賽後恐無總排，屆時查驗 |
| 第一屆極限東征_瘋911 | raceon2026 | 2026-09-11 | 瘋系列，恐無總排 |
| 台灣瘋系列 小台灣縮時環島顛峰300K限時挑戰賽 | raceon2026 | 2026-09-26 | 瘋系列 300K，恐無總排 |
| TIS桃園台南280KM雙城挑戰賽 | raceon2026 | 2026-10-31 | 往屆僅發完賽獎座/證書，恐無排名 |
| 騎士協會聯賽 S7 花蓮太平洋盃 | ensage2026 | 2026-12-04~05 | 聯賽末站，辦完應有 cyclist.org.tw PDF 成績 |

</details>

---

## ❌【NO_RANKING — 無逐筆排名】— 30 場

<details>
<summary>展開查看（已確認不可爬）</summary>

| 賽事 | 行事曆 | 原因摘要 |
|------|--------|----------|
| 超越巔峰-中央山脈極致挑戰 | raceon2026 | 多日極致挑戰：僅完賽英雄榜/關門時間 |
| 2026南投旅遊百K自行車挑戰 | raceon2026 | 休閒小鎮漫遊，無排名 |
| Light One Bike 系列 - 生態遊程 | raceon2026 | 低碳慢遊生態團騎，明示非競賽 |
| 2026時代騎輪節 Wheels Ride Festival | raceon2026 | 計時僅供參考，明示非競賽 |
| 瘋系列第七屆中雙塔 | raceon2026 | 無總排 + ATSport（封鎖） |
| Light One Bike 系列 - 長距離挑戰 | raceon2026 | 低碳慢遊生態團騎，明示非競賽 |
| 屏東來義之心山嵐單車行 | biji2025 | 休閒團騎，查無成績頁 |
| 瘋系列 白毛山巔峰騎跡 | biji2025 | 完賽獎牌制，無總排 + ATSport |
| 南投旅遊百 K 挑戰 | biji2025 | 休閒小鎮漫遊，無排名 |
| 友誼萬歲〜關子嶺鐵馬行 | biji2025 | 休閒團騎（lohasnet），無排名 |
| 雲林單車遊-梅好騎跡 咖啡探索之旅 | biji2025 | 休閒團騎；2025 停辦 |
| 友誼萬歲 關子嶺鐵馬行 | biji2025 | 休閒團騎（lohasnet），無排名 |
| 雙潭騎跡 單車嘉義 | biji2025 | 免費計時查詢「不排名」 |
| 瘋系列 第七屆東三塔/東雙塔挑戰 | ensage2026 | 無總排 + ATSport（封鎖） |
| 2026萬眾騎BIKE | ensage2026 | 媽祖遶境群眾騎乘，非競賽 |
| 瘋系列 八卦山傳奇100K限時挑戰賽 | ensage2026 | 主辦明示「所有成績沒有總排」+ ATSport |
| 瘋系列 第二屆谷關雪見硬漢200K限時挑戰賽 | ensage2026 | 無總排 + ATSport（封鎖） |
| 瘋系列第六屆東三塔／東雙塔挑戰 | ensage2026 | 無總排 + ATSport（封鎖） |
| 9 騎士協會環海岸山脈220K | ensage2026 | 挑戰/團騎，無逐筆排名 |
| 明德競技 環湖饗宴-樂遊騎跑啟航 | ensage2026 | 休閒性質無排名（ctrun.com.tw） |
| Lydia & 欣欣「探索汐鴿」E起騎! | ensage2026 | 休閒認證路線社交團騎，無排名 |
| 樂遊苗栗一騎跑 aYa 完封客十二宮 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 樂遊苗栗一騎跑 VJ 綠光海風 鳴鳳古道 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 中央山脈極致挑戰 | ensage2026 | 多日極致挑戰：僅完賽英雄榜/關門時間 |
| 樂遊苗栗一騎跑 aYa 參探苗道 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| aYa 西進武嶺圓夢團(單日) | ensage2026 | aYa 嚮導團騎，非計時賽 |
| 樂遊苗栗一騎跑 樂享山海 一起練五宮 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 樂遊苗栗一騎跑 御風泊客 獅山古道 哈加縱走 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 樂遊苗栗一騎跑 Doris 巨人之手 雪見 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 樂遊苗栗一騎跑 Tracy 逐浪登炎 暢玩苗栗山海 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |

</details>

---

## 🔀【OTHER_LEAGUE — 行事曆誤標】— 2 場

<details>
<summary>展開查看</summary>

| 賽事 | 行事曆 | 實際歸屬 |
|------|--------|----------|
| 南庄山水悠遊行/仙山KOM | ensage2026 | 實為 96聯賽 苗栗站（96sporter.com），2026-10-18 尚未舉辦 |
| 騎士協會 KOM 新版KOM 北進武嶺 | ensage2026 | 實為 96聯賽 武嶺站（96sporter.com），2026-09-07 尚未舉辦 |

</details>

---

## 說明

- **真正的行事曆偵查（discover.py）與成績 ingest 都在維護者本機進行**。本雲端環境 IP 被三大賽事行事曆（RACE ON / 運動筆記 / ensage）以 HTTP 403 封鎖，無法代跑。
- 本報告僅反映上次本機 `scrapers/freshness_local.ps1 → discover.py` 寫入 `web/public/data/v1/coverage.json` 的狀態。
- 如需更新偵查結果，請在本機執行 `python scrapers/discover.py`，結果會自動寫入 coverage.json 並推入 repo。
