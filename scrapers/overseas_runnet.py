# -*- coding: utf-8 -*-
"""Process a RUNNET (result.one.runnet.jp) overseas race into a de-identified
dataset — kept SEPARATE from the Taiwan master so it never skews Taiwan stats.

RUNNET is a Next.js SPA, so results are JS-rendered (no static GET). The raw
finisher table is captured with a headless browser (Chrome DevTools / Playwright)
by extracting every category <table> on /races/<id>/race-top into a JSON like:
  {race, date, data:[{category, rows:[{rank,bib,name,team,net,overall}]}]}
This script turns that into unified, masked records.

Usage:
  python overseas_runnet.py <raw_extraction.json> <raceId> <region>
Output: data/processed/_overseas/runnet_<raceId>.json (+ .public.json)
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
# internal (has name_raw) stays under data/processed (gitignored); the
# de-identified public copy goes to web/public/data/overseas (deploy artifact).
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "_overseas")
PUB_DIR = os.path.join(common.PUBLIC_DATA_DIR, "overseas")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PUB_DIR, exist_ok=True)


def _gender(category):
    if "女子" in category or "女" in category:
        return "F"
    if "男子" in category or "男" in category:
        return "M"
    return None


def _age_band(category):
    m = re.search(r"(\d{1,2})\s*[～~\-]\s*(\d{1,2})\s*歳", category)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"(\d{1,2})\s*歳以上", category)
    return f"{m.group(1)}+" if m else None


def build(raw, race_id, region):
    race = raw.get("race") or f"runnet {race_id}"
    date = raw.get("date")
    year = common.extract_year(date or race)
    out = []
    for cat in raw.get("data", []):
        category = cat.get("category") or ""
        gender = _gender(category)
        age = _age_band(category)
        for r in cat.get("rows", []):
            name = (r.get("name") or "").strip()
            if not name:
                continue
            net = (r.get("net") or "").strip()
            rank = r.get("rank")
            out.append(common.make_record(
                source_platform="runnet.jp", source_url=f"https://result.one.runnet.jp/races/{race_id}",
                source_format="html-headless", race_name_raw=f"{year} {race}",
                year=year, date=date, race_type="hillclimb", region=region,
                result_label="種目別順位", category_raw=category, gender=gender, age_group=age,
                rank_overall=int(rank) if str(rank).isdigit() else None,
                bib=r.get("bib") or None, name_raw=name, team=(r.get("team") or None),
                finish_time=net or None,
                finish_seconds=common.time_to_seconds(net) if net else None,
                scraped_at="2026-06-11"))
    return out


def main():
    if len(sys.argv) < 4:
        print("usage: python overseas_runnet.py <raw.json> <raceId> <region>")
        return
    raw_path, race_id, region = sys.argv[1], sys.argv[2], sys.argv[3]
    raw = json.load(open(raw_path, encoding="utf-8"))
    recs = build(raw, race_id, region)
    full = os.path.join(OUT_DIR, f"runnet_{race_id}.json")
    json.dump(recs, open(full, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    pub = [{k: v for k, v in r.items() if k != "name_raw"} for r in recs]
    json.dump(pub, open(os.path.join(PUB_DIR, f"runnet_{race_id}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    from collections import Counter
    print(f"records={len(recs)} race={raw.get('race')}")
    print(f"  categories={len(raw.get('data', []))} gender={dict(Counter(r['gender'] for r in recs))}")
    print(f"  sample: {recs[0]['name_masked']} [{recs[0]['category_raw']}] "
          f"{recs[0]['finish_time']} rank={recs[0]['rank_overall']}")
    print(f"  -> {os.path.relpath(full)} (internal) + web/public/data/overseas/runnet_"
          f"{race_id}.json (public) — SEPARATE from Taiwan master")


if __name__ == "__main__":
    main()
