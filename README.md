# 台灣公路車賽事資料專案 (tw-cycling-data)

收集、清洗、正規化台灣公路車賽事成績(2010–2026),分階段做成資料庫 → 互動視覺化 → 選手追蹤,最終以 Vercel 靜態網頁呈現。

## 進度

| 階段 | 狀態 |
|---|---|
| 資料源偵查(16-agent 工作流) | ✅ `recon-report.md` / `recon-raw.json` |
| 爬蟲可行性 PoC(cyclist + Bravelog) | ✅ `poc-findings.md` |
| **Phase 1a:cyclist.org.tw 管線(2024–26)** | ✅ **3,913 筆 / 12 場**(競技型,性別 83%+分齡 95%) |
| **Phase 1b:Bravelog 管線(2024–26)** | ✅ **29,138 筆 / 45 場**(市民/挑戰型,廣覆蓋) |
| 正規化 + 合併 + 驗證工具層 | ✅ `normalize.py` / `merge.py` / `validate.py` |
| **★ 合併 master 資料集(2024–26)** | ✅ **33,051 筆 / 47 場 / 20 系列**,已驗證去識別化 |
| Phase 1d de-risk:cycling.org.tw | ✅ `cycorg-poc-findings.md`(含 UCI ID 發現) |
| Phase 1c:歷史回填 2014–2023(cyclist 已支援 `--years`) | 待辦 |
| Phase 1d:cycling.org.tw 國家級源(1998–2026) | 待辦 |
| Phase 2:互動視覺化儀表板 | 待辦(資料齊全後再議) |
| Phase 3:選手歷年追蹤 | 待辦 |

## 目錄

```
recon-report.md / recon-raw.json   資料源版圖偵查
poc-findings.md                    PoC 可行性實證
scrapers/
  common.py            共用:HTTP、組別/性別/分齡正規化、姓名遮罩(PDPA)、賽名 race_key、統一紀錄
  normalize.py         跨源正規化:race_class(頒獎組別類型)+ series(賽事系列)對照表
  cyclist_crawl.py     ★ 正式爬蟲 cyclist.org.tw(支援 --years 歷史回填、--out)
  bravelog_calendar.py ★ Bravelog contestId 探索(/search API)+ 自行車賽分類
  bravelog_crawl.py    ★ 正式爬蟲 Bravelog(contest→raceId子賽事→分頁,per-contest 快取)
  merge.py             ★ 合併所有來源 → master 資料集(套用 normalize)
  validate.py          資料品質驗證(重複/時間/名次倒置/覆蓋率/年份漂移)
  summarize.py         產生單一資料集統計摘要
  *_poc.py / *_inspect.py / *_probe.py / bravelog_parse.py   PoC/探勘一次性腳本(保留參考)
data/
  pdf/cyclist/                    下載快取的成績 PDF(重跑免重抓)
  raw/bravelog_cycling_contests.json   Bravelog 自行車賽 contest 工作清單
  raw/bravelog_by_contest/        Bravelog 各 contest 解析快取(可續跑)
  processed/
    cyclist_2024_2026.json / .public.json / cyclist_summary.json
    bravelog_2024_2026.json / .public.json
    master_2024_2026.json           ★ 合併後完整資料(內部用)
    master_2024_2026.public.json    ★ 去識別化(供前端/Vercel)
    master_summary.json             綜合摘要(平台/年份/性別/race_class/series)
```

## 執行

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

## 統一資料欄位(每筆 = 一位選手在一場賽事的成績)

`source_platform` `source_url` `source_format` ｜ `race_name_raw` `race_name_canonical` `race_key`(去重/合併鍵)`year` `date` `race_type` `region` ｜ `result_label`(來源 PDF 標籤)`category_raw`(原始組別)`gender`(M/F/None)`age_group`(分齡:`24-35`/`U15`/`MASTER`…)｜ `rank_overall` `bib` ｜ `name_raw`(內部)`name_masked`(`李○○`,PDPA)`nationality` `team` ｜ `finish_time` `finish_seconds` `splits` ｜ `scraped_at`

## cyclist.org.tw 管線重點

- 鏈路:`results_list.asp?pno=N`(分類)→ `results_txt.asp?pno=NNN`(賽事)→ `upfile/.../*.pdf` → pdfplumber **逐行文字** 解析(不可用表格偵測)。
- **欄位順序逐 PDF 不同**(`姓名 國籍 組別 車隊` vs `姓名 組別 車隊 國籍`)→ 解析器**讀中文表頭自動判斷順序**(`detect_order`)。
- **組別碼直接給性別+分齡**:`M24-35`→男/24-35、`W36`→女/36、`MASTER`→男/masters。
- 偏好「總排名(GC)」PDF(含全員+組別欄);跨分類重複以 `(race_key, year, bib, finish)` 全域去重(本輪移除 473 筆)。

## 已知限制 / 待辦

- **gender=None ≈ 635 筆(16%)多為正常**:U13/U14/U15 青少年組、挑戰組、電輔車組——資料源本就未編碼性別;真正解析失敗僅約 89 筆(2%,外籍/TTT 邊緣格式)。
- `date` 部分取自 PDF URL 日期碼,偶有沿用舊值(年份以標題為準,正確)。
- `race_key` 為保守正規化;正式「賽名/組別對照表」仍待建(recon 風險:三個「武嶺」不可合併、KOM 挑戰≠登山王之路)。
- **PDPA**:公開輸出一律用 `*.public.json`(無 `name_raw`)、顯示 `name_masked`。上線前需下架機制與條款檢視。

## 下一步

1. **Bravelog 管線**:先解 contestId 探索(哪些是 2024–26 自行車賽)→ 遍歷 子賽事×組別×分頁 → 正規化進同一 schema。
2. cyclist 歷史回填 2014–2023;1998–2013 改用 cycling.org.tw。
3. 合併兩來源 → 統一資料集 → Phase 2 視覺化。
