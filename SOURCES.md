# 資料來源登錄表(Sources Registry)

> 本檔是**活的登錄表**:每次新增來源、發現新阻擋、或解開某個卡點,都要回來更新。
> 最後更新:2026-06-11

主資料集 master:**83,103 筆 / 2009–2026 / 115 場 / 4 來源**(海外賽另計)。

---

## ✅ 已爬取(完成)

| 來源 | 內容 | 格式 / 方式 | 涵蓋 | 爬蟲 | 筆數 |
|---|---|---|---|---|---|
| **cyclist.org.tw**<br>(自行車騎士協會) | 臺灣自行車聯賽全系列(陽明山王/太平山王/環花東/花蓮太平洋盃)+ KOM 登山王 | 靜態 PDF,pdfplumber 逐行;表頭自動判欄序 | 2015–2026 | `cyclist_crawl.py` | 11,276 |
| **bravelog.tw**<br>(運動趣) | 市民/挑戰賽龍頭(96聯賽/雪巴大滿貫/L'Étape/落日飛車/銅礦88/LIVDAY) | `/search` JSON API 探索 → server-rendered rank 頁分頁 | 2018–2026 | `bravelog_calendar.py` + `bravelog_crawl.py` | 46,553 |
| **tsu.com.tw**<br>(台灣自行車聯盟) | 縣長盃繞圈、越野/gravel、NeverStop武嶺、96系列、大專/地方賽;**含 TCU 選手 ID** | 靜態 HTML(UTF-8),表頭對映;`/race?y=` 年份×分頁 → `/race/result` | 2009–2025 | `tsu_crawl.py` | 24,925 |
| **cycling.org.tw**<br>(自由車協會) | 國家級:全國公路錦標賽/國手選拔(**含 UCI ID**)+ 2013 舊寬表 | 新制 PDF + 舊 .xls 寬表→長表 reshape | 2013, 2025 | `cycling_crawl.py` + `cycling_oldroad.py` | 349 |
| **runnet.jp**<br>(海外,獨立別集) | 日本 Mt.富士ヒルクライム等(**不進台灣 master**) | JS/SPA(Next.js);headless 渲染 + 頁內 fetch 受保護 JSON API | 2026 | `overseas_runnet.py` | 8,724 |

> 合併工具:`merge.py`(年份無關、自動納源、跨源去重)。海外賽存 `web/public/data/overseas/`,不進 merge。

---

## ⚠️ 受限 / 被擋(暫無法系統性納入)

| 來源 | 卡點 | 可能的破法 |
|---|---|---|
| **伊貝特 / bao-ming** | 詳情頁 302+Refresh 反爬跳轉;成績多不在站內 | Playwright 跟隨跳轉(但成績落點才是關鍵) |
| **iBodyGo** | UA / Session 阻擋 | 帶完整 headers + cookie jar |
| **ATSport** | 封鎖非台灣 IP | 台灣 IP 代理 / 在台節點 |
| **樂活成績站** | JS 動態渲染 | Playwright headless |
| **irunner.biji.co**<br>(筆記報名) | JS 查詢式、**無「列出全部」入口**;自行車多為 DIY 營隊/MTB | 找背後 XHR 端點;或 seed 名單逐筆查 |
| **ctrun**<br>(全統) | 成績查詢需**會員登入**;且多為認證型無名次 | headless 帶登入 cookie;以「認證型」型別收 |
| **runnet.jp** | JS/SPA + JSON API **受保護**(Python 直連被擋/500) | ✅ 已解:headless 在已登入分頁內 `fetch` API |
| **sportsnet.org.tw** | 純跑步(路跑協會),**非自行車** | 不適用(不對題) |
| **96好動客 / taiwanbike.tw** | 純報名 / 觀光入口,**成績流向他站或無成績** | 不必處理(下游已抓 / 無成績) |

**通則**:能抓的共同點 = 有可瀏覽清單 + 靜態檔/HTML(或可從頁內呼叫的 JSON) + 免登入。卡點分四型:① 成績不在站內 ② 無清單可列舉 ③ 登入/IP/UA 牆 ④ 純 JS 動態(需 headless)。

---

## 🔍 探索 / 發現用(行事曆種子,供 `discover.py`)

不靠人工列舉:從**公開行事曆**反推「應存在的賽事」母表,再與 master 比對找缺口。

| 行事曆 | 用途 |
|---|---|
| **RACE ON 行事曆**(raceon.com.tw) | 年度自行車賽曆(可列舉) |
| 部落格賽曆(CYCLINGTIME / ensage / Betery / je22) | 跨來源交叉驗證 |
| 各平台 event list(bravelog `/search`、tsu `/race`、cyclist 列表) | 平台自身賽事清單 |

→ 詳見 `scrapers/discover.py`(缺漏分析:行事曆 → 正規化 → 比對 master → 缺漏清單 + 推測來源)。

---

## 真正剩的缺口

散落 **FB 社團 / 主辦一次性頁** 的在地賽(輪耀台灣、Dirty Formosa/gravel、梅山36彎、澎湖跳島、環大苗栗、桃園航空城繞圈賽…)——無結構化來源,需 **OCR 成績圖** 或主辦索取原始檔。
