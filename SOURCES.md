# 資料來源登錄表(Sources Registry)

> 本檔是**活的登錄表**:每次新增來源、發現新阻擋、或解開某個卡點,都要回來更新。
> 最後更新:2026-06-11

主資料集 master:**84,091 筆 / 2009–2026 / 116 場 / 4 來源**(海外賽另計)。

---

## ✅ 已爬取(完成)

| 來源 | 內容 | 格式 / 方式 | 涵蓋 | 爬蟲 | 筆數 |
|---|---|---|---|---|---|
| **cyclist.org.tw**<br>(自行車騎士協會) | 臺灣自行車聯賽全系列(陽明山王/太平山王/環花東/花蓮太平洋盃)+ KOM 登山王 | 靜態 PDF,pdfplumber 逐行;表頭自動判欄序 | 2015–2026 | `cyclist_crawl.py` | 11,276 |
| **bravelog.tw**<br>(運動趣) | 市民/挑戰賽龍頭(96聯賽/雪巴大滿貫/L'Étape/落日飛車/銅礦88/LIVDAY) | `/search` JSON API 探索 → server-rendered rank 頁分頁 | 2018–2026 | `bravelog_calendar.py` + `bravelog_crawl.py` | 46,553 |
| **tsu.com.tw**<br>(台灣自行車聯盟) | 縣長盃繞圈、越野/gravel、NeverStop武嶺、96系列、大專/地方賽;**含 TCU 選手 ID** | 靜態 HTML(UTF-8),表頭對映;`/race?y=` 年份×分頁 → `/race/result` | 2009–2025 | `tsu_crawl.py` | 24,925 |
| **cycling.org.tw**<br>(自由車協會) | 國家級:全國公路錦標賽/國手選拔(**含 UCI ID**)+ 2013 舊寬表 | 新制 PDF + 舊 .xls 寬表→長表 reshape | 2013, 2025 | `cycling_crawl.py` + `cycling_oldroad.py` | 349 |
| **cyclist.org.tw 臺灣自行車聯賽**<br>(子來源:`results_txt.asp` 聯賽頁) | TCL 個人計時賽 ITT + **團隊計時賽 TTT** + 公路繞圈各分組。走 `results_list.asp?pno=13` → `results_txt.asp?pno=N` 落地頁 → 成績公告 PDF,主 `cyclist_crawl` 抓不到。個人列雙版面(組別在 col1/col3);TTT 依車隊分組、把名次與「取第4名時間」傳遞給全隊。排除 road(重複)/積分/累計 | landing 頁 → 成績公告 PDF | 2025–2026 | `cyclist_league.py` | 819(TTT)+ ITT + 繞圈 |
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
| **irunner.biji.co**<br>(筆記報名) | **逐筆查(競賽編號 or 姓名)**、無「列出全部」端點;結果走 csrf+session 的 AJAX,頁面重(廣告/FB widget)→ 瀏覽器擷取 XHR 常 timeout。已知端點 `/track/{id}/results|record|group`,但 search 參數未破。理論可破:headless + **依常見姓氏(陳/林/黃…)或 bib 列舉** 拼回全場(每查一批),但 per-query 慢、ROI 低(多為跑步) | headless + 姓氏/bib 列舉(未完成,新玉門關為例) |
| **ctrun**<br>(全統) | 成績查詢需**會員登入**;且多為認證型無名次 | headless 帶登入 cookie;以「認證型」型別收 |
| **runnet.jp** | JS/SPA + JSON API **受保護**(Python 直連被擋/500) | ✅ 已解:headless 在已登入分頁內 `fetch` API |
| **sportsnet.org.tw** | 純跑步(路跑協會),**非自行車** | 不適用(不對題) |
| **96好動客 / taiwanbike.tw** | 純報名 / 觀光入口,**成績流向他站或無成績** | 不必處理(下游已抓 / 無成績) |

**通則**:能抓的共同點 = 有可瀏覽清單 + 靜態檔/HTML(或可從頁內呼叫的 JSON) + 免登入。卡點分四型:① 成績不在站內 ② 無清單可列舉 ③ 登入/IP/UA 牆 ④ 純 JS 動態(需 headless)。

---

## 🔍 探索 / 發現用(行事曆種子,供 `discover.py`)

不靠人工列舉:從**公開行事曆**反推「應存在的賽事」母表,再與 master 比對找缺口。

| 行事曆 | 狀態 |
|---|---|
| **RACE ON 行事曆**(raceon.com.tw) | ✅ `discover.py` 已接(`parser=raceon`,`<li>` 結構) |
| **運動筆記 自行車行事曆**(running.biji.co) | ✅ `discover.py` 已接(`parser=biji`,需 HTML entity 解碼) |
| 單車誌 cycling-update.info / CYCLINGTIME | ❌ 文章/內容式(非結構化賽曆),headless 也只抓到導覽列+舊環法文章 → 不適合當 gap 種子 |
| 各平台 event list(bravelog `/search`、tsu `/race`) | 平台自身清單(已是來源,gap 分析意義較小) |

→ `scrapers/discover.py`:行事曆 → 正規化(core=race_key 去年份/季節/距離/屆)→ fuzzy-diff master → 缺漏清單 + 推測來源。**目前 2 個行事曆 → 找出 22 場缺漏**(環大苗栗/桃園航空城繞圈賽✅已補/瘋系列數場/Gravel Fundo/白毛山/雲林梅好騎跡…),輸出 `data/processed/_discover/missing_races.json`。

### 已知但尚待處理(從 discover 追出的)
- ✅ **臺灣自行車聯賽 TTT(團隊計時賽)已收**(`parse_ttt`:依車隊分組、把隊名次與「取第4名時間」傳遞給全隊成員,strip 國籍碼)——819 列。_積分排名/累計總排名_ 為衍生排名仍不收(非完賽列)。
- **瘋系列(中雙塔/縮時環島300K/911/無眠夜騎/白毛山)**:成績多在**主辦自家頁或 FB**,無統一平台 → 逐場找頁或 OCR。
- **tsu.com.tw 2026**:已重爬,但 2026 賽事尚無成績公告(0 筆),賽季進行中再回來補。

### FB(社團/粉專)能不能自動爬?
**不能,也不建議**:需登入、強反爬/封號、違反 ToS,內容多需登入且成績常是**圖片**。可行路線 = **使用者提供成績圖 → OCR/視覺模型轉結構化**(非自動爬 FB)。

---

## 真正剩的缺口

散落 **FB 社團 / 主辦一次性頁** 的在地賽(輪耀台灣、Dirty Formosa/gravel、梅山36彎、澎湖跳島、環大苗栗、桃園航空城繞圈賽…)——無結構化來源,需 **OCR 成績圖** 或主辦索取原始檔。
