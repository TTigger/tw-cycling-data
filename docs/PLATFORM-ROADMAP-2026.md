# 台灣公路車資料平台 — 平台藍圖與開發計畫(定案版)

> **版本**:v2 定案 2026-07-03(v1 討論稿同日,經逐項審查後回填)
> **性質**:已定案的方向與分階段計畫。各項實作前仍走 superpowers spec → plan 流程;
> Phase 2 定大方向、Phase 3 只定觸發條件,細節屆時再議(見 §10 決策記錄、§11 未決事項)。

---

## 0. 定位

現在的 tw-cycling-data 是「台灣公路車**成績**的整合儀表板」;
下一階段定位為「**台灣自行車運動的開放資料基礎設施**」——
成績是第一根支柱,賽曆、路線地形、選手發展是同一平台的自然延伸。

**定位護欄(定案)**:做「台灣自行車的所有資料」,不做「所有自行車的資料」。
只收**在台灣發生、或台灣人參與**的成績;國際資料一律**官方來源**(UCI DataRide)
或**策展外鏈**(PCS 等),絕不大宗鏡像第三方資料庫。
環台賽屬於前者(在台舉辦的 UCI 2.1),世巡賽屬於後者。

---

## 1. 現況總檢(2026-07-03 全盤檢查)

### 1.1 資產盤點

| 資產 | 現況 |
|---|---|
| 資料規模 | 147,609 筆 / 161 場 / 27,309 位可追蹤選手 / 2009–2026 / 8 來源(+海外賽 8,724 筆獨立別集) |
| 管線品質 | 22 個 test 檔、140 個 pytest;`validate.py`;`discover.py` 缺漏雷達(3 行事曆 → 53 場缺口) |
| 身分歸併 | tsu_rider_id / uci_id 錨點 + 同名信心分級,全台唯一跨年生涯追蹤 |
| 前端紀律 | Astro 6 SSG + React islands;邏輯抽 `src/lib/*.ts` 配 vitest;最大元件 195 行 |
| 開放資料 | v1 靜態 JSON API、MCP server(7 工具)、CC BY 4.0 資料集 Release、CITATION.cff |
| 法遵 | PDPA 去識別化為文件化硬約束;`dataset.py` 有 ○ 字防呆 |
| 開發文化 | spec → plan(docs/superpowers)+ docs/learnings 知識庫 |

**市場位置**:全台唯一跨平台整合、可追蹤生涯、可比較落點的公路車成績站。護城河 = 只有我們有的台灣市民賽資料。

### 1.2 風險與技術債 → 處置對照

| # | 項目 | 嚴重度 | 處置(定案) |
|---|---|---|---|
| 1 | master 無異地備份(含 name_raw,單機存放) | 🔴 | **Phase 0-1 立即做**;加密快照(必加密,含 PII)→ R2,含還原演練 |
| 2 | 原始素材(PDF/HTML)未保存 | 🔴 | Phase 0-2:raw archive hook,從下次爬取起累積,不回溯 |
| 3 | 無 CI | 🔴 | Phase 0-3:GitHub Actions(pytest+vitest+astro check+build) |
| 4 | 185MB 資料進 git | 🟠 | 短期:資料/程式 commit 分離;Phase 2 D2 遷 R2;歷史 filter-repo 剝離(Q5=A) |
| 5 | viz.json 29MB 單體 | 🟠 | Phase 2:按年分片,預設載近 3 年;不上 parquet-wasm 等重型方案 |
| 6 | client:only 全站、SEO 弱 | 🟠 | Phase 2:僅賽事頁(214 個 SSG 殼)build 時內嵌前 20 名 + 關鍵統計;選手頁不動 |
| 7 | 搜尋 O(n) | ⚪ | 暫緩;實測未痛,出現卡頓再上 build-time 索引 |
| 8 | 人工對照表(RACE_KEY_CANONICAL/_SERIES) | 🟡 | 不消滅、資料化:搬 `data/curation/*.yaml` + 候選產生器例行化 + CI 未對映閾值警示;判斷權留人 |
| 9 | race_type 雙軌 | 🟡 | Phase 1 搭 D1 收斂:`classify()` 為唯一真相,merge 時寫入,爬蟲值降級參考欄 |
| 10 | 去重鍵脆弱 | 🟡 | Phase 1 搭 D1:鍵改 `(race_key, year, name_raw, round(finish_seconds))` + 丟棄列寫入 validation 稽核 |
| 11 | 欄位覆蓋率(gender 35%/date 31%/region 62% 缺) | 🟡 | date 用行事曆回填(Phase 1,天氣前置);region 半自動詞典;gender **不硬猜**(PDPA 語境不用名字推性別) |
| 12 | 文件漂移(SOURCES.md/MCP README) | 🟡 | Phase 0-5:統計塊改腳本生成 + CI 一致性斷言;人只維護敘述 |
| 13 | PoC 腳本混居 scrapers/ | 🟡 | Phase 0-4:git mv 至 `scrapers/archive/` |

---

## 2. 北極星:四資料支柱 × 六類服務對象

### 四個資料支柱

| 支柱 | 現況 | 目標 |
|---|---|---|
| ① 成績 | ✅ 核心已建成 | 補 ATSport/樂活/OCR 長尾 + 環台賽等在台 UCI 賽事(DataRide) |
| ② 賽曆 | 🌱 discover.py 3 行事曆 parser 僅用於找缺漏 | 反轉為對外服務:未來賽事索引 + ICS 訂閱 + 報名連結 |
| ③ 路線與地形 | 🌱 climb_profiles.json 人工海拔表 | 台灣爬坡百科:坡度剖面(DEM/OSM)+ 歷年最速 + VAM 分布 + 職業對標刻度 |
| ④ 選手發展 | 🌱 cycling.org.tw 349 筆含 UCI ID | 全錦賽/選拔歷史回填 + 台將海外足跡(策展 YAML + 外鏈 PCS,**不爬取**) |

### 六類服務對象

| 對象 | 平台提供 |
|---|---|
| 車友 | 現有全部 + 賽事預測/配速、賽曆訂閱、新成績 RSS;(觸發後)認領、通知 |
| 車隊 | 車隊頁 +(觸發後)可嵌入 widget、賽季報告 |
| 賽事主辦 | 人肉禮賓收檔 →(觸發後)上傳工具、賽後報告 |
| 研究者/媒體 | API/資料集/MCP + DOI、parquet、引用面英文、年度報告 |
| 政府/公協會 | 台灣公路車年度報告(參與/性別/年齡/地理趨勢) |
| AI 代理 | MCP(已有)+ 未來站內自然語言查詢(未排程) |

### 向大型站借鑑的結構課(PCS / FirstCycling / Strava)

1. **萬物皆頁面、頁頁互連**:前端慣例定案——任何實體名稱出現處皆為連結。
2. **URL 十年不變**:網頁 URL 比照 API v1 的穩定性承諾(現行 vercel.app 網域下即開始維持)。
3. **密表格 > 炫圖表、快就是體驗**:核心資料靜態直出(§1.2-6),圖表為增強層。
4. **有名字的招牌指標**(PCS Points 課):列 Phase 3 候選(Q9=B),評估時點 = 爬坡百科與預測器上線後。
5. **國家/賽季切面**(FirstCycling nation 頁):支柱④ 台將足跡頁的版型參考。
6. **使用者地標實體**(Strava segments 課):每座爬坡 = 穩定 ID + URL + 歷年榜,目標成為該坡的 canonical 連結。

技術棧不借(它們是老 PHP);借的是資訊架構與產品心法。

---

## 3. 架構五決策(全數定案)

### D1|SQLite canonical store ✅
- `master.db`:records / races / athletes / identity_links / takedowns 五表起步。
- DuckDB 定位為分析與 parquet 匯出工具(ATTACH sqlite),與 SQLite 並用不二選一(Q9 參照 §10)。
- **遷移劇本(C 型)**:① json→db / db→json 雙向轉換器 → ② 雙軌對賬:同一 master 走兩路徑跑全部 builder,v1 輸出 byte-identical(key 排序白名單)→ ③ builder 逐顆切讀 DB(一顆一 commit,每顆重對賬)→ ④ merge 原生寫 DB。任一步對賬不過即停在上一步;master.json 降級為匯出格式,保留一個賽季。
- 附帶收益:takedown 成表自動傳播;validate 大半變 SQL 斷言。

### D2|資料出版與 git 解耦 → Cloudflare R2(Q1=A)✅
- Phase 2 執行:上傳 v1 → `data-load.ts` base URL 環境變數切換 → 自灰度一週 → 正式切換 → 觀察一個資料更新週期 → 最後 `git filter-repo` 剝離資料歷史(Q5=A;破壞性、需重 clone,單獨約時間執行)。
- **⚠️ 網域復議檢查點(Q2 連動)**:R2 公開桶的 `r2.dev` 開發網址有速率限制、不宜正式環境;無自訂網域時的替代是 Vercel rewrite 代理(URL 不變但流量仍計 Vercel 頻寬,部分抵銷遷移效益)。**故定案:D2 動工前必須先復議網域決策**(見 §11)。在那之前 API base URL 維持 `tw-cycling-data.vercel.app/data/v1` 不變。

### D3|靜態優先 + 薄動態層 ✅
讀取路徑永遠靜態、CDN 可全量快取;動態層僅限寫入類(投稿/認領/下架表單),Cloudflare Workers + 佇列;**端點只寫佇列、絕不直接動資料**,人工核可後才進管線;對外表單一律掛 Turnstile。

### D4|管線單一入口:Python CLI ✅
`python -m pipeline refresh [--source X] [--skip-scrape]`(非 Makefile;Windows 節點友善、順序規則可寫成有狀態檢查)。每步宣告前置條件、失敗斷點續跑;內建「race key 變動清 race/ 目錄」「manifest 最後跑」等規則。

### D5|raw archive ✅
`common.py` 共用 `archive_response()` hook;結構 `raw/{source}/{YYYY-MM-DD}/{原檔名}` + manifest(URL+hash);同步 R2 冷層,**與 master 加密備份同桶不同前綴**(Q3=A)。

### 目標架構圖

```
台灣節點(住宅IP;行事曆403與ATSport封鎖之實測解法)     雲端
┌────────────────────────────┐    ┌──────────────────────────────┐
│ scrapers ──► raw archive ──┼──► │ R2: raw/(原始快照,冷層)       │
│    │                       │    │ R2: backup/(master.db 加密)   │
│    ▼                       │    ├──────────────────────────────┤
│ master.db (SQLite)         │    │ Phase 2 後:                   │
│    │  merge/identity/      │    │ R2+CDN: /data/v1/*.json      │◄── 前端/API/MCP
│    │  takedown 皆入庫       │    │ (動工前先復議網域,見 §11)      │
│    ▼                       │    ├──────────────────────────────┤
│ build_*(輸出契約不變) ──────┼──► │ GitHub ─► CI ─► Vercel       │◄── 使用者
│ git push(純程式碼)          │    │ Workers(投稿/下架佇列,Phase 2) │
└────────────────────────────┘    └──────────────────────────────┘
```

---

## 4. 資料擴展(定案優先序)

### 4a. 補洞(支柱①)

| 優先 | 項目 | 定案 |
|---|---|---|
| 1 | **ATSport** | Phase 1 資料線首位;在台節點跑(TCP 封鎖只擋境外);解「搬家型缺口」(戀戀197-2025 等) |
| 2 | **樂活成績站** | Phase 1;Playwright(runnet 先例) |
| 3 | **iBodyGo** | Phase 1 花 1 天估量再決定;量不足即登錄「已評估、量不足」結案 |
| 4 | **環台賽缺口驗證** | Phase 1 半天:確認 master 是否缺 Tour de Taiwan → Phase 2 經 UCI DataRide 收錄(Q10=A) |
| 5 | **cycling.org.tw 歷史回填** | Phase 2;支柱④地基(137 檔 2009–2026) |
| 6 | **FB/主辦頁長尾(53 場)** | 維持不爬 FB;Phase 2 起 OCR 投稿「無 UI 版」(Issue 模板+人工視覺模型入庫),驗證需求後才蓋端點 |
| 7 | tsu 2026 例行補抓 | 併入 pipeline refresh 預設流程 |

### 4b. 新資料類型

1. **賽曆服務 + ICS**(Phase 1,CP 值最高單項):discover parser 反轉輸出 → `/calendar` 頁 + `calendar.json` + ICS 訂閱檔;「找下一場」高頻需求 + 內連歷年成績頁形成飛輪。
2. **台灣爬坡百科**(Phase 2):首發 5 座做深(Q8 定案:**武嶺東進(KOM 線)、武嶺西進、風櫃嘴、陽金 P 字、太平山**)——坡度剖面 + 歷年最速 + VAM 分布 + 「你 vs 職業」刻度尺 + 穩定 URL。
3. **賽事天氣回填**(Phase 1 末):前置 = date 回填;中央氣象署開放資料;先只做賽事頁顯示,入模型等資料厚再說。
4. **台將國際足跡**(Phase 3,硬依賴 4a-5):策展 YAML(選手×賽季×重點成績×PCS 外鏈),**不爬取 PCS**。
5. **職業對標常數表**(隨 4b-2):手工維護 JSON(職業 VAM 區間、KOM 職業組歷年、W/kg 分級),供爬坡百科與預測器引用。
6. **年度報告 2026**(定時項:11 月初動工、12 月中發布):配 DOI;**第一年獨立掛名**,以成品為籌碼談 2027 合作。

---

## 5. 服務擴展(定案)

| 項目 | 定案 |
|---|---|
| **目標賽事預測器** | Phase 1 產品線;benchmarks+difficulty+爬坡資料現成,零後端;把「查過去」變「規劃未來」 |
| **新成績通知** | Phase 1 從 RSS/Atom 起(build 時 diff 產 feed,零維運);它是未來一切推播的事件源 |
| **成績認領/帳號** | 不排程;觸發制(§7 Phase 3 表);若做:魔術連結,無密碼;認領僅解鎖本人視圖,公開輸出永遠遮罩 |
| **LINE bot** | 暫緩;事實記錄:LINE Notify 已於 2025-03 終止,Messaging API 免費層 200 則/月,推播成本結構不成立;先以 RSS+ICS 滿足訂閱 |
| **主辦上傳工具** | 先「人肉禮賓版」:coverage 頁放一句「主辦願提供成績檔請寄來」,人工入庫;工具化走觸發制 |
| **可嵌入 widget** | Phase 3 觸發制;前置:URL 承諾(視網域復議結果) |
| **英文 i18n** | 拆兩段:**引用面**(API docs/DATASET/年度報告英文)Phase 2;**全站 UI 雙語**明文推遲 Phase 3 後 |
| **DOI + parquet** | 前移:DOI = Phase 0-6(Zenodo GitHub 整合);parquet = D1 完成後 DuckDB 一行匯出 |

---

## 6. 開發流程(定案)

### 6.1 兩條軌道

```
資料軌(例行、可排程、台灣節點):
  scrape → raw archive → merge → validate → build_* → 發佈(Phase 2 前 git commit;後 R2 上傳)
  不含程式邏輯變更;跑的永遠是已定案管線
功能軌(開發、開發機):
  spec → plan → branch → 實作 → 驗證閘門 → PR → merge
  功能落地後,才出現在下一次資料軌產出
```

### 6.2 三種流程型態

| 型態 | 適用 | 流程 |
|---|---|---|
| A. 機械工 | 備份、CI、目錄整理、sitemap、feed | 不寫 spec;branch → PR,PR 描述即文件 |
| B. 標準功能 | 新頁面、新 builder、新資料源 | 完整 spec → plan → tasks → PR(現行 superpowers 流程) |
| C. 遷移工程 | D1 SQLite、D2 資料出 git | spec + **遷移劇本**:雙軌並行 → 對賬 → 切換 → 回退條件 |

### 6.3 標準功能生命週期(B 型)

```
1. spec(docs/superpowers/specs/)必含:目標/非目標、資料流、PDPA 影響、API 契約變更
2. plan 拆 tasks(2–5 個,各自可獨立 commit)
3. 實作:每 task = 實作 → 測試(pytest/vitest)→ commit
4. 驗證閘門:astro check(0 errors)→ vitest → pytest → astro build → 瀏覽器實測
5. 收尾:動 API → manifest+docs/API.md 同步;踩坑 → docs/learnings/;動欄位 → SOURCES/DATASET 檢查
6. PR → merge → 下次資料軌 refresh 帶出產物
```

### 6.4 新資料源劇本

```
PoC 探勘(一次性,事後進 archive/)→ 確認量與欄位
→ spec(欄位對映、去重策略、預估筆數)→ parser + pytest(快取樣本,不打網路)
→ 接 merge(SOURCE_PREFIXES)→ validate 全量 → SOURCES.md 登錄 → 全站 rebuild
驗收:增量 ≈ 預估;validate 無新增異常;抽 3 場人工對照原始成績
```

---

## 7. 分階段路線圖(定案)

### Phase 0|止血(~2 週,全 A 型)

| # | 項目 | 驗收條件 |
|---|---|---|
| 0-1 | master+raw 加密備份腳本(age/7z-AES → R2)★當天做 | 完成一次**還原演練** |
| 0-2 | raw archive hook 進 common.py | 下次爬取起自動落原檔 |
| 0-3 | GitHub Actions CI(pytest+vitest+astro check+build) | PR 必經;shallow clone+快取控時長 |
| 0-4 | scrapers/archive/ 整理(git mv ~20 個 PoC 檔) | 正式目錄僅剩 pipeline 會呼叫的腳本 |
| 0-5 | 文件統計改生成(SOURCES.md 統計塊、MCP README 工具表) | CI 斷言生成值一致 |
| 0-6 | Zenodo DOI 開關 | 下個 dataset release 自動配 DOI |
| 0-7 | sitemap + robots | 527 個 SSG 頁全進 sitemap |
| 0-8 | pipeline CLI 骨架(串現有步驟,不改邏輯) | 一鍵跑完 refresh |

(原 0-6 網域項依 Q2 移除,復議點見 §11。)

### Phase 1|地基 + 快贏(雙線並行,6–8 週;Q4=A)

```
資料線                                產品線
w1-2  ATSport(PoC→正式,新源劇本)       w1-2  賽曆服務 + ICS(B)
w3-4  樂活成績站(Playwright)           w3-4  目標賽事預測器(B)
w5-7  D1 SQLite 遷移(C,§3 劇本)        w5    date 回填(行事曆→master)
w8    race_type 收斂 + 去重鍵修正       w6    天氣回填(CWA,賽事頁顯示)
      (搭 D1 同次 schema 變更)          w7-8  RSS feed(A)+ iBodyGo 評估(1天)
零星   環台賽缺口驗證(半天,排任一空檔)
```

出口驗收:D1 對賬 byte-identical;ATSport 入庫;賽曆頁與預測器上線;RSS 可訂閱。

### Phase 2|平台化(~一季)

| 項目 | 要點 |
|---|---|
| **網域復議** ← 本階段第一件事 | D2 的前置(§3-D2、§11) |
| D2 資料出 git(C 型) | R2 上傳→base URL 切換→灰度→切換→觀察一週期→最後 filter-repo 剝離(Q5=A,單獨約時間) |
| OCR 投稿無 UI 版 | Issue 模板 + 人工視覺模型入庫;需求驗證後才蓋 Workers 端點 |
| 爬坡百科首發 5 座 | Q8 定案清單;含職業對標刻度尺 |
| viz.json 按年分片 | 探索頁預設近 3 年 |
| 賽事頁 SSG 內嵌前 20 名 | SEO 主攻;僅賽事頁 |
| 引用面英文 | API docs/DATASET/報告模板 |
| cycling.org.tw 歷史回填 | 支柱④地基 |
| 環台賽 UCI DataRide 收錄 | 只收台灣舉辦場次(Q10=A) |
| 年度報告 2026 | 11 月初動工、12 月中發布、配 DOI、獨立掛名 |

### Phase 3|生態系(不排時程,全觸發制;Q7 照案)

| 項目 | 觸發條件 |
|---|---|
| 成績認領/輕量帳號 | OCR 投稿累積 ≥30 件,或「想跨裝置同步」回饋 ≥10 次 |
| LINE bot | ICS 訂閱 ≥100 且有分攤訊息費的合作方 |
| 主辦上傳工具 | 人肉禮賓版累積 ≥3 個主辦重複投件 |
| 可嵌入 widget | 車隊/主辦主動詢問 ≥3 次(前置:URL 承諾,視網域復議) |
| 台將國際足跡完全體 | cycling.org.tw 回填完成(硬依賴) |
| 招牌綜合指標(Q9=B) | 爬坡百科 + 預測器上線後評估 |
| 全站 UI 英文 i18n | 引用面英文上線後,視國際流量再議 |

### 階段檢查點(每 Phase 結束,定案下一階段)

固定四問:① 上階段驗收全過?② 資料規模/流量變化需調優先序?③ Phase 3 觸發條件亮了嗎?④ 來源地圖有變(SOURCES.md diff)?——答完才寫下階段第一份 spec。

---

## 8. 資料軌節奏(Q6=C:A 起步 → B 演進)

```
起步(pipeline CLI 穩定前):固定週更(賽季中)/ 每月(離季)
  python -m pipeline refresh
  人工介入點僅二:validate 亮紅、race_merge 候選核可
演進(CLI 穩定後):行事曆驅動——discover 見未來 7 天有賽事才提頻
每月:discover 缺漏雷達 review(既有排程保留)
每季:SOURCES.md 敘述巡檢、依賴升級(Astro/ECharts)、備份還原演練
每年:年度報告、DATASET release 改版、CITATION.cff 版號
```

---

## 9. 原則與護欄(不隨擴張改變)

1. **PDPA 三鐵律**:公開輸出僅遮罩名+加鹽 ID;聚合 n≥20;下架傳播至所有出口(site/API/dataset/MCP)。新功能 spec 必含「PDPA 影響」節。備份含 name_raw **必加密**。
2. **成績僅供參考,以主辦公告為準**;預測/報告類產出同掛免責。
3. **靜態優先**:動態層只做寫入佇列;成本維持一人非營利可負擔(R2+Vercel+Workers 免費額度)。
4. **來源關係**:爬蟲節流、標註來源、不做來源站競品;方向是從「我們去爬」走向「主辦自願供給」。
5. **開放為預設**:新資料類型一律同時進 v1 API 與資料集 Release。
6. **國際資料紅線**(2026-07-03 新增):只收在台發生或台灣人參與;官方來源或策展外鏈;不鏡像第三方資料庫。
7. **前端互連慣例**(新增):任何實體名稱出現處皆為連結;網頁 URL 比照 API v1 穩定性承諾。

---

## 10. 決策記錄(2026-07-03)

| # | 決策 | 裁決 |
|---|---|---|
| Q1 | 物件儲存 | **A. Cloudflare R2** |
| Q2 | 網域 | **暫不購買,沿用 tw-cycling-data.vercel.app**;復議條件見 §11 |
| Q3 | 備份目的地 | **A. 與資料同一 R2 桶**(不同前綴) |
| Q4 | Phase 1 排程 | **A. 雙線並行**(6–8 週) |
| Q5 | git 資料歷史 | **A. filter-repo 剝離**(Phase 2 末、單獨執行) |
| Q6 | 資料軌節奏 | **C. 固定週更起步 → 行事曆驅動演進** |
| Q7 | Phase 3 觸發值 | **照案**(§7 表) |
| Q8 | 爬坡百科首發 | **照案**:武嶺東進、武嶺西進、風櫃嘴、陽金 P 字、太平山 |
| Q9 | 招牌綜合指標 | **B. Phase 3 候選**(爬坡百科+預測器後評估) |
| Q10 | 環台賽 | **A. Phase 1 缺口驗證 → Phase 2 DataRide 收錄** |
| — | 架構 D1/D3/D4/D5、各 ✓ 項 | 全數照案採納 |
| Q11 | Supabase 取代 SQLite?(2026-07-03 追議) | **否,D1 維持 SQLite**。理由:name_raw 不上第三方雲(PDPA 姿態)、免費層限制(7 天閒置暫停/egress ~5GB/無自動備份)正中本專案要害、與 D3 靜態優先哲學相反。Supabase 改列動態層候選(見 §11-4) |

## 11. 未決事項(掛明確復議條件)

1. **網域**(Q2):復議時點 = **Phase 2 D2 動工前**(R2 公開桶正式環境實務上需自訂網域;替代方案 Vercel rewrite 代理會抵銷部分頻寬效益)。屆時三選一:買網域 / rewrite 代理 / 延後 D2。widget 等「URL 承諾」類功能同受此連動。
2. **招牌綜合指標**:名稱、公式、政治學(會不會引發排名爭議)——觸發後另開 spec。
3. **站內自然語言查詢**(AI 服務對象):未排程,MCP 使用數據累積後再議。
4. **動態層技術選型(Workers+D1 vs Supabase)**:復議時點 = Phase 3 認領/投稿端點觸發時。預設傾向 Workers+D1(與 R2 同生態、免費層不暫停);**若帳號/魔術連結體驗成為重點,Supabase Auth 列正選候選**。
5. **瀏覽器內 SQL 查詢(點子備忘)**:parquet 放 R2 + DuckDB-WASM 讓使用者在靜態頁面直接對資料集下 SQL——零後端、零 egress 費、符合靜態優先。Phase 3 之後視需求。
