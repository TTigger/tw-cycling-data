# -*- coding: utf-8 -*-
"""Scrape TCU criterium (繞圈賽) results from events.criterium.tw.

A small multi-event timing platform; server-rendered HTML, no JS/auth needed.
Per race: GET the overview page for name/date + event sub-page ids, then GET
each /races/{id}/events/{n} and parse the results table. This is the ONLY
source that exposes FIN/DNF/DNS status + lap counts. /api/ is robots-disallowed,
so we scrape the rendered pages. Output: data/processed/criterium_2024_2026.json
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402
import criterium_parse as cp  # noqa: E402

BASE = "https://events.criterium.tw"
SEED_RACE_IDS = [19554, 19267, 18931, 18772, 18571]
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                   "criterium_2024_2026.json")


def build_records(parsed_rows, race_meta, event_label, event_url, scraped_at):
    recs = []
    for row in parsed_rows:
        gender, age = cp.parse_category(row.get("category"))
        recs.append(common.make_record(
            source_platform="criterium.tw", source_url=event_url,
            source_format="html",
            race_name_raw=race_meta.get("name"), year=race_meta.get("year"),
            date=race_meta.get("date"), region=race_meta.get("region"),
            result_label=event_label, category_raw=row.get("category"),
            gender=gender, age_group=age,
            rank_overall=row.get("rank"), bib=row.get("bib"),
            team=row.get("team"), name_raw=row.get("name"),
            finish_time=row.get("finish_time"),
            status=row.get("status"), laps=row.get("laps"),
            scraped_at=scraped_at))
    return recs


def crawl(race_ids, session=None):
    session = session or common.make_session()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for rid in race_ids:
        ov = common.polite_get(session, f"{BASE}/races/{rid}").text
        meta = cp.parse_race_meta(ov)
        print(f"  race {rid}: {meta.get('name')} ({meta.get('date')}) "
              f"events={meta.get('event_ids')}")
        for n in (meta.get("event_ids") or []):
            url = f"{BASE}/races/{rid}/events/{n}"
            html = common.polite_get(session, url).text
            rows = cp.parse_event_page(html)
            out.extend(build_records(rows, meta, cp.event_name(html), url, now))
    return out


def main():
    recs = crawl(SEED_RACE_IDS)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    print(f"\n  {len(recs)} rows -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
