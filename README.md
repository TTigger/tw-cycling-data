# 台灣公路車賽事資料專案 (tw-cycling-data)

> 🌐 English: **[README.en.md](README.en.md)**

收集、清洗、正規化台灣公路車賽事成績(2015–2026),做成資料庫 → 互動視覺化儀表板,已部署為 Vercel 靜態網頁。

## 進度

| 階段 | 狀態 |
|---|---|
| 資料源偵查(16-agent 工作流) | ✅ `recon-report.md` / `recon-raw.json` |
| 爬蟲可行性 PoC(cyclist + Bravelog) | ✅ `poc-findings.md` |
| **Phase 1a:cyclist.org.tw 管線(2024–26)** | ✅ **3,913 筆 / 12 場**(競技型,性別 83%+分齡 95%) |
| **Phase 1b:Bravelog 管線(2018–26)** | ✅ **44,850 筆 / 61 場**(市民/挑戰型;已排除鐵人三項) |
| **Phase 1d:cycling.org.tw 國家級源** | ✅ 全國公路錦標賽 **203 筆(2025,含 UCI ID)**;舊年份寬表格式擱置 |
| 正規化 + 合併 + 驗證工具層 | ✅ `normalize.py` / `merge.py`(年份無關、自動納源) / `validate.py` |
| **★ 合併 master 資料集** | ✅ **56,329 筆 / 2015–2026 / 72 場 / 3 來源**,已去識別化 |
| **Phase 2:互動視覺化儀表板(4 頁)** | ✅ `web/`(總覽/探索/賽事/傳奇爬坡;Astro+React+ECharts,Claude 風,RWD) |
| **部署 Vercel** | ✅ 已上線(Root Directory=`web`,push 自動部署) |
| **Phase 1c:歷史回填(cyclist 2014–23 + Bravelog 2018–23)** | ✅ +7,363 + 歷史 Bravelog |
| **Phase 3:選手歷年追蹤(姓名為主、車隊+UCI 為輔)** | ✅ `/athletes` **11,205 位可追蹤選手**(≥2 場);進步軌跡+歷年成績+同名信心標記 |

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
  merge.py             ★ 合併所有來源 → master 資料集(套用 normalize)
  validate.py          資料品質驗證(重複/時間/名次倒置/覆蓋率/年份漂移)
  build_viz.py         ★ master.public → 前端資料檔(viz/races/race;含 pytest)
  build_athletes.py    ★ master → 選手追蹤資料(athletes 索引 + athlete/<id>;姓名為主歸併、同名信心標記;含 pytest)
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

Astro + React islands + Tailwind v4 + ECharts,Claude 暖色風,5 頁:`/`(總覽)、`/explore`(探索)、`/race`(賽事詳情)、`/athletes`(選手追蹤)、`/climbs`(傳奇爬坡)。

```powershell
python scrapers\build_viz.py            # master.public → web/public/data/{viz,races,race/*}.json
python scrapers\build_athletes.py       # master → web/public/data/{athletes.json, athlete/<id>.json}
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

`source_platform` `source_url` `source_format` ｜ `race_name_raw` `race_name_canonical` `race_key`(去重鍵)`year` `date` `race_type` `region` ｜ `result_label` `category_raw`(原始組別)`gender`(M/F/None)`age_group`(`24-35`/`U15`/`MASTER`…)｜ `rank_overall` `bib` ｜ `name_raw`(內部)`name_masked`(`李○○`,PDPA)`nationality` `team` ｜ `finish_time` `finish_seconds` `splits` ｜ `scraped_at`

## 重點與限制

- **cyclist.org.tw**:列表 → 賽事頁 → PDF → pdfplumber **逐行文字** 解析;**欄位順序逐 PDF 不同**,解析器讀中文表頭自動判斷(`detect_order`);組別碼直接給性別+分齡;跨分類以 `(race_key,year,bib,finish)` 去重。
- **Bravelog**:`/search` JSON API 探索 contest → server-rendered rank 頁分頁解析(無需 JS)。
- **gender=None ≈ 16%** 多為正常(U13–U15/挑戰組/電輔車 資料源未編碼性別);Bravelog 多市民賽不分組。
- **PDPA**:公開輸出僅用 `*.public.json`(無 `name_raw`)、顯示遮罩姓名;網站頁尾標註來源與下架說明。
- **分齡組正規化**:原始 `age_group` 跨源混用兩套制度(5 歲制 20/25/30… 與範圍式 24-35/40-49),`normalize.age_band()` 統一為十年制粗分級(`U19/19-29/30-39/40-49/50-59/60+/MASTER`)供探索頁篩選與箱形圖;原始 `age_group` 保留於各場成績。
- **race_key / 組別類型** 為保守正規化;賽名對照表仍待精修(三個「武嶺」不可合併、KOM 挑戰≠登山王之路)。

## 選手追蹤的身分識別(Phase 3)

- **以 `name_raw` 為主鍵**串接整段生涯(車隊逐年變動,硬用車隊當複合鍵會把換隊選手拆散)。
- **UCI ID 為強錨點**:姓名唯一對應到一個 UCI ID 時,合併其 UCI 與非 UCI 成績,並標 high 信心。
- **同名信心標記**:跨多支車隊、或同一身分出現 M+F 性別不一致 → 標 `low`(高同名風險),UI 加註提醒。
- **PDPA**:輸出僅含遮罩姓名(`林○宇`,保留首尾)、加鹽不可逆 `athlete_id`、`has_uci` 布林;不公開 `name_raw` 與原始 UCI ID。索引僅 ≥2 場的可追蹤選手;每位歷程檔點擊才載入。

## 下一步

- 儀表板增強:賽名/組別正規化對照表(統一 M20/20-24/M24-35)、ECharts tree-shake、手機篩選抽屜、a11y 打磨、自訂網域。
- cycling.org.tw 舊年份寬表格式回填(目前僅 2025 國家級源)。
