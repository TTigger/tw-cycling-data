# 羅馬拼音名遮罩修正(Romanized Name Masking)— 設計 spec

**日期**:2026-06-30
**狀態**:已核可,待寫實作計畫
**範圍**:修 `common.mask_name` 的拉丁分支——目前 `"Alex Dupont" → "Alex D."` **露出名字**;改為 `A○ Dupont`(名/中名→首字母+○,保留姓氏),並把雜質名清成空。改完全量重建(merge→master.public→web/v1→dataset)並發新版資料集。這是「開放資料集」隱私抽查發現的上游缺口(先前作 B 列為後續)。

## 背景與動機

`common.mask_name` 對中文名做「留姓藏名」(李○明),但**拉丁分支只做 `Alex D.`**——保留完整名字 `Alex`,僅把姓縮成首字母。發布開放資料集前抽查發現約 2.5%(~3,704 筆)`name_masked` 未正確遮罩(多為外籍/羅馬拼音名露出名字 + 少量 HTML/編號雜質)。**同一份 `name_masked` 也顯示在網站選手頁**,故此為上游修正,網站與資料集一併受惠。

遮罩政策集中在 `merge.py:92`(`if name_raw: name_masked = mask_name(name_raw)`,無條件由 `name_raw` 重算),故改 `mask_name` + 重跑 merge 即全面重算,**不需重爬**(18 個 per-source 檔皆在且含 `name_raw`)。

## 已核可的決策

1. **拉丁遮罩規則**:`A○ Dupont`(保守對稱——名/中名→首字母+○,保留姓氏;單 token `Alex→A○`)。
2. **雜質名清空**(`<span c.`、`1.` 等→空字串)。
3. **中文分支不變**。
4. **不重爬**;全量重建由 controller 在程式改完後執行。
5. **新版資料集 release 為對外動作**,重建驗證後由 owner 確認再發。

## 新 `mask_name` 拉丁分支規則(精確)

由 `name_raw`(完整原名)計算。中文分支(含 `[一-鿿]`)維持現狀。其餘(拉丁/其他):

1. **雜質 → 空字串**:名字含 `<` 或 `>`(HTML 殘渣)→ `""`;或斷詞後無任何含字母的 token(純數字/標點,如 `1.`)→ `""`。
2. **token 化**:`parts = [p for p in name.split() if 任一字元 isalpha()]`(濾掉純標點 token)。
3. **單 token**:`parts[0][0] + "○"`(`Alex → A○`)。
4. **多 token**:最後一個 token(姓氏)保留;其餘每個 → 首字母 + `○`;空格相連。
   - `Alex Dupont → A○ Dupont`
   - `Alex Marie Dupont → A○ M○ Dupont`
   - `ABBY ROBERTS → A○ ROBERTS`

**性質**:輸出**含 `○`**(資料集「無○清空」防護會保留);藏名字、保留姓氏(同名辨識可用);雜質不外顯。

## 元件設計

### `scrapers/common.py:mask_name`(純函式,可測)
- 只改拉丁分支(上述規則)+ 雜質判斷;中文分支與 `if not name` 早退不變。
- 更新 docstring 反映新拉丁規則。

### 重建管線(機械式;程式改完後由 controller 在功能分支上執行)
1. `python scrapers/merge.py` → 重算 `master.json`(內部,含 name_raw)+ `master.public.json` + `master_summary.json`。
2. `python scrapers/build_viz.py && build_athletes.py && build_teams.py && build_series.py && build_insights.py && build_race_dna.py && build_difficulty.py && build_benchmarks.py && build_manifest.py` → 重生 `web/public/data/v1/`(含 athlete/race/team 分片、benchmarks、manifest)。
3. `python scrapers/build_dataset.py` → 重生 `data/dist/` 資料集資產。
4. `python scrapers/validate.py` → 通過。
5. **抽查**:`master.public.json` 中所有 `name_masked` 皆「藏名字」(拉丁名皆含 `○` 或為空;無 `Alex D.` 式完整名字;無 `<`/`>`/純數字殘渣)。
6. `cd web && npm run build` → astro 重建選手頁等(讀新 name_masked)。
7. commit 重生資料(`web/public/data/v1/` + 其他產物;`data/dist` 為 gitignored 不進 commit)。

### 發布(owner 手動,重建後)
- `gh release create dataset-v<新日期> data/dist/* …`(取代舊版的更安全資料)。release notes 註明:羅馬拼音名遮罩已修正。

## 測試(照 dev-workflow)

- `scrapers/test_common.py`(新增或追加)測 `mask_name`:
  - 中文不變:`李大明→李○明`、`王明→王○`、`歐陽菲菲→歐○○菲`。
  - 拉丁:`Alex Dupont→A○ Dupont`、`Alex Marie Dupont→A○ M○ Dupont`、`Alex→A○`、`ABBY ROBERTS→A○ ROBERTS`。
  - 雜質:`<span c.→""`、`1.→""`、`Gilles <.→""`。
  - 邊界:空/None 早退不變。
- 重建後:`pytest scrapers/` 全綠;`validate.py` 通過;抽查 master.public 無未遮罩拉丁名。
- 流程:程式改 + 測試走 SDD → 合併前 controller 跑全量重建 + 抽查 + commit 重生資料 → 終審 → 合併 → owner 發新 release。

## 風險與緩解

- **誤遮罩中文**:中文分支不動;測試涵蓋中文不變。
- **重建出錯/資料漂移**:每步驟後檢查(merge 筆數、validate、抽查遮罩 100%);重建在功能分支,合併前驗證。
- **選手追蹤鍵變動**:約 2,156 筆 name_masked 改變 → 該批選手分組微調(可接受;多為外籍一次性參賽)。
- **巨大 diff**:web/public/data/v1 重生(3 萬+ 檔)+ 部分內容變動;commit 訊息標明「羅馬拼音遮罩重建」。
- **舊 release 仍在**:發新版即可;舊版 `dataset-v2026.06.30` 可保留或於 notes 標示已被取代(owner 決定)。

## YAGNI(不做)

- 不重爬;不改中文規則;不移除資料集「無○清空」防護(保留作 defense-in-depth);不自動發 release。

## 未來待辦(本次不做)

- 若 name_raw 本身偶有殘缺(極少),可加上游清洗;目前以 mask_name 雜質→空涵蓋。
