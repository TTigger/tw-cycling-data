# 開放資料集發布 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把去識別化逐筆成績打包成版本化、附 schema 與 CC BY 4.0 授權的可下載開放資料集(CSV.gz + JSON.gz + datapackage),經 GitHub Releases 發布。

**Architecture:** `scrapers/dataset.py`(純函式:白名單欄位投影,刪除外部識別碼)+ `scrapers/build_dataset.py`(串流 master.public → 寫 `data/dist/` 的 release 資產:csv.gz/json.gz/datapackage.json/CHECKSUMS)+ 文件(`DATASET.md`/`DATASET.en.md`/`CITATION.cff`/README)。實際 `gh release` 由 owner 確認後執行。

**Tech Stack:** Python 標準庫(csv/gzip/json/hashlib/datetime)、pytest。

## Global Constraints

- **白名單投影**:輸出欄位 == `PUBLISH_COLUMNS`(20 欄);**`DROP_COLUMNS` 一律不得出現在輸出**(`uci_id, tsu_rider_id, source_url, bib, nationality, name_raw, scraped_at, source_format, race_name_raw`)。安全測試逐欄斷言。
- **格式**:`tw-cycling-results.csv.gz` + `tw-cycling-results.json.gz`。
- **授權**:CC BY 4.0;attribution 連回 repo;opt-out 走 GitHub Issues `https://github.com/TTigger/tw-cycling-data/issues`。
- **指標由產物計算**:datapackage 的 `count`/`bytes`/`hash`(sha256)不可寫死,測試斷言一致。
- **版本**:日期式 `YYYY.MM.DD`(`datetime.now().strftime("%Y.%m.%d")`)。
- **不自動發布**:build 只產檔;`gh release create` 由 owner 執行。
- **大檔不進 git**:`data/dist/` 加入 `.gitignore`。
- 既有測試流程:`python -m pytest scrapers/` 綠;每 task 自己 commit。

## 已確認的現況

- `master.public.json`:119MB、147,609 筆、28 欄:`age_band, age_group, bib, category_raw, date, finish_seconds, finish_time, gender, name_masked, nationality, race_class, race_key, race_name_canonical, race_name_raw, race_type, rank_overall, region, result_label, scraped_at, series, source_format, source_platform, source_url, splits, team, tsu_rider_id, uci_id, year`。
- `common.iter_records(path)` 串流逐筆 dict;`common.PUBLIC_DATA_DIR` = web/public/data/v1(本案不寫這裡)。
- repo 無 LICENSE/DATASET/datapackage/CSV、無 GitHub Release。

---

## File Structure

**新增(後端):** `scrapers/dataset.py`、`scrapers/build_dataset.py`、`scrapers/test_dataset.py`、`scrapers/test_build_dataset.py`
**新增(文件):** `DATASET.md`、`DATASET.en.md`、`CITATION.cff`
**修改:** `.gitignore`(加 `data/dist/`)、`README.md`、`README.en.md`(Open Dataset 區段)、`scrapers/test_dataset.py`(文件涵蓋測試)

---

## Task 1: `dataset.py` — 白名單投影(純函式)

可測的欄位投影,確保只輸出安全欄位。交付物:`dataset.py` + 安全測試。

**Files:**
- Create: `scrapers/dataset.py`
- Test: `scrapers/test_dataset.py`

**Interfaces:**
- Produces:
  - `FIELDS: list[tuple[str,str,str]]`(20 筆 `(name, type, description)`,固定順序)
  - `PUBLISH_COLUMNS: list[str]` = `[f[0] for f in FIELDS]`
  - `DROP_COLUMNS: list[str]` = 明列被刪欄
  - `project_row(row: dict) -> dict`:回只含 PUBLISH_COLUMNS(順序固定,缺欄補 None)
  - `csv_value(v) -> str`:list→JSON 字串、None→""、其餘→str

- [ ] **Step 1: Write the failing test**

`scrapers/test_dataset.py`:

```python
import dataset as D


def test_publish_columns_match_fields_and_count_20():
    assert D.PUBLISH_COLUMNS == [f[0] for f in D.FIELDS]
    assert len(D.PUBLISH_COLUMNS) == 20


def test_project_row_keeps_only_publish_columns():
    raw = {c: f"v_{c}" for c in D.PUBLISH_COLUMNS}
    # add every dropped/sensitive column with a sentinel value
    for c in D.DROP_COLUMNS:
        raw[c] = "SENSITIVE"
    raw["name_raw"] = "王大明"   # must never appear
    out = D.project_row(raw)
    assert list(out.keys()) == D.PUBLISH_COLUMNS          # exact set + order
    for c in D.DROP_COLUMNS + ["name_raw"]:
        assert c not in out                               # safety gate
    assert "SENSITIVE" not in out.values()


def test_drop_columns_cover_the_reidentifiers():
    for c in ("uci_id", "tsu_rider_id", "source_url", "bib", "nationality",
              "name_raw", "scraped_at", "source_format", "race_name_raw"):
        assert c in D.DROP_COLUMNS


def test_project_row_fills_missing_with_none():
    out = D.project_row({"year": 2024})
    assert out["year"] == 2024 and out["name_masked"] is None


def test_csv_value_handles_list_and_none():
    assert D.csv_value(None) == ""
    assert D.csv_value(123) == "123"
    assert D.csv_value([{"k": 10}]) == '[{"k": 10}]'      # JSON, ensure_ascii off
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_dataset.py -v`
Expected: FAIL(`ModuleNotFoundError: No module named 'dataset'`)

- [ ] **Step 3: Implement `dataset.py`**

```python
# -*- coding: utf-8 -*-
"""Project a master.public.json row to the public open-dataset shape.
WHITELIST projection (PUBLISH_COLUMNS): anything not listed is dropped, so new
upstream columns never leak. External re-identifiers are explicitly dropped."""
import json

# (name, frictionless type, description) — single source for schema + docs.
FIELDS = [
    ("race_key", "string", "賽事鍵;同一賽事跨年共用。"),
    ("year", "integer", "年份。"),
    ("date", "string", "賽事日期 YYYY-MM-DD(約 69% 有)。"),
    ("region", "string", "縣市層級地區(約 38% 有)。"),
    ("series", "string", "賽事系列。"),
    ("race_name_canonical", "string", "正規化賽事名稱。"),
    ("race_type", "string", "賽別:road / criterium / KOM / TT 等。"),
    ("race_class", "string", "賽事分類。"),
    ("result_label", "string", "成績組別標籤(距離/組別)。"),
    ("category_raw", "string", "原始分組字串。"),
    ("gender", "string", "性別 M/F(約 52% 有)。"),
    ("age_band", "string", "分齡帶 U19/19-29/30-39/40-49/50-59/60+(約 36% 有)。"),
    ("age_group", "string", "細分齡。"),
    ("rank_overall", "integer", "總名次(認證賽多為空)。"),
    ("finish_seconds", "number", "完賽秒數。"),
    ("finish_time", "string", "完賽時間字串。"),
    ("splits", "string", "分段時間(JSON;約 9% 有)。"),
    ("team", "string", "車隊(約 46% 有)。"),
    ("name_masked", "string", "遮罩姓名(如 李○明)。"),
    ("source_platform", "string", "來源平台。"),
]

PUBLISH_COLUMNS = [f[0] for f in FIELDS]

# Explicitly dropped: external re-identifiers + internal/redundant columns.
DROP_COLUMNS = ["uci_id", "tsu_rider_id", "source_url", "bib", "nationality",
                "name_raw", "scraped_at", "source_format", "race_name_raw"]


def project_row(row):
    """Whitelist projection: only PUBLISH_COLUMNS, fixed order, missing -> None."""
    return {c: row.get(c) for c in PUBLISH_COLUMNS}


def csv_value(v):
    """CSV-safe stringification. list/dict -> compact JSON (ensure_ascii off);
    None -> empty string; everything else -> str."""
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_dataset.py -v`
Expected: PASS(5 tests)

- [ ] **Step 5: Commit**

```bash
git add scrapers/dataset.py scrapers/test_dataset.py
git commit -m "feat(dataset): whitelist row projection dropping external re-identifiers"
```

---

## Task 2: `build_dataset.py` — 產出 release 資產

串流 master.public → 寫 csv.gz/json.gz/datapackage.json/CHECKSUMS。交付物:可重現產出 + smoke 測試 + 實檔。

**Files:**
- Create: `scrapers/build_dataset.py`
- Test: `scrapers/test_build_dataset.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `dataset.PUBLISH_COLUMNS`/`FIELDS`/`project_row`/`csv_value`、`common.iter_records`。
- Produces:
  - `build(records, out_dir, version) -> dict`(回 `{"count":int, "files":{name:{"bytes":int,"sha256":str}}}`,並寫出 4 個檔)。
  - `main()`:讀 master.public、`build(...)`、印摘要。

- [ ] **Step 1: Write the failing test**

`scrapers/test_build_dataset.py`:

```python
import csv
import gzip
import io
import json
import os
import build_dataset as B
import dataset as D


def _rows():
    base = {c: None for c in D.PUBLISH_COLUMNS}
    r1 = dict(base, year=2024, name_masked="李○明", finish_seconds=3600, splits=[{"k": 1}])
    r2 = dict(base, year=2025, name_masked="陳○明", finish_seconds=4000)
    # include sensitive keys to prove they are dropped
    r1["uci_id"] = "10012345678"; r1["name_raw"] = "李大明"; r1["source_url"] = "http://x"
    return [r1, r2]


def test_build_writes_assets_and_drops_sensitive(tmp_path):
    out = str(tmp_path)
    summary = B.build(_rows(), out, "2026.06.30")

    assert summary["count"] == 2
    # csv.gz header == PUBLISH_COLUMNS, no sensitive columns
    with gzip.open(os.path.join(out, "tw-cycling-results.csv.gz"), "rt", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == D.PUBLISH_COLUMNS
    for c in D.DROP_COLUMNS:
        assert c not in header

    # datapackage: count + per-file sha256/bytes present, license CC-BY-4.0
    dp = json.load(open(os.path.join(out, "datapackage.json"), encoding="utf-8"))
    assert dp["count"] == 2
    assert dp["licenses"][0]["name"] == "CC-BY-4.0"
    assert dp["version"] == "2026.06.30"
    names = {r["path"] for r in dp["resources"]}
    assert "tw-cycling-results.csv.gz" in names and "tw-cycling-results.json.gz" in names
    for r in dp["resources"]:
        assert len(r["hash"]) == 64 and r["bytes"] > 0      # sha256 hex
    # schema fields cover every published column
    fields = {fld["name"] for fld in dp["resources"][0]["schema"]["fields"]}
    assert fields == set(D.PUBLISH_COLUMNS)

    # CHECKSUMS.txt lists both gz files
    chk = open(os.path.join(out, "CHECKSUMS.txt"), encoding="utf-8").read()
    assert "tw-cycling-results.csv.gz" in chk and "tw-cycling-results.json.gz" in chk

    # json.gz round-trips and contains no sensitive keys
    with gzip.open(os.path.join(out, "tw-cycling-results.json.gz"), "rt", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2 and "uci_id" not in data[0] and "name_raw" not in data[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest scrapers/test_build_dataset.py -v`
Expected: FAIL(`ModuleNotFoundError: No module named 'build_dataset'`)

- [ ] **Step 3: Implement `build_dataset.py`**

```python
# -*- coding: utf-8 -*-
"""Build the public open dataset release assets from master.public.json:
tw-cycling-results.csv.gz, .json.gz, datapackage.json, CHECKSUMS.txt -> data/dist/.
Whitelist projection via dataset.project_row. Does NOT publish a release."""
import csv
import gzip
import hashlib
import io
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
import common   # noqa: E402
import dataset  # noqa: E402

IN = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "master.public.json")
DIST = os.path.join(os.path.dirname(__file__), "..", "data", "dist")
CSV_NAME = "tw-cycling-results.csv.gz"
JSON_NAME = "tw-cycling-results.json.gz"
REPO = "https://github.com/TTigger/tw-cycling-data"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(records, out_dir, version):
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, CSV_NAME)
    json_path = os.path.join(out_dir, JSON_NAME)

    count = 0
    with gzip.open(csv_path, "wt", encoding="utf-8", newline="") as cf, \
            gzip.open(json_path, "wt", encoding="utf-8") as jf:
        w = csv.writer(cf)
        w.writerow(dataset.PUBLISH_COLUMNS)
        jf.write("[")
        for row in records:
            p = dataset.project_row(row)
            w.writerow([dataset.csv_value(p[c]) for c in dataset.PUBLISH_COLUMNS])
            jf.write(("," if count else "") + json.dumps(p, ensure_ascii=False))
            count += 1
        jf.write("]")

    files = {}
    for name in (CSV_NAME, JSON_NAME):
        path = os.path.join(out_dir, name)
        files[name] = {"bytes": os.path.getsize(path), "sha256": _sha256(path)}

    datapackage = {
        "name": "tw-cycling-results",
        "title": "Taiwan road-cycling race results (de-identified)",
        "version": version,
        "homepage": REPO,
        "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/"}],
        "attribution": f"tw-cycling-data ({REPO})",
        "contact": f"{REPO}/issues",
        "count": count,
        "resources": [
            {"path": CSV_NAME, "format": "csv", "compression": "gz",
             "bytes": files[CSV_NAME]["bytes"], "hash": files[CSV_NAME]["sha256"],
             "schema": {"fields": [{"name": n, "type": t, "description": d}
                                   for n, t, d in dataset.FIELDS]}},
            {"path": JSON_NAME, "format": "json", "compression": "gz",
             "bytes": files[JSON_NAME]["bytes"], "hash": files[JSON_NAME]["sha256"]},
        ],
    }
    with open(os.path.join(out_dir, "datapackage.json"), "w", encoding="utf-8") as f:
        json.dump(datapackage, f, ensure_ascii=False, indent=1)

    with open(os.path.join(out_dir, "CHECKSUMS.txt"), "w", encoding="utf-8") as f:
        for name in (CSV_NAME, JSON_NAME):
            f.write(f"{files[name]['sha256']}  {name}\n")

    return {"count": count, "files": files}


def main():
    version = datetime.now().strftime("%Y.%m.%d")
    summary = build(common.iter_records(IN), DIST, version)
    print(f"dataset v{version}: rows={summary['count']} -> {os.path.relpath(DIST)}")
    for name, info in summary["files"].items():
        print(f"  {name}: {info['bytes'] // 1024} KB  sha256={info['sha256'][:12]}…")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest scrapers/test_build_dataset.py -v`
Expected: PASS

- [ ] **Step 5: Ignore the dist dir**

在 `.gitignore` 末新增一行(若無 `data/dist` 規則):

```
data/dist/
```

- [ ] **Step 6: Real build + sanity-check**

Run:
```bash
python scrapers/build_dataset.py
zcat data/dist/tw-cycling-results.csv.gz | head -1
python -c "import json;d=json.load(open('data/dist/datapackage.json',encoding='utf-8'));print('count',d['count'],'ver',d['version']);print('cols',[f['name'] for f in d['resources'][0]['schema']['fields']])"
ls -la data/dist/
```
Expected: header 為 20 個 PUBLISH_COLUMNS、**無 uci_id/tsu_rider_id/source_url/bib/nationality**;`count` 約 147,609;csv.gz/json.gz/datapackage.json/CHECKSUMS.txt 都在;檔案大小合理(csv.gz 數 MB~十幾 MB)。

- [ ] **Step 7: Run full scrapers suite + commit**

Run: `python -m pytest scrapers/ -q`
Expected: 全綠。

```bash
git add scrapers/build_dataset.py scrapers/test_build_dataset.py .gitignore
git commit -m "feat(dataset): build_dataset.py emits csv.gz/json.gz/datapackage/CHECKSUMS to data/dist"
```

---

## Task 3: 文件 — `DATASET.md` / `DATASET.en.md` / `CITATION.cff` / README

人讀說明 + 引用 metadata。交付物:文件齊備,涵蓋每個欄位,測試斷言一致。

**Files:**
- Create: `DATASET.md`、`DATASET.en.md`、`CITATION.cff`
- Modify: `README.md`、`README.en.md`、`scrapers/test_dataset.py`(文件涵蓋測試)

**Interfaces:**
- Consumes: `dataset.PUBLISH_COLUMNS`/`DROP_COLUMNS`。

- [ ] **Step 1: Add a doc-coverage test to `scrapers/test_dataset.py`**

在 `scrapers/test_dataset.py` 末追加:

```python
import os

_ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_dataset_docs_list_every_column_and_license():
    for fn in ("DATASET.md", "DATASET.en.md"):
        text = open(os.path.join(_ROOT, fn), encoding="utf-8").read()
        for c in D.PUBLISH_COLUMNS:
            assert c in text, f"{fn} missing column {c}"
        assert "CC BY 4.0" in text or "CC-BY-4.0" in text
        assert "issues" in text                       # opt-out link present


def test_citation_cff_has_license_and_type_dataset():
    cff = open(os.path.join(_ROOT, "CITATION.cff"), encoding="utf-8").read()
    assert "cff-version" in cff and "CC-BY-4.0" in cff and "dataset" in cff
```

Run: `python -m pytest scrapers/test_dataset.py -v`
Expected: FAIL(文件尚未建立)

- [ ] **Step 2: Write `DATASET.md`(中文)**

```markdown
# tw-cycling-data 開放資料集

台灣公路自行車賽事成績的**去識別化**逐筆資料集:8 個來源正規化彙整,147,609 筆、2009–2026。供研究與分析使用。

- **授權**:[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。使用請標註來源 `tw-cycling-data`(https://github.com/TTigger/tw-cycling-data)。
- **下載**:見本專案 [GitHub Releases](https://github.com/TTigger/tw-cycling-data/releases)(`tw-cycling-results.csv.gz` / `.json.gz` + `datapackage.json`)。
- **English**: see [DATASET.en.md](DATASET.en.md).

## 隱私

本資料集為**已公開賽事成績**之去識別化彙整:僅含遮罩姓名 `name_masked`(如 李○明),**已刪除**外部識別碼(`uci_id`、`tsu_rider_id`、`source_url`)與 `bib`、`nationality`。若你是當事人並希望移除你的資料,請至 [GitHub Issues](https://github.com/TTigger/tw-cycling-data/issues) 申請。

## 欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `race_key` | string | 賽事鍵;同一賽事跨年共用 |
| `year` | integer | 年份 |
| `date` | string | 賽事日期 YYYY-MM-DD(約 69% 有) |
| `region` | string | 縣市層級地區(約 38% 有) |
| `series` | string | 賽事系列 |
| `race_name_canonical` | string | 正規化賽事名稱 |
| `race_type` | string | 賽別:road / criterium / KOM / TT 等 |
| `race_class` | string | 賽事分類 |
| `result_label` | string | 成績組別標籤 |
| `category_raw` | string | 原始分組字串 |
| `gender` | string | 性別 M/F(約 52% 有) |
| `age_band` | string | 分齡帶 U19/19-29/30-39/40-49/50-59/60+(約 36% 有) |
| `age_group` | string | 細分齡 |
| `rank_overall` | integer | 總名次(認證賽多為空) |
| `finish_seconds` | number | 完賽秒數 |
| `finish_time` | string | 完賽時間字串 |
| `splits` | string | 分段時間(JSON;約 9% 有) |
| `team` | string | 車隊(約 46% 有) |
| `name_masked` | string | 遮罩姓名(如 李○明) |
| `source_platform` | string | 來源平台 |

## 載入

```python
import pandas as pd
df = pd.read_csv("tw-cycling-results.csv.gz")   # gzip 自動處理
```

## 引用

見 [CITATION.cff](CITATION.cff)(GitHub 右側「Cite this repository」)。

## 發布(維護者)

```bash
python scrapers/build_dataset.py
gh release create dataset-vYYYY.MM.DD data/dist/* \
  --title "Dataset YYYY.MM.DD" --notes "去識別化逐筆成績,CC BY 4.0。"
```
```

- [ ] **Step 3: Write `DATASET.en.md`(英文全文)**

```markdown
# tw-cycling-data Open Dataset

A **de-identified**, row-level dataset of Taiwan road-cycling race results: 8 sources normalized into one file — 147,609 rows, 2009–2026. For research and analysis.

- **License**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please attribute `tw-cycling-data` (https://github.com/TTigger/tw-cycling-data).
- **Download**: see [GitHub Releases](https://github.com/TTigger/tw-cycling-data/releases) (`tw-cycling-results.csv.gz` / `.json.gz` + `datapackage.json`).
- **中文**:見 [DATASET.md](DATASET.md)。

## Privacy

This is a de-identified aggregation of **already-public race results**: only a masked name `name_masked` (e.g. 李○明) is included; external identifiers (`uci_id`, `tsu_rider_id`, `source_url`) and `bib`, `nationality` are **removed**. If you are a data subject and want your records removed, please open a [GitHub Issue](https://github.com/TTigger/tw-cycling-data/issues).

## Columns

| Column | Type | Description |
|---|---|---|
| `race_key` | string | Race key; shared across years of the same event |
| `year` | integer | Year |
| `date` | string | Race date YYYY-MM-DD (~69% present) |
| `region` | string | County-level region (~38% present) |
| `series` | string | Race series |
| `race_name_canonical` | string | Canonical race name |
| `race_type` | string | road / criterium / KOM / TT, etc. |
| `race_class` | string | Race classification |
| `result_label` | string | Result group label |
| `category_raw` | string | Raw category string |
| `gender` | string | M/F (~52% present) |
| `age_band` | string | Age band U19/19-29/30-39/40-49/50-59/60+ (~36% present) |
| `age_group` | string | Fine-grained age |
| `rank_overall` | integer | Overall rank (often empty for certification rides) |
| `finish_seconds` | number | Finish time in seconds |
| `finish_time` | string | Finish time string |
| `splits` | string | Split times (JSON; ~9% present) |
| `team` | string | Team (~46% present) |
| `name_masked` | string | Masked name (e.g. 李○明) |
| `source_platform` | string | Source platform |

## Load

```python
import pandas as pd
df = pd.read_csv("tw-cycling-results.csv.gz")
```

## Cite

See [CITATION.cff](CITATION.cff) (GitHub "Cite this repository").
```

- [ ] **Step 4: Write `CITATION.cff`**

```yaml
cff-version: 1.2.0
title: "tw-cycling-data: Taiwan road-cycling race results (de-identified)"
message: "If you use this dataset, please cite it."
type: dataset
authors:
  - name: "tw-cycling-data contributors"
url: "https://github.com/TTigger/tw-cycling-data"
repository-code: "https://github.com/TTigger/tw-cycling-data"
license: CC-BY-4.0
version: "2026.06.30"
date-released: "2026-06-30"
```

- [ ] **Step 5: Add Open Dataset section to both READMEs**

`README.md` 增一段(置於 Public API 區段附近):

```markdown
## Open Dataset

去識別化逐筆成績(147,609 筆,2009–2026,CC BY 4.0)可下載:見 [Releases](https://github.com/TTigger/tw-cycling-data/releases) 與 [DATASET.md](DATASET.md)。已刪除外部識別碼;當事人可於 [Issues](https://github.com/TTigger/tw-cycling-data/issues) 申請移除。
```

`README.en.md` 對應英文段:

```markdown
## Open Dataset

De-identified row-level results (147,609 rows, 2009–2026, CC BY 4.0) are downloadable: see [Releases](https://github.com/TTigger/tw-cycling-data/releases) and [DATASET.en.md](DATASET.en.md). External identifiers are removed; data subjects can request removal via [Issues](https://github.com/TTigger/tw-cycling-data/issues).
```

- [ ] **Step 6: Run the doc tests + full suite**

Run: `python -m pytest scrapers/test_dataset.py -q && python -m pytest scrapers/ -q`
Expected: PASS / 全綠。

- [ ] **Step 7: Commit**

```bash
git add DATASET.md DATASET.en.md CITATION.cff README.md README.en.md scrapers/test_dataset.py
git commit -m "docs(dataset): DATASET.md/.en + CITATION.cff + README Open Dataset section"
```

---

## Self-Review

**1. Spec coverage:** 保守版欄位 + 白名單 + 安全測試 → Task 1 ✅;csv.gz/json.gz/datapackage/CHECKSUMS + 指標由產物計算 → Task 2 ✅;`data/dist` gitignored → Task 2 Step 5 ✅;CC BY 4.0 + opt-out + 載入範例 + 發布指令 → Task 3(DATASET.md)✅;英文全文 → DATASET.en.md ✅;CITATION.cff → Task 3 ✅;README 雙語 → Task 3 ✅;不自動發布 → 無 release task,DATASET 記指令 ✅;版本日期式 → Task 2 ✅。

**2. Placeholder scan:** 無 TBD;每步附完整程式/文件內容。發布指令的 `YYYY.MM.DD` 是使用者執行時填入的真實佔位(對外動作,刻意留給 owner),非計畫佔位。

**3. Type consistency:** `FIELDS`/`PUBLISH_COLUMNS`/`DROP_COLUMNS`/`project_row`/`csv_value`(Task 1)被 Task 2 的 `build` 與 Task 3 的測試一致使用;datapackage `resources[0].schema.fields` 由 `dataset.FIELDS` 產生,與 DATASET.md 欄位表同源(測試斷言文件含每欄);版本字串 `YYYY.MM.DD` 在 build(datetime)、datapackage、CITATION.cff、release tag 一致格式。

---

## 執行順序

Task 1 → 2 → 3。Task 1 先(投影 + 安全);Task 2 用其產資產;Task 3 文件(測試依賴 dataset 常數 + 產出語意)。發布(`gh release`)在合併後由 owner 執行。
