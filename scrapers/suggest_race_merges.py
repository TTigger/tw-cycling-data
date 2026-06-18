# -*- coding: utf-8 -*-
"""Candidate generator for the race-key normalization REVIEW batch (Feature 🔤).

Reads  data/processed/master.json  (INTERNAL), applies the CURRENT normalization
(normalize.enrich, incl. the existing RACE_KEY_CANONICAL map), then clusters the
remaining 140 distinct race_keys to PROPOSE further merges. It NEVER edits the
map — output is a human-approval table:

  data/processed/race_merge_candidates.md    (review this)
  data/processed/race_merge_candidates.json  (machine-readable)

Two signatures per key:
  safe_core  — strips edition (第N屆/回) / year / ROC-year / English tail /
               generic filler / punctuation, but KEEPS distinctive CJK brands
               (美利達 / 崇越 …) and structural markers (站 段 季 Day Stage S# 組 …).
  loose_core — safe_core AND also strips those structural markers.

Cluster by loose_core. Within a loose cluster the verdict is 3-tier:
  • REJECT — members differ by a CORRUPT marker (Day# / 季 / 部段 / 場次 / paired
             六月·九月). The memory ruled these distinct events (multi-day stages,
             seasonal courses, geographic segments, two editions in one year);
             merging would collapse them and corrupt cross-year/severity.
  • SAFE   — one safe_core, ≥2 keys: pure edition/spelling variants, safe to add.
  • REVIEW — multiple safe_cores, no corrupt marker: genuine judgement calls
             (division splits 挑戰組/競賽組/分齡組, GravelFundo stage/heat) — a
             human must rule whether they are the same race.
Already-merged events collapse to a single key and never reappear. SAFE is a
HINT, not a guarantee — verify before applying (different sponsors can share a
generic tail like 「嘉年華」).
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import common      # noqa: E402
import normalize   # noqa: E402

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.json")
OUT = os.path.join(HERE, "..", "data", "processed")

# generic filler that distinguishes editions, not events. NOTE: distinctive
# brands (美利達 / 崇越 / 兆豐 …) are deliberately NOT stripped — the brand is
# part of the event identity, so keeping it prevents over-merging two different
# sponsors' races that share a generic tail (e.g. …嘉年華).
_STOP = [
    "中華民國", "自行車", "自由車", "單車", "腳踏車", "公路車",
    "挑戰賽", "挑戰", "錦標賽", "邀請賽", "大賽", "系列賽", "系列活動", "系列",
    "比賽", "賽事", "活動", "成績總表", "成績紀錄", "成績", "總表", "大會師",
    "暨", "之", "盃", "杯", "屆",
]
_STOP_RE = re.compile("|".join(map(re.escape, sorted(_STOP, key=len, reverse=True))))

# structural markers: their presence means a key may be a *sub-event*, kept in
# safe_core so different sub-events don't collapse — stripped only in loose_core.
_STRUCT = re.compile(
    r"Day\s?\d+|Stage\s?\d+|S\d+|Round\s?\d+|第?\d+站|[冬春夏秋]季|季|[一二三四五六七八九十\d]+月|"
    r"場次|[上下]午|[東西南北中]部段|.段|Heroes|KOM|挑戰組|競賽組|市民組|巿民組|分齡組",
    re.I,
)

# corrupt-merge markers (memory): differ-by-these = genuinely distinct events.
_CORRUPT = re.compile(r"Day\s?\d|[冬春夏秋]季|[東西南北中]部段|場次|六月|九月", re.I)


def _strip_edition(s):
    s = s or ""
    s = re.sub(r"20[0-2]\d", "", s)            # western year
    s = re.sub(r"^1\d\d年", "", s)             # leading ROC year (102年 / 114年)
    s = re.sub(r"第?\d+[屆回]", "", s)         # edition no.
    return s


def safe_core(name):
    s = _strip_edition(name)
    s = re.sub(r"[A-Za-z]+", "", s)            # English transliteration tails
    s = _STOP_RE.sub("", s)                    # sponsor / filler
    s = re.sub(r"[\s．.、&·,／/\-‑—_()（）「」『』【】\[\]:：!！]", "", s)
    s = s.replace("巿", "市")
    return s


def loose_core(name):
    s = _STRUCT.sub("", name or "")
    s = safe_core(s)
    s = re.sub(r"\d+", "", s)                  # any remaining digits
    return s


def main():
    agg = defaultdict(lambda: {"years": set(), "rows": 0, "name": None})
    for r in common.iter_records(IN):
        normalize.enrich(r)
        rk = r.get("race_key")
        if not rk:
            continue
        a = agg[rk]
        a["rows"] += 1
        if r.get("year"):
            a["years"].add(r["year"])
        if a["name"] is None:
            a["name"] = r.get("race_name_canonical") or rk

    keys = {rk: {"rk": rk, "name": v["name"], "rows": v["rows"],
                 "years": sorted(v["years"]),
                 "safe": safe_core(v["name"]), "loose": loose_core(v["name"])}
            for rk, v in agg.items()}

    clusters = defaultdict(list)
    for k in keys.values():
        if k["loose"]:                         # skip keys that reduce to empty
            clusters[k["loose"]].append(k)

    _ORDER = {"SAFE": 0, "REVIEW": 1, "REJECT": 2}
    cands = []
    for loose, members in clusters.items():
        if len(members) < 2:
            continue
        safes = {m["safe"] for m in members}
        corrupt = any(_CORRUPT.search(m["name"] or "") for m in members)
        if len(safes) > 1 and corrupt:
            verdict = "REJECT"
        elif len(safes) == 1:
            verdict = "SAFE"
        else:
            verdict = "REVIEW"
        members = sorted(members, key=lambda m: (-m["rows"]))
        cands.append({
            "verdict": verdict, "loose": loose,
            "safe_cores": sorted(safes),
            "members": [{"rk": m["rk"], "name": m["name"], "rows": m["rows"],
                         "years": m["years"]} for m in members],
            "total_rows": sum(m["rows"] for m in members),
        })

    cands.sort(key=lambda c: (_ORDER[c["verdict"]], -len(c["members"]), -c["total_rows"]))

    with open(os.path.join(OUT, "race_merge_candidates.json"), "w", encoding="utf-8") as f:
        json.dump(cands, f, ensure_ascii=False, indent=1)

    n = {t: sum(c["verdict"] == t for c in cands) for t in _ORDER}
    lines = ["# 賽名正規化 — 候選合併表(需人工逐組核可,未自動套用)", ""]
    lines.append(f"來源:140 個 race_key → {len(cands)} 個候選群組"
                 f"({n['SAFE']} SAFE / {n['REVIEW']} REVIEW / {n['REJECT']} REJECT)。")
    lines.append("REJECT = 依既有判準視為不同賽事(多日/季節/路段/同年多場),合併會破壞跨年。"
                 " SAFE 僅為提示,仍須核對。")
    lines.append("")
    for tag in ("SAFE", "REVIEW", "REJECT"):
        group = [c for c in cands if c["verdict"] == tag]
        lines.append(f"## {tag}({len(group)} 組)")
        lines.append("")
        for i, c in enumerate(group, 1):
            lines.append(f"### {tag}-{i}  ·  {len(c['members'])} 鍵 / {c['total_rows']} 筆")
            for m in c["members"]:
                yrs = ",".join(map(str, m["years"])) or "—"
                lines.append(f"- `{m['rk']}`  ({yrs}; {m['rows']} 筆) — {m['name']}")
            lines.append("")
    with open(os.path.join(OUT, "race_merge_candidates.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"candidates: {len(cands)} "
          f"(SAFE {n['SAFE']}, REVIEW {n['REVIEW']}, REJECT {n['REJECT']}) "
          f"-> data/processed/race_merge_candidates.md")


if __name__ == "__main__":
    main()
