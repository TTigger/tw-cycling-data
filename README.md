# 台灣公路車賽事資料專案 (tw-cycling-data)

> 🌐 English: **[README.en.md](README.en.md)**

收集、清洗、正規化台灣公路車賽事成績(2024–2026,可擴充至 2010+),做成資料庫 → 互動視覺化儀表板,最終以 Vercel 靜態網頁呈現。

## 進度

| 階段 | 狀態 |
|---|---|
| 資料源偵查(16-agent 工作流) | ✅ `recon-report.md` / `recon-raw.json` |
| 爬蟲可行性 PoC(cyclist + Bravelog) | ✅ `poc-findings.md` |
| **Phase 1a:cyclist.org.tw 管線(2024–26)** | ✅ **3,913 筆 / 12 場**(競技型,性別 83%+分齡 95%) |
| **Phase 1b:Bravelog 管線(2024–26)** | ✅ **29,138 筆 / 45 場**(市民/挑戰型,廣覆蓋) |
| 正規化 + 合併 + 驗證工具層 | ✅ `normalize.py` / `merge.py` / `validate.py` |
| **★ 合併 master 資料集(2024–26)** | ✅ **33,051 筆 / 47 場 / 20 系列**,已去識別化 |
| Phase 1d de-risk:cycling.org.tw | ✅ `cycorg-poc-findings.md`(含 UCI ID 發現) |
| **Phase 2:互動視覺化儀表板(4 頁)** | ✅ `web/`(總覽/探索/賽事/傳奇爬坡;Astro+React+ECharts,Claude 風,RWD) |
| 部署 Vercel | ⏳ 前置完成,待連結 GitHub→Vercel |
| Phase 1c:歷史回填 2014–2023(cyclist 已支援 `--years`) | 待辦 |
| Phase 1d:cycling.org.tw 國家級源(1998–2026) | 待辦 |
| Phase 3:選手歷年追蹤(UCI ID) | 待辦 |

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
  summarize.py         產生單一資料集統計摘要
  *_poc.py / *_inspect.py / *_probe.py / bravelog_parse.py   PoC/探勘一次性腳本(保留參考)
data/processed/
  master_2024_2026.public.json     ★ 去識別化合併資料(供前端)
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
python scrapers\validate.py master_2024_2026.json      # 資料品質檢查
```

## 前端儀表板(`web/`)

Astro + React islands + Tailwind v4 + ECharts,Claude 暖色風,4 頁:`/`(總覽)、`/explore`(探索)、`/race`(賽事詳情)、`/climbs`(傳奇爬坡)。

```powershell
python scrapers\build_viz.py            # master.public → web/public/data/{viz,races,race/*}.json
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
- **race_key / 組別** 為保守正規化;正式對照表仍待精修(三個「武嶺」不可合併、KOM 挑戰≠登山王之路)。

## 下一步

- 連結 GitHub → Vercel 完成上線(見「部署」)。
- 歷史回填 2014–2023(`cyclist_crawl.py --years 2014-2023`)。
- cycling.org.tw 國家級源(環台賽/全國錦標賽,含 **UCI ID**)。
- Phase 3 選手歷年追蹤(以 UCI ID 串接,做選手頁)。
