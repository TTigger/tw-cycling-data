# PoC 爬蟲可行性實證結果

> 日期:2026-06-04 ｜ 兩個來源端到端實測通過,均有真實結構化樣本資料產出。
> 程式:`scrapers/` ｜ 樣本輸出:`data/processed/`

## ✅ 來源 A:cyclist.org.tw(自行車騎士協會)— 最易,品質最佳

**完整鏈路驗證通過**:列表頁 → 賽事頁 → PDF 下載 → pdfplumber 文字解析 → 結構化列。

- **列表**:`results_list.asp?pno=N`(N=1 KOM登山王 / 2 俱樂部聯賽 / 13 臺灣自行車聯賽…),靜態 HTML,直含 PDF 連結。
- **賽事頁**:`results_txt.asp?pno=NNN`,`<title>` 給賽名+年份,PDF **錨點文字直接是組別標籤**(總排名/分組排名/公路賽競賽/國中/挑戰),URL 日期碼(`/20260509/`)給賽事日期。
- **PDF 解析關鍵**:`extract_text()` 逐行 regex 解析(**不要用表格偵測**,版面複雜會失敗)。資料列高度規律:
  ```
  總排名 編號 姓名 國籍 組別 車隊 ...分段時間... 總時間
  1 251 李廷威 TWN M25 EPIC TRCA Team 01:45:53.03 00:14:38.35 02:00:31.38
  ```
- **重大收穫**:**組別欄 `M25/W40` 直接同時給性別(M/W)+ 分齡組** → 解決 recon 擔心的「缺性別/年齡」。
- **實測**:2026 太平山王累計總排名 PDF → **解析出 80 筆**完整成績(`data/processed/sample_cyclist_taipingshan2026_gc.json`)。性別分布 M:53 / F:10 / U(青少年):17。
- **待微調**:U13/U14/U15 青少年組無性別碼(顯示 None)、Chinese 組別名(菁英組/挑戰組)需另建對照,跨年版面需逐年校正。

## ✅ 來源 B:Bravelog 運動趣 — 確認「無需 JS」,靜態可抓

**解開 recon 的判讀衝突**:用 Chrome DevTools 實測,導航後**無任何 rank 資料的 XHR**(只有 GA analytics)→ 成績是 **server-side render 在初始 HTML 文件**裡,純 `requests` 即可抓。

- **rank 頁**:`/contest/rank/{contestId}`(contestId = 日期碼如 `2025101802`),每位選手乾淨結構:
  - `<a href="/athlete/{raceId}/{bib}">` → raceId + 號碼布
  - `.name` 姓名 ｜ `.detail-info` 三個 span(號碼 / 組別如「104公里挑戰組」/ 性別組「男子組/女子組」)｜ `.time` 完賽時間
- **API 線索**:站台有後端 API base `lb.bravelog.tw/api/v2.0/`、`backend.bravelog.tw/api/v2.0/`(無公開文件,目前靠 SSR HTML 即足夠,API 留作後備)。
- **更豐富欄位**:選手明細頁 `/athlete/{raceId}/{bib}` 依 recon 有晶片淨時間/分段/均速/多維排名(Phase 2/3 再抓)。
- **實測**:`contest/rank/2025101802`(L'Étape 日月潭)→ 解析出 19 筆(`data/processed/sample_bravelog_2025101802.json`)。
- **全量待補**:單一 view 只回一個組別/距離的一頁;完整需遍歷 子賽事(raceId)× 組別(下拉)× 分頁(`?page=`)。可行,屬工程量問題。

## 結論

| 來源 | 鏈路 | 技術 | 給性別 | 給年齡 | 難度 |
|---|---|---|---|---|---|
| cyclist.org.tw | 靜態→PDF→regex | requests+pdfplumber | ✅(組別碼) | ✅(分齡組) | 低 |
| Bravelog | 靜態 SSR HTML→CSS/regex | requests | ✅(男/女子組) | △(分齡組,部分賽事) | 低-中 |

**兩者都不需 headless 瀏覽器做主爬取** → 非常適合做成「離線預處理 → 靜態 JSON → Vercel 純前端」的架構。下一步可正式建 Phase 1 資料管線。
