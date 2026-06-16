# 資料來源登錄表(Sources Registry)

> 本檔是**活的登錄表**:每次新增來源、發現新阻擋、或解開某個卡點,都要回來更新。
> 最後更新:2026-06-16

主資料集 master:**116,953 筆 / 2009–2026 / 140 場 / 5 來源**(海外賽另計;賽名正規化合併 7 組同活動後)。

> 各來源現況筆數(master 內,跨源去重後):bravelog 46,553・irunner 32,862・tsu 24,924・cyclist 12,265・cycling 349。

---

## ✅ 已爬取(完成)

| 來源 | 內容 | 格式 / 方式 | 涵蓋 | 爬蟲 | 筆數 |
|---|---|---|---|---|---|
| **cyclist.org.tw**<br>(自行車騎士協會) | 臺灣自行車聯賽全系列(陽明山王/太平山王/環花東/花蓮太平洋盃)+ KOM 登山王 | 靜態 PDF,pdfplumber 逐行;表頭自動判欄序 | 2015–2026 | `cyclist_crawl.py` | 11,276 |
| **bravelog.tw**<br>(運動趣) | 市民/挑戰賽龍頭(96聯賽/雪巴大滿貫/L'Étape/落日飛車/銅礦88/LIVDAY) | `/search` JSON API 探索 → server-rendered rank 頁分頁 | 2018–2026 | `bravelog_calendar.py` + `bravelog_crawl.py` | 46,553 |
| **tsu.com.tw**<br>(台灣自行車聯盟) | 縣長盃繞圈、越野/gravel、NeverStop武嶺、96系列、大專/地方賽;**含 TCU 選手 ID** | 靜態 HTML(UTF-8),表頭對映;`/race?y=` 年份×分頁 → `/race/result` | 2009–2025 | `tsu_crawl.py` | 24,925 |
| **cycling.org.tw**<br>(自由車協會) | 國家級:全國公路錦標賽/國手選拔(**含 UCI ID**)+ 2013 舊寬表 | 新制 PDF + 舊 .xls 寬表→長表 reshape | 2013, 2025 | `cycling_crawl.py` + `cycling_oldroad.py` | 349 |
| **cyclist.org.tw 臺灣自行車聯賽**<br>(子來源:`results_txt.asp` 聯賽頁) | TCL 個人計時賽 ITT + **團隊計時賽 TTT** + 公路繞圈各分組。走 `results_list.asp?pno=13` → `results_txt.asp?pno=N` 落地頁 → 成績公告 PDF,主 `cyclist_crawl` 抓不到。個人列雙版面(組別在 col1/col3);TTT 依車隊分組、把名次與「取第4名時間」傳遞給全隊。排除 road(重複)/積分/累計 | landing 頁 → 成績公告 PDF | 2025–2026 | `cyclist_league.py` | 819(TTT)+ ITT + 繞圈 |
| **irunner.biji.co**<br>(筆記晶片計時) | 換平台後的競技/市民賽:新玉門關公路賽、美利達盃、輪躍台南、彰化Classic 100、淡江大橋、環大苗栗、Gravel Fundo(Gravel/MTB/Enduro) | **逐筆查 → 翻頁全擷取**(見下「破解」);姓名/名字字/拉丁字母列舉 + GET `?rs=&page=` 分頁,依 memno 去重(~99%);組內完賽時間衍生名次 | 2023–2026 | `irunner_crawl.py` | 32,862 |
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
| ~~**irunner.biji.co**~~ | ✅ **已破(2026-06-12)**,移至上方已爬取表。破解法見下節。 | — 已解 — |
| **ctrun**<br>(全統) | 成績查詢需**會員登入**;且多為認證型無名次 | headless 帶登入 cookie;以「認證型」型別收 |
| **runnet.jp** | JS/SPA + JSON API **受保護**(Python 直連被擋/500) | ✅ 已解:headless 在已登入分頁內 `fetch` API |
| **sportsnet.org.tw** | 純跑步(路跑協會),**非自行車** | 不適用(不對題) |
| **96好動客 / taiwanbike.tw** | 純報名 / 觀光入口,**成績流向他站或無成績** | 不必處理(下游已抓 / 無成績) |

**通則**:能抓的共同點 = 有可瀏覽清單 + 靜態檔/HTML(或可從頁內呼叫的 JSON) + 免登入。卡點分四型:① 成績不在站內 ② 無清單可列舉 ③ 登入/IP/UA 牆 ④ 純 JS 動態(需 headless)。

### 🔓 iRunner 破解法(`irunner_crawl.py`,2026-06-12)
先前判「無全榜端點」是**填錯搜尋欄位**所致。實際:
1. **搜尋欄位是 `rs`**(中文姓名/晶片號**子字串**比對),不是 `keyword`。POST `/track/{id}/record` 只重渲染;
2. **分頁用 GET `/track/{id}/record?rs={詞}&page={N}`**(POST 帶 page 無效)→ 每頁 10 筆、**無上限**,翻到 maxpage 即完整批;
3. 結果列直出:`data-memno` / `timing-record-number`(號碼布)/ `timing-record-name`(姓名)/ `timing-record-time`(完賽)/ `timing-record-div`(組別含距離·性別/M45·車隊);
4. **完整擷取**:列舉「台灣百家姓 + 高頻名字字 + 拉丁 a–z」(拉丁掃英文名/車隊),每詞翻頁,依 **memno 去重** → 聯集 ≈ 全場。實測美利達盃 1834(純姓氏)→ **2016(加掃尾)≈ 真實場 ~2015**,**~99%**;
5. **賽事發現**:掃 `/track/{id}` 區間取 og:title,關鍵字分類自行車(排除馬拉松/三鐵/田徑);
6. 名次非結果列所含 → **依組內完賽時間排序衍生**(標 `derivedrank`);成績經 PDPA 遮罩後入 master,跨源與 Bravelog 自動去重(2026-06 該批去重 2,934 筆)。

> 同法應可套用其他 biji 系晶片計時站。**ATSport** 則是 TCP 層封我方出口 IP(GCP 主機 35.194.189.45,443/80 皆 timeout),須在台節點/代理。

---

## 🔍 探索 / 發現用(行事曆種子,供 `discover.py`)

不靠人工列舉:從**公開行事曆**反推「應存在的賽事」母表,再與 master 比對找缺口。

| 行事曆 | 狀態 |
|---|---|
| **RACE ON 行事曆**(raceon.com.tw) | ✅ `discover.py` 已接(`parser=raceon`,`<li>` 結構) |
| **運動筆記 自行車行事曆**(running.biji.co) | ✅ `discover.py` 已接(`parser=biji`,需 HTML entity 解碼) |
| **ensage 2026 自行車&三鐵行事曆**(blog.ensage.tours) | ✅ `discover.py` 已接(`parser=ensage`,`<tr>` 表格 132 筆;濾掉三鐵/跑步 + ensage 自家保母車/接駁/海外旅遊產品) |
| 96好動客 / 伊貝特 / Phomi / biji competition | ❌ JS 動態 或 自行車稀少(伊貝特 index 30 場僅 1 自行車)→ 不適合靜態列舉 |
| 單車誌 / CYCLINGTIME / ctyeh | ❌ 文章/內容式或 JS,非結構化賽曆 |

→ `scrapers/discover.py`:行事曆 → 正規化(core=race_key 去年份/季節/距離/屆)→ fuzzy-diff master → 缺漏清單 + 推測來源。**目前 3 個行事曆 → 找出 53 場缺漏**(瘋系列 八卦山傳奇/谷關雪見硬漢/中雙塔/白毛山·TWB 東三塔550/東雙塔470/彰化騎福·TBA 西濱挑戰·萬眾騎BIKE·梅山36彎·Gravel Fundo…),輸出 `data/processed/_discover/missing_races.json`。多為主辦自家頁/FB,屬 OCR 或逐場索取範疇。

### 已知但尚待處理(從 discover 追出的)
- ✅ **臺灣自行車聯賽 TTT(團隊計時賽)已收**(`parse_ttt`:依車隊分組、把隊名次與「取第4名時間」傳遞給全隊成員,strip 國籍碼)——819 列。_積分排名/累計總排名_ 為衍生排名仍不收(非完賽列)。
- **瘋系列(中雙塔/縮時環島300K/911/無眠夜騎/白毛山)**:成績多在**主辦自家頁或 FB**,無統一平台 → 逐場找頁或 OCR。
- **tsu.com.tw 2026**:已重爬,但 2026 賽事尚無成績公告(0 筆),賽季進行中再回來補。

### FB(社團/粉專)能不能自動爬?
**不能,也不建議**:需登入、強反爬/封號、違反 ToS,內容多需登入且成績常是**圖片**。可行路線 = **使用者提供成績圖 → OCR/視覺模型轉結構化**(非自動爬 FB)。

---

## 🔁 「賽事搬家」型缺口(2026-06-12 發現)

部分我們**過去有收**的賽事,新一屆**換了計時/成績平台**,於是斷在我們爬不到的那一邊。典型例:

- **戀戀197 東海岸自行車公路賽**(台東 197 縣道):2022/2023/2024 三屆都在 **Bravelog**(已收,共 6,547 列);**2025 屆(12/07 辦)不在 Bravelog**,改由 **iRunner(筆記晶片計時)/ ATSport** 計時 → 落在我們的 blocked 平台。這不是 Bravelog 漏抓,是賽事換平台。

**順手做的 Bravelog 完整度稽核**:用 `/search` JSON 比對「Bravelog 上的自行車賽 vs 我們已收」——

| 年 | Bravelog 上自行車賽 | 我們已收 | 結論 |
|---|---|---|---|
| 2025 | 27(含 2 組重複/拆組) | 26 | 實質**收滿** |
| 2026 | 8 | 6 | 其餘 2 場為未來賽、尚無成績 |

→ **我們在爬的平台(Bravelog)沒有系統性漏抓**;新缺口主要來自「搬家到 iRunner/ATSport」與長尾 FB/主辦頁。**iRunner 已於 2026-06-12 破解收錄**(11 場/12,727 筆);**戀戀197-2025 仍缺**——它在 ATSport,而 ATSport 於本環境 TCP 層被封(需在台節點),或走投稿/主辦索取。

---

## 真正剩的缺口

散落 **FB 社團 / 主辦一次性頁** 的在地賽(輪耀台灣、Dirty Formosa/gravel、梅山36彎、澎湖跳島、環大苗栗、桃園航空城繞圈賽…)——無結構化來源,需 **OCR 成績圖** 或主辦索取原始檔。另加「搬家到 iRunner/ATSport」的競技賽(戀戀197-2025 等)。
