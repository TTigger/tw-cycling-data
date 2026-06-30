# 台灣公路車賽事資料專案 (tw-cycling-data)

> English: **[README.en.md](README.en.md)** ｜ 資料來源登錄表(已爬/受限/發現):**[SOURCES.md](SOURCES.md)**

收集、清洗、正規化台灣公路車賽事成績(2009–2026),做成資料庫 → 互動視覺化儀表板,已部署為 Vercel 靜態網頁。

## Public API

唯讀 JSON API(CC BY 4.0,去識別化)。Base:`https://tw-cycling-data.vercel.app/data/v1`,入口 [`manifest.json`](https://tw-cycling-data.vercel.app/data/v1/manifest.json)。端點與 schema 見 [`docs/API.md`](docs/API.md)。也提供 Python MCP server(見 [`mcp-server/`](mcp-server/))。

## Open Dataset

去識別化逐筆成績(147,609 筆,2009–2026,CC BY 4.0)可下載:見 [Releases](https://github.com/TTigger/tw-cycling-data/releases) 與 [DATASET.md](DATASET.md)。已刪除外部識別碼;當事人可於 [Issues](https://github.com/TTigger/tw-cycling-data/issues) 申請移除。

## 這個專案是什麼、給誰用(Why)

台灣的公路車成績**散落在 4 個以上的平台**,而且大多「只能逐場/逐筆查」,沒有一個地方能跨賽事比較、追蹤一位選手的生涯。本專案把這些公開成績**彙整、去識別化、正規化**,做成**免費、開源、互動**的成績探索站——目前是**全台唯一**把分散資料整合起來、還能分析的工具(現有 **147,609 筆 / 130 場 / 2009–2026 / 8 來源**,另收海外賽)。

**十頁各自的作用:**

| 頁面 | 功能 | 對誰、有什麼用 |
|---|---|---|
| **總覽** | KPI、賽季行事曆熱圖、逐年趨勢、女子參與、組別組成 | 一眼看懂台灣公路車生態 |
| **探索** | 多維篩選 → 完賽時間分布、分齡箱形圖、競爭強度、距離vs速度 | 想自己切資料分析的人 |
| **賽事** | 排行榜、領獎台、**「你贏過多少 %」percentile**、跨年變化、車隊戰力、**賽事 DNA 指紋(6 軸雷達、可並排比較、找相似賽事)**、**賽事嚴苛度(完賽異常推估)**、**完賽率(FIN/DNF/DNS,目前繞圈賽有)**、賽事搜尋 | **車友**:找自己那場、看落點、看歷年變快沒 |
| **系列** | 多站系列(96聯賽/捷安特/崇越/雪巴大滿貫/GravelFundo/TCU…)**賽季綜合表現總排** | 看一整季全貌、不再散在各站 |
| **選手** | 22,035 位可追蹤選手、搜尋、**歷年生涯、進步軌跡、賽季回顧、跨年難度校正、爬坡vs平路雷達、騎乘分身、1v1 對比、交手戰績(宿敵)、戰力卡(白金/金/銀/銅分級·可上傳照片)** | 追蹤一位車手整段生涯、跟對手勝負 |
| **車隊** | 車隊名單、隊史最佳戰績、活躍年表(805 隊,門檻 ≥4 位可追蹤車手、≥2 場) | 看一支車隊的陣容與戰績 |
| **傳奇爬坡** | **VAM 爬坡指數**、單場+跨賽爬坡王、推算 W/kg、場地最速榜 | 爬坡咖:武嶺/KOM 跨年跨賽同尺比較 |
| **洞察** | **紀錄牆、巔峰年齡曲線、突破之星、賽事星等、成績換算器、地理熱點** | 趨勢與冷知識 |
| **海外賽** | 富士山等(獨立收錄,不混入台灣統計) | 海外賽事 |
| **資料涵蓋** | 資料來源透明度、行事曆缺漏賽事清單 | 看我們收了什麼、還缺什麼 |

**核心價值**:把原本「散落、只能逐筆查」的成績,變成「**可搜尋、可追蹤生涯、可比較落點**」的社群資源。對車友最實在的是 percentile(我贏過多少人)、生涯追蹤、爬坡指數、宿敵戰績——這些原本不存在。

**設計原則**:PDPA 去識別化(僅遮罩名 `李○明`,公開檔無真實姓名);非營利;成績僅供參考,以主辦公告為準;當事人可申請下架。涵蓋面誠實揭露於 **[SOURCES.md](SOURCES.md)**(已爬/受限/缺口)。

## 使用者操作總覽

進站後使用者可做的事:

| 操作 | 在哪 | 說明 |
|---|---|---|
| **搜尋**(頁面/賽事/選手) | 全站命令列(`Ctrl/⌘+K`) | 打字找特定一場賽事或一位車手;選手以遮罩名為搜尋鍵(見下方說明) |
| **多維篩選切資料** | 探索 | 依年份/系列/組別/性別/分齡篩出完賽時間分布、分齡箱形圖、競爭強度等 |
| **選賽事看排行榜 / percentile** | 賽事 | 名次、領獎台、切分組;看「你贏過多少%」的落點 |
| **比較兩場賽事 DNA / 找相似賽事** | 賽事 | 選第二場並排 6 軸雷達,或點相似賽事跳轉 |
| **看一場完賽率** | 賽事(繞圈賽) | 完賽/報到人數、未完賽、未出發(目前 TCU 繞圈賽有 status 資料) |
| **追蹤選手生涯** | 選手 | 歷年成績、進步軌跡、賽季回顧、跨年難度校正 |
| **1v1 對比 / 宿敵戰績** | 選手 | 兩位車手並排比較、交手勝負紀錄 |
| **找騎乘分身** | 選手 | 列出指紋最相似的同性別車手 |
| **戰力卡(可上傳照片)** | 選手 | 白金/金/銀/銅分級的個人戰力卡 |
| **系列賽季總排** | 系列 | 多站系列的賽季綜合名次 |
| **爬坡 VAM / 推算 W/kg** | 傳奇爬坡 | 武嶺/KOM 跨年跨賽同尺比較、場地最速榜 |
| **我的最愛 / 深色模式 / 行動版抽屜** | 全站 | localStorage 收藏、明暗主題、手機導覽抽屜 |
| **分享** | 全站 | 每頁 OG 分享圖 + meta;賽事頁為可被搜尋的 SSG 頁 |

**關於選手搜尋(去識別化下的限制)**:公開資料只有遮罩名(`林○宇`),搜尋以遮罩名比對。搜尋鍵會**忽略遮罩符號**,所以打姓氏「林」、尾字「宇」或可見首尾「林宇」都能命中;但打不出被遮的中間字,且**同名碰撞**(`林冠宇`/`林家宇` 皆遮為 `林○宇`)需靠下拉中的年份、場次、車隊、UCI 標記來辨識,點進選手頁另有同名信心標記。

## 目錄

```
recon-report.md / recon-raw.json   資料源版圖偵查
poc-findings.md                    爬蟲 PoC 可行性實證
cycorg-poc-findings.md             cycling.org.tw 國家級源探勘
docs/superpowers/                  設計 spec 與實作計畫(brainstorm→plan)
scrapers/
  common.py            共用:HTTP、組別/性別/分齡正規化、姓名遮罩(PDPA)、賽名 race_key、統一紀錄
  normalize.py         跨源正規化:race_class(頒獎組別類型)+ series(賽事系列)對照表
  cyclist_crawl.py     ★ 正式爬蟲 cyclist.org.tw(支援 --years 歷史回填、--out)
  bravelog_calendar.py ★ Bravelog contestId 探索(/search API)+ 自行車賽分類
  bravelog_crawl.py    ★ 正式爬蟲 Bravelog(contest→raceId子賽事→分頁,per-contest 快取)
  cycling_crawl.py     ★ 正式爬蟲 cycling.org.tw 國家級 PDF 成績冊(含 UCI ID)
  cyclist_league.py    ★ 臺灣自行車聯賽 ITT(cyclist.org.tw results_txt 落地頁 → 成績公告 PDF;桃園繞圈賽等)
  tsu_crawl.py         ★ 正式爬蟲 tsu.com.tw(/race?y= 年份×分頁 → /race/result 表頭對映;含 TCU 選手 ID)
  merge.py             ★ 合併所有來源 → master 資料集(套用 normalize、跨源去重)
  validate.py          資料品質驗證(重複/時間/名次倒置/覆蓋率/年份漂移)
  build_viz.py         ★ master.public → 前端資料檔(viz/races/race;含 pytest)
  build_athletes.py    ★ master → 選手追蹤資料(athletes 索引 + athlete/<id>:身分歸併、同名信心、爬坡王 climb_vam、專長雷達 traits、交手戰績 rivals、騎乘分身指紋 athlete_features;含 pytest)
  build_insights.py    ★ master → insights.json(巔峰年齡曲線/突破之星/賽事星等/地理熱點;含 pytest)
  build_difficulty.py  ★ master → race_difficulty.json(跨年難度校正:每場每年中位數+難度係數;含 pytest)
  build_race_dna.py    ★ master → race_dna.json(賽事 DNA:每場每年 6 軸跨站正規化指紋 + 找相似賽事;含 pytest)
  build_series.py      ★ master → series.json(賽事系列總標:多站系列賽季綜合表現總排;含 pytest)
  build_fonts.py       ★ 自架字型瘦身:擷取站上實際用到的字 → 子集化 5 種字型為 web/public/fonts/*.woff2(免 Google Fonts、CJK 不再分 ~25 個子集請求)
  discover.py          ★ 缺漏發現:爬公開行事曆 → 與 master 比對 → 輸出「缺漏賽事 + 推測來源」(不靠人工列舉)
  overseas_runnet.py   海外賽(runnet headless)→ web/public/data/overseas(獨立別集,不進 master)
  race_type.py         賽事類型分類(爬坡/繞圈/計時/公路;含 pytest)
  summarize.py         產生單一資料集統計摘要
  *_poc.py / *_inspect.py / *_probe.py / bravelog_parse.py   PoC/探勘一次性腳本(保留參考)
data/processed/
  master.public.json     ★ 去識別化合併資料(供前端)
  *_summary.json                   統計摘要
web/                               前端 Astro 儀表板(見下)
```

## 資料管線(Python)

```powershell
pip install -r requirements.txt

# Phase 1a — cyclist.org.tw
python scrapers\cyclist_crawl.py                      # 全量 2024–2026(PDF 已快取則很快)
python scrapers\cyclist_crawl.py --years 2014-2023 --out cyclist_2014_2023.json  # 歷史回填

# Phase 1b — Bravelog
python scrapers\bravelog_calendar.py 2024 2025 2026   # 1) 建自行車賽 contest 工作清單
python scrapers\bravelog_crawl.py                     # 2) 爬成績(可續跑;--limit N 冒煙)

# 合併 + 驗證
python scrapers\merge.py                               # 合併所有來源 → master
python scrapers\validate.py master.json      # 資料品質檢查
```

## 前端儀表板(`web/`)

Astro + React islands + Tailwind v4 + ECharts,Claude 暖色風,10 頁(深色模式、我的最愛、行動版抽屜):
- `/`(總覽)、`/explore`(探索)、`/overseas`(海外賽)、`/coverage`(資料涵蓋)
- `/teams`(**車隊頁**:車手名單、隊史最佳戰績、活躍年表,`teams.json` + `team/<id>.json`)
- `/race`(賽事詳情 + 排行榜/percentile + **賽事 DNA 指紋**:6 軸跨站正規化雷達、可並排比較、**找相似賽事**最近鄰,`race_dna.json` + **賽事嚴苛度**:以完賽人數/時間 vs 歷年推估,`race_difficulty.json`)
- `/series`(**賽事系列總標**:多站系列賽季綜合表現總排,`series.json`)
- `/athletes`(選手追蹤 + **騎乘分身**:指紋最近鄰相似選手,`athlete_features.json` + **跨年難度校正**:原始 vs 校正後完賽時間,`race_difficulty.json` + **1v1 對比** + 爬坡手vs平路手雷達 + 交手戰績宿敵)
- `/climbs`(傳奇爬坡 + **爬坡指數 VAM**:單場 VAM 排行 + 跨賽「爬坡王」榜 + 推算 W/kg + 場地最速榜,基於策展的 `climb_profiles.json` 海拔對照表)
- `/insights`(數據洞察:**紀錄牆**(最大場面/最多出賽/冠軍/連續年/回頭王,去識別化)、巔峰年齡曲線、突破之星、賽事星等、成績換算器、賽事地理熱點)

```powershell
python scrapers\build_viz.py            # master.public → web/public/data/{viz,races,race/*}.json
python scrapers\build_athletes.py       # master → athletes/athlete/<id>/climb_vam.json(含雷達+宿敵)
python scrapers\build_insights.py       # master → insights.json(洞察頁:年齡曲線/突破之星/星等/地理)
python scrapers\build_difficulty.py     # master → race_difficulty.json(選手頁:跨年難度校正)
python scrapers\build_race_dna.py       # master → race_dna.json(賽事頁:賽事 DNA 指紋雷達 + 找相似賽事)
python scrapers\build_series.py         # master → series.json(系列頁:多站賽季綜合總排)
python scrapers\build_teams.py          # master → teams.json + team/<id>.json(車隊頁)
python scrapers\build_viz.py            # 亦產 overview.json(首頁預聚合)+ race_crossyear.json(賽事跨年)
python scrapers\build_og.py             # → web/public/og.png(OG 分享圖,需重跑於統計變動後)
python scrapers\build_fonts.py          # 子集化自架字型 → web/public/fonts/*.woff2(需 data/_fonts_src 內的來源 TTF)
cd web
npm install
npm run dev                             # http://localhost:4321
npm test                                # vitest 單元測試
npx astro check                         # 型別檢查
npm run build                           # 產出 web/dist(靜態)
```

## 部署(Vercel,GitHub 自動)

- 資料檔 `web/public/data/*` **已納入版控**(部署 artifact;Vercel build 無 Python 無法重生)。更新資料:重跑 `python scrapers\build_viz.py` 後 commit。
- Vercel 設定:**Root Directory = `web`**、Framework = Astro(自動偵測)、Output = `dist`,純靜態無需 adapter。
- push 到 GitHub(private)→ Vercel 連結 repo → 每次 push 自動部署。

## 統一資料欄位(每筆 = 一位選手在一場賽事的成績)

`source_platform` `source_url` `source_format` ｜ `race_name_raw` `race_name_canonical` `race_key`(去重鍵)`year` `date` `race_type` `region` ｜ `result_label` `category_raw`(原始組別)`gender`(M/F/None)`age_group`(`24-35`/`U15`/`MASTER`…)`age_band`(十年制粗分級)｜ `rank_overall` `bib` `uci_id` `tsu_rider_id`(選手身分錨)｜ `name_raw`(內部)`name_masked`(`李○明`,保留首尾,PDPA)`nationality` `team` ｜ `finish_time` `finish_seconds` `splits` ｜ `scraped_at`

## 重點與限制

- **cyclist.org.tw**:列表 → 賽事頁 → PDF → pdfplumber **逐行文字** 解析;**欄位順序逐 PDF 不同**,解析器讀中文表頭自動判斷(`detect_order`);組別碼直接給性別+分齡;跨分類以 `(race_key,year,bib,finish)` 去重。
- **Bravelog**:`/search` JSON API 探索 contest → server-rendered rank 頁分頁解析(無需 JS)。
- **gender=None ≈ 16%** 多為正常(U13–U15/挑戰組/電輔車 資料源未編碼性別);Bravelog 多市民賽不分組。
- **PDPA**:公開輸出僅用 `*.public.json`(無 `name_raw`)、顯示遮罩姓名;網站頁尾標註來源與下架說明。
- **分齡組正規化**:原始 `age_group` 跨源混用兩套制度(5 歲制 20/25/30… 與範圍式 24-35/40-49),`normalize.age_band()` 統一為十年制粗分級(`U19/19-29/30-39/40-49/50-59/60+/MASTER`)供探索頁篩選與箱形圖;原始 `age_group` 保留於各場成績。
- **race_key / 組別類型** 為保守正規化;賽名對照表仍待精修(三個「武嶺」不可合併、KOM 挑戰≠登山王之路)。
- **排行榜名次**:競技賽的 `category_raw` 會把多個分項(公路賽+計時賽)併在同一組,且來源 `rank_overall` 是分項內名次而非總排。排行榜因此**依 `(組別, 分項)` 分組、組內依完賽時間重排 1..N** 呈現,並附 `原始` 欄保留來源名次——所以顯示名次可能與主辦官方名次不同(以主辦公告為準)。詳見 [docs/learnings/race-leaderboard-ranking.md](docs/learnings/race-leaderboard-ranking.md)。

## 選手追蹤的身分識別(Phase 3)

- **穩定選手 ID 為強錨點**:tsu 的 `tsu_rider_id`(TCU-…)與 cycling 的 `uci_id`,姓名唯一對應到一個 ID 時即合併其全部成績並標 high 信心——這讓換隊/跨年的生涯能正確歸併(例:一位 2013–2026、跨 8 隊的女將靠 TCU ID 正確合為一人)。
- **無 ID 者以 `name_raw` 為主鍵**串接生涯(車隊逐年變動,硬用車隊當複合鍵會把換隊選手拆散)。
- **同名信心標記**:跨多支車隊、或同一身分出現 M+F 性別不一致 → 標 `low`(高同名風險),UI 加註提醒。
- **PDPA**:輸出僅含遮罩姓名(`林○宇`,保留首尾)、加鹽不可逆 `athlete_id`、`has_uci` 布林;不公開 `name_raw` 與原始 UCI ID。索引僅 ≥2 場的可追蹤選手;每位歷程檔點擊才載入。

## 下一步

- 自訂網域(若未來綁定,需更新 `astro.config` 的 `site`;目前指向 `tw-cycling-data.vercel.app`)。
- 賽名/組別正規化續精修(候選產生器 `scrapers/suggest_race_merges.py` 產人工核可表)。
- cycling.org.tw 舊年份寬表格式回填(目前僅 2025 國家級源)。
- 維護者請先讀 `docs/learnings/` 與 `AGENTS.md`(這次大改的非顯而易見決策與陷阱)。
