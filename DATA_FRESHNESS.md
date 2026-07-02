# 資料新鮮度週報

產生時間：**2026-07-02 01:01 UTC**  
coverage.json 最後更新：**2026-06-30 04:28 UTC**（約 1.8 天前，新鮮度正常）

> **偵查方式說明**：行事曆偵查（discover.py）由維護者在本機 Windows 排程執行（scrapers/freshness_local.ps1），結果已寫入 `web/public/data/v1/coverage.json`。雲端 IP 會被 RACE ON / 運動筆記 / ensage 以 HTTP 403 封鎖，故本報告**不執行任何偵查**，僅整理已提交的 coverage.json 狀態。

---

## 涵蓋摘要

> 本節資料來自 `web/public/data/v1/coverage.json`（含行事曆追蹤的 6 個平台）。  
> `data/processed/master_summary.json` 另含 twbike.org 與 taiwanbike.org 共 147,609 筆、161 場，為全量資料集。

| 項目 | 數值 |
|------|------|
| 成績筆數（coverage 追蹤範圍） | **118,501** |
| 場次數（calendar 掃描到） | **130** |
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

行事曆來源：RACE ON 2026、運動筆記 自行車賽事行事曆、ensage 2026 自行車&三鐵行事曆

---

## 缺漏清單（共 44 場）

| 分類 | 場數 | 可行動？ |
|------|------|----------|
| 🔍 **尚未調查**（無 status） | **0** | ✅ 最高優先（本次已全數調查完） |
| 🚧 **BLOCKED（有成績·平台待支援）** | **7** | ✅ 次高優先，有潛在新資料源 |
| ⏳ NOT_HELD | 5 | — 未辦，辦完再查 |
| ❌ NO_RANKING | 30 | — 確認無逐筆排名，不可爬 |
| 🔀 OTHER_LEAGUE | 2 | — 行事曆誤標，另案追蹤 |

---

## 🔍 尚未調查（0 場）

本次 coverage.json 所有缺漏均已標記狀態，無待調查項目。

---

## 🚧 BLOCKED — 有成績·平台待支援（7 場）

> 這些賽事**確認有逐筆名次與成績**，但結果存放於本站尚不支援的平台格式，是最值得評估開發新爬蟲的機會。

### 平台 A：twbike.org PDF + score.focusline（5 場）

共 5 場 TWB 台灣自行車協會賽事，成績以 PDF 形式掛在 twbike.org，並同步至 score.focusline 計時平台。

| 賽事 | 行事曆 | 備注 |
|------|--------|------|
| TWB台灣自行車協會 第4屆東三塔550 | ensage2026 | twbike.org PDF + score.focusline |
| TWB台灣自行車協會 第4屆東雙塔470 | ensage2026 | twbike.org PDF + score.focusline |
| TWB台灣自行車協會 彰化騎福 | ensage2026 | twbike.org PDF + score.focusline |
| TWB台灣自行車協會 北高360 | ensage2026 | twbike.org PDF + score.focusline |
| TWB東三塔＆雙塔 | ensage2026 | twbike.org PDF + score.focusline |

**建議**：
- `score.focusline.net` 若有 HTML 成績頁，可評估爬取可行性（與 tsu.com.tw 同屬計時後台）。
- PDF 成績可用 `pdfplumber` 解析，但格式可能因賽事不同而異，維護成本較高。
- 優先調查 score.focusline 是否已有結構化頁面。

### 平台 B：taiwanbike.org Google Sheets（2 場）

| 賽事 | 行事曆 | 備注 |
|------|--------|------|
| TBA中華民國自行車協會 第16屆雙主場輪霸西濱挑戰 | ensage2026 | taiwanbike.org Google Sheets |
| 輪霸西濱 五大重點 降低雨天騎乘風險 | ensage2026 | taiwanbike.org Google Sheets |

**建議**：
- 確認 Google Sheets 是否設為公開（anyone with link）。
- 若公開，可透過 `/export?format=csv` 直接下載 CSV，解析成本低。
- 注意：這 2 筆為同一系列賽的不同版本行事曆登記，可能是同一場。

---

## ⏳ NOT_HELD — 尚未舉辦（5 場）

<details>
<summary>點開查看（辦完再查）</summary>

| 賽事 | 行事曆 | 預計日期 | 備注 |
|------|--------|----------|------|
| 瘋系列 無眠征途 夜騎日月潭限時挑戰賽 | raceon2026 | 2026-07-18 | 瘋系列限時挑戰，完賽後恐無總排（屆時查驗） |
| 第一屆極限東征_瘋911 | raceon2026 | 2026-09-11 | 瘋系列，恐無總排 |
| 台灣瘋系列 小台灣縮時環島顛峰300K限時挑戰賽 | raceon2026 | 2026-09-26 | 瘋系列300K限時挑戰，恐無總排 |
| TIS桃園台南280KM雙城挑戰賽 | raceon2026 | 2026-10-31 | 往屆僅發完賽獎座/證書，恐無排名 |
| 騎士協會聯賽 S7 花蓮太平洋盃 | ensage2026 | 2026-12-04~05 | 辦完應有 cyclist.org.tw PDF 成績 |

</details>

---

## ❌ NO_RANKING — 已確認無排名（30 場）

<details>
<summary>點開查看（休閒/瘋系列/無排名活動，不可爬）</summary>

| 賽事 | 行事曆 | 說明 |
|------|--------|------|
| 超越巔峰-中央山脈極致挑戰 | raceon2026 | 多日極致挑戰，僅完賽英雄榜/關門時間，無排名 |
| 2026南投旅遊百K自行車挑戰 | raceon2026 | 休閒小鎮漫遊，無排名 |
| Light One Bike 系列 - 生態遊程 | raceon2026 | 低碳慢遊生態團騎，明示非競賽（伊貝特報名） |
| 2026時代騎輪節 Wheels Ride Festival | raceon2026 | 明示非競賽，計時僅供參考 |
| 瘋系列第七屆中雙塔 | raceon2026 | 無總排 + ATSport（封鎖） |
| Light One Bike 系列 - 長距離挑戰 | raceon2026 | 低碳慢遊生態團騎，明示非競賽 |
| 屏東來義之心山嵐單車行 | biji2025 | 休閒團騎，查無成績頁 |
| 瘋系列 白毛山巔峰騎跡 | biji2025 | 完賽獎牌制，無總排 + ATSport |
| 南投旅遊百 K 挑戰 | biji2025 | 休閒小鎮漫遊，無排名 |
| 友誼萬歲〜關子嶺鐵馬行 | biji2025 | 休閒團騎（lohasnet），無排名 |
| 雲林單車遊-梅好騎跡 咖啡探索之旅 | biji2025 | 休閒團騎，2025 停辦 |
| 友誼萬歲 關子嶺鐵馬行 | biji2025 | 休閒團騎（lohasnet），無排名 |
| 雙潭騎跡 單車嘉義 | biji2025 | 免費計時查詢「不排名」 |
| 瘋系列 第七屆東三塔/東雙塔挑戰 | ensage2026 | 無總排 + ATSport（封鎖） |
| 2026萬眾騎BIKE | ensage2026 | 媽祖遶境群眾騎乘，非競賽 |
| 瘋系列 八卦山傳奇100K限時挑戰賽 | ensage2026 | 主辦明示「所有成績沒有總排」+ ATSport計時 |
| 瘋系列 谷關雪見硬漢200K限時挑戰賽 | ensage2026 | 無總排 + ATSport（封鎖平台） |
| 9 騎士協會環海岸山脈220K | ensage2026 | 挑戰/團騎，無逐筆排名 |
| 明德競技 環湖饗宴-樂遊騎跑啟航 | ensage2026 | 休閒性質，無排名（ctrun.com.tw） |
| Lydia & 欣欣「探索汐鴿」E起騎! | ensage2026 | 社交團騎，無排名 |
| 樂遊苗栗一騎跑 aYa 完封客十二宮 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 樂遊苗栗一騎跑 VJ 綠光海風 鳴鳳古道 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 中央山脈極致挑戰 | ensage2026 | 多日極致挑戰，僅完賽英雄榜/關門時間，無排名 |
| 樂遊苗栗一騎跑 aYa 參探苗道 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| aYa 西進武嶺圓夢團(單日) | ensage2026 | aYa 嚮導團騎，非計時賽 |
| 樂遊苗栗一騎跑 樂享山海 一起練五宮 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 樂遊苗栗一騎跑 御風泊客 獅山古道 哈加縱走 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 樂遊苗栗一騎跑 Doris 巨人之手 雪見 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 樂遊苗栗一騎跑 Tracy 逐浪登炎 暢玩苗栗山海 | ensage2026 | 嚮導團騎/集點健康活動，無排名 |
| 瘋系列第六屆東三塔／東雙塔挑戰 | ensage2026 | 無總排 + ATSport（封鎖） |

</details>

---

## 🔀 OTHER_LEAGUE — 行事曆誤標（2 場）

<details>
<summary>點開查看（歸屬其他聯賽，另案追蹤）</summary>

| 賽事（行事曆顯示） | 行事曆 | 實際聯賽 | 備注 |
|-------------------|--------|----------|------|
| 南庄山水悠遊行/仙山KOM | ensage2026 | 96聯賽 苗栗站（96sporter.com） | 2026-10-18 尚未舉辦 |
| 騎士協會 KOM 新版KOM 北進武嶺 | ensage2026 | 96聯賽 武嶺站（96sporter.com） | 2026-09-07 尚未舉辦 |

</details>

---

## 說明

- **行事曆偵查與成績 ingest** 均在維護者本機進行；本報告僅反映上次本機 `python scrapers/discover.py` 寫入 `coverage.json` 的狀態。
- 雲端 CI 環境 IP 被 RACE ON / 運動筆記 / ensage 行事曆以 HTTP 403 封鎖，**不在此環境執行 discover.py**。
- 若 coverage.json 超過 10 天未更新，請在本機執行 `python scrapers/discover.py`（Windows: `scrapers/freshness_local.ps1`）。
