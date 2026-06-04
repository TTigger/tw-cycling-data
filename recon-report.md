# 台灣公路車賽事資料源偵查報告

> 階段:資料源偵查(reconnaissance)+ 部落格賽曆交叉驗證
> 產出日期:2026-06-04 ｜ 方法:多代理工作流(16 agents,涵蓋 7 報名站 + Bravelog + 額外探勘 + 3 組部落格賽曆)
> 原始資料:`recon-raw.json`

---

## 一、核心結論:報名與成績「分離外包」是常態

同一場賽事的「報名」與「成績」往往不在同一個網站。要建資料庫,**成績平台才是主目標**,報名平台主要用來發現「有哪些賽事」。

資料生態分三層:
- **(A) 報名平台**:伊貝特、96好動客、筆記報名、雪巴、樂活、全統、活動咖
- **(B) 成績/計時平台**:Bravelog(市民賽龍頭)、iRunner、樂活成績站、iBodyGo、ATSport
- **(C) 主辦/協會自架**:自行車騎士協會(TCF)、自由車協會(國家級)、自行車協會(TBA 認證型)

---

## 二、優先爬取來源(已排序)

| 優先 | 來源 | 涵蓋年份 | 格式 | 可爬性 | 備註 |
|---|---|---|---|---|---|
| ⭐1 | **自行車騎士協會 cyclist.org.tw** | 2014–2026 | PDF | **高(最易)** | 臺灣自行車聯賽全系列(陽明山王/太平山王/環花東/花蓮太平洋盃)+ KOM 登山王。靜態 ASP,`results_list.asp?pno=1..13` 列表直含 PDF 連結,無 JS/登入/captcha,已實測下載成功 |
| ⭐2 | **自由車協會 cycling.org.tw** | **1998–2026** | PDF/Excel/zip | 高 | 國家級權威:環台 Tour de Taiwan、全國公路/場地/登山車錦標賽、國手選拔。**回溯最久**,最適合做歷史母源回填 2010–2017 缺口 |
| ⭐3 | **Bravelog 運動趣** | ~2018–2026 | 網頁表格 | 中(需實測) | 市民/挑戰型龍頭(96聯賽/雪巴大滿貫/L'Étape/落日飛車/銅礦88,自稱全台 80%)。欄位最豐富(晶片淨時間/分段/均速/多維排名)。⚠️ 兩份偵查對 `/contest/rank` 是否需 JS 判讀**衝突**,實作前須用 DevTools 實測 |
| 4 | **筆記報名 irunner.biji.co** | 2016–2026 | 網頁表格 | 高 | 同站靜態 HTML、免登入。經典新玉門關、美利達盃等。限制:需姓名/號碼查詢,無「列出全部」入口 |
| 5 | taiwanbike.org(早期 .xls)+ bao-ming.com(賽事清單) | 2010–2026 | .xls / HTML | 高 / 中 | TBA 早期 .xls 直連適合補 2010–2014 名次;伊貝特 `/eb/index` 靜態可取賽事清單(但詳情頁有反爬需 headless,成績不在站內) |
| ⏸ 暫緩 | ATSport / iBodyGo / EventPal | — | 網頁 | 低 | 結構化或量大,但有 IP/bot 阻擋與 JS 動態,PoC 階段不優先 |

---

## 三、成績格式總覽

- **PDF / Excel**(需檔案解析,但靜態好抓):cyclist.org.tw、cycling.org.tw、taiwanbike.org
- **網頁表格**:Bravelog、iRunner、樂活
- **無任何平台提供有文件的公開 REST API** — 全靠 HTML 解析 / 檔案下載 / 逆向 XHR

---

## 四、建議的正規化資料欄位(節選)

賽事層:`race_id` / `race_name_raw` / `race_name_canonical` / `series` / `edition`(屆數) / `year` / `date_scheduled` / `date_actual`(處理延期) / `race_type`(公路賽/ITT/TTT/繞圈/登山爬坡/MTB/gravel/挑戰/認證) / `is_competitive` / `region` / `distance_km` / `elevation_gain_m` / `stage`

成績層:`category_raw` / `category_canonical` / `age_group` / `age` / `gender` / `athlete_id`(去識別化 hash) / `athlete_name_raw` / `team` / `bib` / `rank_overall` / `rank_gender` / `rank_division` / `finish_time`(大會) / `chip_time`(晶片淨時間) / `splits` / `avg_speed_kmh` / `dnf_status`

溯源層:`source_platform` / `source_url` / `source_format` / `scrape_method` / `scraped_at` / `confidence`

> 完整 40+ 欄位見 `recon-raw.json` 的 `synthesis.proposedSchema`

---

## 五、風險(實作前必讀)

1. **法遵 / 個資(PDPA)** — 成績含真實姓名+隊名+號碼+成績,屬個資法範疇。雖為公開成績,二次彙整成可搜尋資料庫/選手歷年追蹤有「目的外利用」爭議。**上線前建議:姓名去識別化(僅姓氏或 hash)、提供當事人下架機制、區分「公開競賽成績」與「需登入的個人會員歷史(不可爬)」。**
2. **賽事名稱不一致需正規化** — 三個「武嶺」分屬 TIS崇越盃/建大/NeverStop/96聯賽 是**四個不同賽事不可合併**;「KOM 登山王挑戰(10月正賽)」≠「KOM 登山王之路(春夏季)」;環花東有別名+屆數。
3. **組別命名不一致** — 菁英/競賽/精英;分齡 M30 vs M30-39 vs 30-34;96 四色戰衣、雪巴距離分組(經典/進階/終極)、認證等級(菜鳥/學長/鑽石)需建對照表。
4. **缺欄位** — 多數來源缺「實際年齡」(僅分齡組)、缺性別(需由組別反推)、缺晶片時間。
5. **認證型活動無名次**(TWB 雙塔520/北高360、TBA 認證騎乘)— 只有完賽認證,不可當競賽成績混入。
6. **歷史缺口 2010–2017** — 幾乎無整年賽曆部落格,需靠 cycling.org.tw 歷屆 + taiwanbike 早期 .xls 回填,且早期檔案 Big5 編碼 / 掃描 PDF 可能無文字層。
7. **反爬蟲技術阻擋** — bao-ming 詳情頁 302+Refresh;iBodyGo UA/Session 擋;ATSport 擋非台灣 IP;Bravelog/樂活需 Playwright。須先查 `robots.txt`、禮貌限速。

---

## 六、交叉驗證發現的「平台漏抓」賽事

部落格賽曆(CYCLINGTIME 2021、ensage 2026、Betery 2024、je22 2025、RACE ON 2026)比對後,以下在地/小型自辦賽**多不走七大平台**,報名/成績散落 FB 或臨時頁,屬高漏抓風險:

- 輪耀台灣公路系列賽(新玉門關/南化水庫繞圈/175咖啡/崁頭山,主辦 RIDEAWAY)
- Dirty Formosa / Gravel Fundo(礫石公路賽)
- 戀戀197、蘇花無敵海景123K、梅山36彎、八通關玉長公路、澎湖跳島101K
- 瘋系列(八卦山傳奇/谷關雪見硬漢)、美濃山城、LIVDAY 175咖啡
- (MTB,視範圍納入)瑟飛斯盃 / Dan Cup / XTERRA

> 用途:把部落格賽曆當「應存在賽事」母表,與平台抓到的賽事模糊比對,輸出「漏抓清單」。

---

## 七、建議下一步

1. **PoC 先做兩源**:
   - (a) `cyclist.org.tw`:靜態爬蟲抓 `results_list.asp?pno=1..13` → 收集 PDF 連結 → pdfplumber 解析 1–2 場(太平山王 / KOM)驗證欄位抽取。
   - (b) `Bravelog`:用 Chrome DevTools/Playwright 實測 1 個 `/contest/rank/{id}`,確認靜態可抓或需 headless,攔截 XHR 找 JSON 端點,測 `raceId × group × page` 遍歷與 `/athlete/{raceId}/{bib}` 明細。
2. **建兩張對照表**:賽事正規化表、組別正規化表(以部落格賽曆錨點賽事為種子)。
3. **法遵設計先行**:確立去識別化策略、下架政策、查各站 robots.txt 與條款。
4. **決定產品形態再定資料深度**(見下方決策點)。
5. **歷史回填**:2014–2026 以 cyclist.org.tw 為主;1998–2013 以 cycling.org.tw + taiwanbike 早期 .xls + 環台歷屆補齊,標記低 confidence。
