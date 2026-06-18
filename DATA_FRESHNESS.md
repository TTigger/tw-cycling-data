# 台灣公路車成績資料新鮮度週報

**產生時間 (UTC):** Thu Jun 18 01:03:21 UTC 2026

> ⚠️ 本次 discover.py 網路存取全部被雲端環境封鎖（HTTP 403），行事曆無法重新抓取。
> 缺漏清單取自 coverage.json（上一次本機成功執行的結果），仍可作為待辦依據。

---

## 目前涵蓋摘要

| 項目 | 數值 |
|------|------|
| 總成績筆數 | **116,953** |
| 場次數 (race-year) | **149** (coverage.json) / 140 (master_summary) |
| 年份範圍 | **2009 – 2026** |
| 海外賽成績 | 8,724 筆 |

### 各來源筆數

| 來源平台 | 筆數 |
|----------|------|
| bravelog.tw | 46,553 |
| irunner.biji.co | 32,862 |
| tsu.com.tw | 24,924 |
| cyclist.org.tw | 12,265 |
| cycling.org.tw | 349 |

### 年份分布（前十大）

| 年份 | 筆數 |
|------|------|
| 2024 | 33,665 |
| 2025 | 32,029 |
| 2026 | 11,638 |
| 2023 | 18,082 |
| 2022 | 7,863 |
| 2020 | 2,763 |
| 2019 | 1,229 |
| 2018 | 1,124 |
| 2017 | 947 |
| 2016 | 698 |

---

## 缺漏偵查說明

- 行事曆來源：RACE ON 2026、運動筆記 2025、ensage 2026
- 本次 discover.py 執行狀態：**所有行事曆 HTTP 403（雲端 IP 封鎖）**，以 coverage.json 快取結果為準
- 缺漏判定基準：行事曆有列、master.public.json 無對應 race_name_canonical

**行事曆缺漏總計：47 場**（行事曆有，我們還沒收）

---

## 【待 ingest：已破解平台】✅

下列 15 場可在維護者本機透過既有 scraper 爬取：

| # | 賽事名稱 | 猜測來源 | 行事曆 | 可爬性 |
|---|---------|---------|--------|--------|
| 1 | 瘋系列 無眠征途 夜騎日月潭限時挑戰賽 | bravelog.tw / cyclist.org.tw / tsu.com.tw | raceon2026 | ✅ 查驗後 ingest |
| 2 | 台灣瘋系列 小台灣縮時環島顛峰300K限時挑戰賽 | bravelog.tw / cyclist.org.tw / tsu.com.tw | raceon2026 | ✅ 查驗後 ingest |
| 3 | TIS桃園台南280KM雙城挑戰賽 | bravelog.tw / cyclist.org.tw / tsu.com.tw | raceon2026 | ✅ 查驗後 ingest |
| 4 | 瘋系列 八卦山傳奇100K限時挑戰賽 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 5 | 瘋系列 第二屆台灣瘋系列 谷關雪見硬漢200K限時挑戰賽 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 6 | 9 騎士協會環海岸山脈220K | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 7 | 騎士協會聯賽 S1 陽明山登山王 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 8 | 騎士協會聯賽 S2 春季登山王之路 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 9 | 騎士協會聯賽 S3-S4 環花東 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 10 | 明德競技 環湖饗宴-樂遊騎跑啟航 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 11 | 騎士協會聯賽 S5 太平山挑戰賽 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 12 | aYa 西進武嶺圓夢團(單日) | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 13 | 南庄山水悠遊行/仙山KOM | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 14 | 騎士協會 KOM 北進武嶺 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |
| 15 | 騎士協會聯賽 S7 花蓮太平洋盃 | bravelog.tw / cyclist.org.tw / tsu.com.tw | ensage2026 | ✅ 查驗後 ingest |

### 本機 ingest 提示

```bash
# 1. 在 bravelog / cyclist / tsu 上找到對應賽事頁面，確認成績已公告
# 2. 執行對應 scraper（擇一或多個）
python scrapers/bravelog_crawl.py
python scrapers/cyclist_crawl.py
python scrapers/tsu_crawl.py

# 3. 合併與重建
python scrapers/merge.py
python scrapers/build_viz.py
python scrapers/build_athletes.py
python scrapers/build_insights.py
python scrapers/build_difficulty.py
python scrapers/build_race_dna.py

# 4. 驗證
python scrapers/validate.py

# 5. 提交
git add web/public/data/
git commit -m "data: ingest <race-name> <year>"
git push
```

> **注意：** 成績常於賽後數天至數週才公告，上列場次不一定已有成績可爬。
> 建議先手動確認各平台上該賽事頁面確實已有完整成績，再執行 scraper。

---

## 【待人工/OCR】⛔

下列 32 場來源不明或位於被封鎖/無結構化資料的平台（FB 社團、主辦自家頁、ATSport 等），需人工查驗或 OCR：

| # | 賽事名稱 | 行事曆 | 備註 |
|---|---------|--------|------|
| 1 | 超越巔峰-中央山脈極致挑戰 | raceon2026 | 需查主辦頁 |
| 2 | 第一屆極限東征_瘋911 | raceon2026 | 需查主辦頁 |
| 3 | Light One Bike 系列 - 生態遊程 | raceon2026 | 需查主辦頁 |
| 4 | 2026時代騎輪節 Wheels Ride Festival | raceon2026 | 需查主辦頁 |
| 5 | 瘋系列第七屆中雙塔 | raceon2026 | 需查主辦頁 |
| 6 | Light One Bike 系列 - 長距離挑戰 | raceon2026 | 需查主辦頁 |
| 7 | 屏東來義之心山嵐單車行 | biji2025 | 需查主辦頁 |
| 8 | 瘋系列 白毛山巔峰騎跡 | biji2025 | 需查主辦頁 |
| 9 | 南投旅遊百 K 挑戰 | biji2025 | 需查主辦頁 |
| 10 | 友誼萬歲〜關子嶺鐵馬行 | biji2025 | 需查主辦頁 |
| 11 | 雲林單車遊-梅好騎跡 咖啡探索之旅 | biji2025 | 需查主辦頁 |
| 12 | 友誼萬歲 關子嶺鐵馬行 | biji2025 | 需查主辦頁（疑為重複） |
| 13 | 雙潭騎跡 單車嘉義 | biji2025 | 需查主辦頁 |
| 14 | TWB台灣自行車協會 第4屆東三塔550 | ensage2026 | 需查主辦頁 |
| 15 | TWB台灣自行車協會 第4屆東雙塔470 | ensage2026 | 需查主辦頁 |
| 16 | 瘋系列 第七屆東三塔/東雙塔挑戰 | ensage2026 | 需查主辦頁 |
| 17 | TWB台灣自行車協會 彰化騎福 | ensage2026 | 需查主辦頁 |
| 18 | TBA中華民國自行車協會 第16屆雙主場輪霸西濱挑戰 | ensage2026 | 需查主辦頁 |
| 19 | 2026萬眾騎BIKE | ensage2026 | 需查主辦頁 |
| 20 | TWB台灣自行車協會 北高360 | ensage2026 | 需查主辦頁（與 TBA 北高360 系列重疊？） |
| 21 | TWB東三塔＆雙塔 | ensage2026 | 需查主辦頁（疑為重複） |
| 22 | 瘋系列第六屆東三塔／東雙塔挑戰 | ensage2026 | 需查主辦頁（疑為重複） |
| 23 | 輪霸西濱 五大重點 降低雨天騎乘風險 | ensage2026 | 需查主辦頁（疑 ensage 廣告文） |
| 24 | Lydia & 欣欣「探索汐鴿」E起騎! | ensage2026 | 需查主辦頁 |
| 25 | 樂遊苗栗一騎跑 aYa 完封客十二宮 | ensage2026 | 需查主辦頁 |
| 26 | 樂遊苗栗一騎跑 VJ 綠光海風 鳴鳳古道 | ensage2026 | 需查主辦頁 |
| 27 | 中央山脈極致挑戰 | ensage2026 | 需查主辦頁（疑為 #1 重複） |
| 28 | 樂遊苗栗一騎跑 aYa 參探苗道 | ensage2026 | 需查主辦頁 |
| 29 | 樂遊苗栗一騎跑 樂享山海 一起練五宮 | ensage2026 | 需查主辦頁 |
| 30 | 樂遊苗栗一騎跑 御風泊客 獅山古道 哈加縱走 | ensage2026 | 需查主辦頁 |
| 31 | 樂遊苗栗一騎跑 Doris 巨人之手 雪見 | ensage2026 | 需查主辦頁 |
| 32 | 樂遊苗栗一騎跑 Tracy 逐浪登炎 暢玩苗栗山海 | ensage2026 | 需查主辦頁 |

---

## 備註

- 行事曆中「樂遊苗栗一騎跑」系列（#25–32）多為健行/觀光型活動，部分可能不含計時成績，需人工確認是否有結構化成績頁。
- ensage 行事曆混入部分廣告文（如「五大重點 降低雨天騎乘風險」），非獨立賽事。
- discover.py 在本機執行時可取得最新缺漏清單；雲端 IP 因各平台封鎖，無法自動重跑。
