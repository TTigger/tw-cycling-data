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
    """Whitelist projection: only PUBLISH_COLUMNS, fixed order, missing -> None.
    Public-dataset name safeguard: emit a masked name only when it is actually
    masked (contains the ○ glyph). Upstream mask_name only masks CJK names, so
    romanized names ("ABBY R.") and scraping junk ("<span c.", "1.") arrive
    UNmasked — blank them here so no real given name leaks into the release."""
    out = {c: row.get(c) for c in PUBLISH_COLUMNS}
    nm = out.get("name_masked")
    if nm is not None and "○" not in nm:
        out["name_masked"] = None
    return out


def csv_value(v):
    """CSV-safe stringification. list/dict -> compact JSON (ensure_ascii off);
    None -> empty string; everything else -> str."""
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)
