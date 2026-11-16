# -*- coding: utf-8 -*-
import irunner_crawl


def test_event_date_from_page_header():
    html = ("<h1 class='h3'>2026 Gravel Fundo</h1><div class='mt-2'>"
            "<i class='fa fa-calendar me-2'></i>2026/01/25</div>")
    assert irunner_crawl.event_date(html) == "2026-01-25"
    assert irunner_crawl.event_date("<p>no date</p>") is None


def test_combined_track_split_into_one_race_per_group():
    rows = [{"memno": "1", "division": "北高360．男", "bib": "1", "name": "王大明", "time": "20:00:00"},
            {"memno": "2", "division": "雙塔520．女", "bib": "2", "name": "陳小美", "time": "30:00:00"}]
    recs = irunner_crawl.to_records(1581, "2026 TBA 北高360+雙塔520", 2026, rows, "2026-11-13")
    assert sorted(r["race_key"] for r in recs) == ["北高360認證成績表2026", "雙塔520認證成績表2026"]
    other = irunner_crawl.to_records(1, "某某盃", 2026, rows)
    assert {r["race_name_raw"] for r in other} == {"某某盃"}
