# 羅馬拼音名遮罩修正 + 重建 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修 `common.mask_name` 拉丁分支(`Alex Dupont→A○ Dupont`、雜質→空),再全量重建(merge→master.public→web/v1→dataset)讓網站與資料集的羅馬拼音名都正確遮罩。

**Architecture:** 程式改動極小(只改 `mask_name` 拉丁分支,純函式)。遮罩政策集中在 `merge.py:92`(無條件由 `name_raw` 重算),故改 `mask_name` + 重跑 merge 即全面重算,不需重爬。重建(merge→build_*→dataset→astro→validate)為機械式步驟,程式改完、task review 通過後由 controller 在功能分支上執行並 commit 重生資料。

**Tech Stack:** Python(`common.py`、merge/build 管線)、pytest;Astro build。

## Global Constraints

- **拉丁遮罩規則**:`A○ Dupont`——名/中名 → 首字母 + `○`,保留姓氏(最後 token);單 token `Alex→A○`;輸出**含 `○`**。
- **雜質 → 空字串**:名字含 `<`/`>`,或斷詞後無含字母 token(`1.` 等)→ `""`。
- **中文分支不變**;`if not name` 早退不變。
- 由 `name_raw`(完整原名)重算(merge.py 既有邏輯)。
- 重建後 **master.public.json 所有 `name_masked` 皆藏名字**(拉丁名含 `○` 或空;無 `Alex D.` 式完整名;無 `<`/`>`/純數字殘渣)。
- 不重爬;不自動發 release(對外動作,owner 手動)。
- 既有測試:`pytest scrapers/` 綠;`validate.py` 通過。

## 已確認的現況

- `common.mask_name`:中文分支 `李○明`;拉丁分支現為 `parts[0] + " " + parts[1][0] + "."`(= `Alex D.`,露名字)。`if not name: return name` 早退;`name.strip()`。
- `merge.py:92`:`if r.get("name_raw"): r["name_masked"] = common.mask_name(r["name_raw"])`(無條件重算)。
- 18 個 per-source 檔在 `data/processed/`,皆含 `name_raw`。重建鏈:`merge.py` → `build_viz/athletes/teams/series/insights/race_dna/difficulty/benchmarks/manifest` → `build_dataset` → `validate` → astro build。
- `scrapers/test_common.py` 已存在(Feature 1 建立)。

---

## File Structure

**修改(SDD Task 1):** `scrapers/common.py`(`mask_name` 拉丁分支 + docstring)、`scrapers/test_common.py`(追加 mask_name 測試)
**重生(controller 重建步驟,非 subagent task):** `data/processed/master*.json`(內部/gitignored)、`web/public/data/v1/**`(committed 產物)、`data/dist/**`(gitignored)

---

## Task 1: 修 `mask_name` 拉丁分支(+ 測試)

唯一的程式改動。交付物:新拉丁規則 + 測試通過。

**Files:**
- Modify: `scrapers/common.py`(`mask_name` 的拉丁分支)
- Test: `scrapers/test_common.py`(追加)

**Interfaces:**
- Produces:`common.mask_name(name)` 拉丁輸出改為 `A○ Surname` 形式 + 雜質→`""`;中文與早退不變。

- [ ] **Step 1: Write the failing test**

在 `scrapers/test_common.py` 追加(import 既有 `common`;若檔頭尚無 `import common` 則加上):

```python
import common


def test_mask_name_cjk_unchanged():
    assert common.mask_name("李大明") == "李○明"
    assert common.mask_name("王明") == "王○"
    assert common.mask_name("歐陽菲菲") == "歐○○菲"


def test_mask_name_romanized_hides_given_keeps_surname():
    assert common.mask_name("Alex Dupont") == "A○ Dupont"
    assert common.mask_name("Alex Marie Dupont") == "A○ M○ Dupont"
    assert common.mask_name("ABBY ROBERTS") == "A○ ROBERTS"
    assert common.mask_name("Alex") == "A○"


def test_mask_name_junk_becomes_empty():
    assert common.mask_name("<span c.") == ""
    assert common.mask_name("Gilles <.") == ""
    assert common.mask_name("1.") == ""


def test_mask_name_empty_and_none_unchanged():
    assert common.mask_name("") == ""
    assert common.mask_name(None) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_common.py -k mask_name -v`
Expected: FAIL(現拉丁分支回 `Alex D.`、雜質未清空)

- [ ] **Step 3: Replace the latin branch in `scrapers/common.py:mask_name`**

把目前的拉丁尾段(從 `# latin name -> "Alex D."` 到函式結尾)整段換成:

```python
    # latin / other scripts -> hide given name(s), keep the surname (last token).
    # Output contains ○ so it is recognisably masked (and kept by the dataset
    # safeguard). Scraping junk -> empty string so it never surfaces.
    if "<" in name or ">" in name:
        return ""
    parts = [p for p in name.split() if any(c.isalpha() for c in p)]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0][0] + "○"
    given = [p[0] + "○" for p in parts[:-1]]
    return " ".join(given) + " " + parts[-1]
```

並把 docstring 末行 `Latin: keep first token + initial -> 'Alex D.'.` 改為
`Latin: hide given name(s) -> initial + ○, keep surname -> 'A○ Dupont'; junk -> ''.`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_common.py -k mask_name -v`
Expected: PASS(全部 mask_name 測試)

- [ ] **Step 5: Run full scrapers suite + commit**

Run: `python -m pytest scrapers/ -q`
Expected: 全綠(注意:既有測試若有寫死 `Alex D.` 形式的斷言會失敗——若有,該斷言屬本次政策變更,更新為新形式)。

```bash
git add scrapers/common.py scrapers/test_common.py
git commit -m "fix(pdpa): mask romanized given names (A○ Dupont) + drop junk names"
```

---

## 重建步驟(controller 執行,非 subagent task)

> Task 1 的 review 通過後,由 controller 在同一功能分支上執行;產生大量重生產物的 commit。

- [ ] **R1: 重跑 merge**

Run: `python scrapers/merge.py`
Expected: 印出筆數(約 147,609);產生 `master.json`/`master.public.json`/`master_summary.json`。

- [ ] **R2: 抽查遮罩 100%**

```bash
python - <<'PY'
import sys; sys.path.insert(0,"scrapers"); import common
bad=[]
for r in common.iter_records("data/processed/master.public.json"):
    nm=r.get("name_masked")
    if not nm: continue
    # 拉丁名必須含 ○;中文名含 ○ 或為 1 字;不可含 < > ;不可是 'X Y.' 完整名形式
    import re
    if re.search(r"[一-鿿]", nm):  # CJK ok if masked or single char
        continue
    if "○" not in nm or "<" in nm or ">" in nm:
        bad.append(nm)
print("unmasked latin names:", len(bad), "examples:", bad[:10])
PY
```
Expected: `unmasked latin names: 0`。若非 0,停下檢查規則。

- [ ] **R3: 重建 web/v1 + dataset + validate**

Run:
```bash
python scrapers/build_viz.py && python scrapers/build_athletes.py && python scrapers/build_teams.py && python scrapers/build_series.py && python scrapers/build_insights.py && python scrapers/build_race_dna.py && python scrapers/build_difficulty.py && python scrapers/build_benchmarks.py && python scrapers/build_manifest.py && python scrapers/build_dataset.py && python scrapers/validate.py
```
Expected: 各步驟成功;`validate.py` 通過。

- [ ] **R4: astro build**

Run: `npm --prefix web run build`
Expected: 成功(選手頁等讀新 name_masked)。

- [ ] **R5: commit 重生資料**

```bash
git add web/public/data/v1
git commit -m "chore(data): rebuild web/v1 with romanized-name masking applied"
```
（`data/processed/*` 與 `data/dist/*` 為 gitignored,不進 commit。）

---

## 發布(owner 手動,合併後)

- 新版資料集:`python scrapers/build_dataset.py` 已於 R3 產出;`gh release create dataset-v<新日期> data/dist/* --title "Dataset <新日期>" --notes "羅馬拼音名遮罩已修正(A○ Surname);CC BY 4.0。"`。
- 由 owner 確認後執行(對外動作)。

---

## Self-Review

**1. Spec coverage:** 拉丁規則 `A○ Dupont` + 單 token + 多 token → Task 1 Step 3 ✅;雜質→空 → Step 3 ✅;中文不變 → 未動 CJK 分支 + 測試 ✅;由 name_raw 重算 → merge.py 既有 ✅;全量重建 + 100% 抽查 → R1–R4 ✅;不重爬 → 用 per-source 既有檔 ✅;新 release owner 手動 → 發布段 ✅。

**2. Placeholder scan:** 無 TBD;Step 3 給完整替換程式;R2 抽查給完整腳本。`<新日期>` 為 owner 發布時填入的對外佔位(刻意)。

**3. Type consistency:** `mask_name` 簽名不變;新拉丁分支回字串(含 `○` 或 `""`),與既有呼叫端(merge/build_* 的 `name_masked`)相容;測試斷言與 Step 3 規則一致(`Alex Dupont→A○ Dupont` 等)。

---

## 執行順序
Task 1(程式 + 測試,走 SDD)→ review 通過 → controller R1–R5(重建 + commit)→ 終審 → 合併 → owner 發新 release。
