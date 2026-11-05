# -*- coding: utf-8 -*-
"""Parsers for sport-result.com, e-better and ATSport (fixtures use made-up names)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import atsport_crawl as at  # noqa: E402
import ebetter_crawl as eb  # noqa: E402
import merge  # noqa: E402
import sport_result_crawl as sr  # noqa: E402


def sr_row(**kw):
    r = {"bib": "1", "name": "王大明", "e_name": "", "gender": "男", "team_name": "",
         "total_place": 2, "gender_place": 2, "group_place": 2, "status": "0",
         "time_official": "02:31:50", "time_chip": "02:29:46",
         "race_name": "市民競賽組", "group_name": "男M40"}
    r.update(kw)
    return r


class TestSportResult:
    contest = {"slug": "2026090702", "name": "2026 96聯賽 武嶺站 競賽組", "event_date": "2026-09-07"}

    def test_keeps_finishers_on_the_existing_race(self):
        rows = [sr_row(), sr_row(bib="2", status="1", time_official="", total_place=None),
                sr_row(bib="3", status="3", time_official="")]
        recs = sr.build_records(rows, self.contest, "2026-11-03")
        assert len(recs) == 1
        r = recs[0]
        assert r["race_key"] == "96聯賽武嶺站競賽組及市民競賽組" and r["year"] == 2026
        assert (r["result_label"], r["category_raw"], r["gender"], r["age_group"]) == \
            ("市民競賽組", "男M40", "M", "40")
        assert r["finish_seconds"] == 9110 and r["rank_overall"] == 2
        assert r["name_masked"] == "王○明"

    def test_course_label_override_and_unknown_contest(self):
        c = {"slug": "2026090701", "name": "x", "event_date": "2026-09-07"}
        r = sr.build_records([sr_row(race_name="96Heroes中華賓士武嶺站-挑戰組", group_name="女子組",
                                     gender="女")], c, "d")[0]
        assert r["result_label"] == "挑戰組-武嶺站" and r["gender"] == "F"
        other = {"slug": "2027010101", "name": "2027 某某自行車賽", "event_date": "2027-01-01"}
        assert sr.build_records([sr_row()], other, "d")[0]["race_name_canonical"] == "某某自行車賽"

    def test_cycling_filter(self):
        assert sr.is_cycling({"slug": "x", "name": "2026 96聯賽 武嶺站 競賽組"})
        assert not sr.is_cycling({"slug": "x", "name": "2026金門鐵人三項挑戰賽"})
        assert not sr.is_cycling({"slug": "x", "name": "2026新北市萬金石馬拉松"})


def eb_row(**kw):
    r = {"runner_num_": "0046", "name_": "陳小華", "team_": "某車隊", "subgroup_title_": "F30",
         "gender_": "0", "canceled_": "0", "group_title_": "55K/3275M", "rank_": "7",
         "result_": "02:40:56"}
    r.update(kw)
    return r


class TestEbetter:
    ev = {"sn": 6903, "race": "TIS崇越盃武嶺自行車挑戰賽(九月場次)", "year": 2026, "date": None,
          "region": "南投縣"}

    def test_build(self):
        recs = eb.build_records([eb_row(), eb_row(canceled_="1"), eb_row(result_="")], self.ev, "d")
        assert len(recs) == 1
        r = recs[0]
        assert r["race_key"] == "TIS崇越盃武嶺自行車挑戰賽九月場次"
        assert (r["gender"], r["age_group"], r["rank_overall"], r["team"]) == ("F", "30", 7, "某車隊")
        assert r["source_url"] == "https://gr.e-better.com.tw/eb/gr/6903"

    def test_gender_can_be_switched_off(self):
        r = eb.build_records([eb_row(gender_="1")], {**self.ev, "gender": False}, "d")[0]
        assert r["gender"] is None


AT_PAGE = """
<a class="dropdown-item event_detail_item" href="javascript:void(0);" data-id='' data-name='全部分組' >全部分組</a>
<a class="dropdown-item event_detail_item" href="javascript:void(0);" data-id='32' data-name='挑戰賽' >
    挑戰賽 (2012-07-22)
</a>
<a class="dropdown-item event_detail_item" href="javascript:void(0);" data-id='33' data-name='競賽組-男' >
    競賽組-男 (2012-07-22)
</a>
<div class="list-group">
<a href="javascript:void(0);" class="score_detail_link list-group-item" data-route="x">
  <div class="rank-col rank-oa"><b class="rank-none">3</b><small></small></div>
  <div class="list-group-item-body">
    <h5><span class="row-no d-none d-md-inline">1.</span>林阿土</h5>
    <div class="d-flex"><p>0142</p><p>M25</p><p></p><p></p></div>
    <div class="d-md-none score-mb"><span class="score-time">02:30:42.990</span></div>
  </div>
</a>
<a href="javascript:void(0);" class="score_detail_link list-group-item" data-route="y">
  <div class="rank-col rank-oa"><b class="rank-none">—</b><small></small></div>
  <div class="list-group-item-body">
    <h5><span class="row-no d-none d-md-inline">2.</span>張三</h5>
    <div class="d-flex"><p>0143</p><p></p></div>
  </div>
</a>
</div>
"""


class TestAtsport:
    def test_courses(self):
        assert at.parse_courses(AT_PAGE) == [("32", "挑戰賽", "2012-07-22"),
                                             ("33", "競賽組-男", "2012-07-22")]

    def test_rows(self):
        rows = at.parse_rows(AT_PAGE)
        assert rows[0] == {"rank": 3, "name": "林阿土", "bib": "0142", "group": "M25",
                           "time": "02:30:42.990"}
        assert rows[1]["time"] is None and rows[1]["rank"] is None and rows[1]["group"] is None


def test_merge_discovers_new_sources_and_drops_the_96_pdf():
    for p in ("sport_result_", "ebetter_", "atsport_"):
        assert p in merge.SOURCE_PREFIXES
    pdf = {"source_platform": "96sporter.com", "race_key": "96聯賽武嶺站競賽組及市民競賽組", "year": 2026}
    assert merge.is_superseded(pdf)
    assert not merge.is_superseded({**pdf, "source_platform": "sport-result.com"})


def test_ebetter_scan_keywords():
    for t in ("2026 TIS桃園台南280KM雙城挑戰賽", "2026台灣登山大滿貫自行車系列賽", "瘋系列第三屆環台賽-西部段",
              "Ciao! Wilier 2000 x Thermaltake"):
        assert eb.CYCLING.search(t) and not eb.NOT_CYCLING.search(t), t
    assert eb.NOT_CYCLING.search("2026 某某馬拉松 42K")
