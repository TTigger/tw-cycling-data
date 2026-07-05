# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import criterium_parse as cp

EVENT_HTML = (
    '<h1>男子A組</h1>'
    '<table class="tbl"><thead><tr><th>#</th><th>BIB</th><th>姓名</th>'
    '<th>分組</th><th>隊伍</th><th style="text-align:right">完賽時間</th>'
    '<th style="text-align:right">圈數</th><th>狀態</th></tr></thead><tbody>'
    '<tr class="row-link"><td class="rank"><span class="pos pos-1">01</span></td>'
    '<td class="tnum">2</td><td>陳大文<!-- --> <span class="mono">★</span></td>'
    '<td class="tnum">M<!-- --> / M30</td><td>.UTSUNOMIYA BLITZEN 宇都宮車隊</td>'
    '<td class="tnum">00:47:38</td><td class="tnum">35</td>'
    '<td><span class="pill fin"><span class="dot"></span>FIN</span></td></tr>'
    '<tr class="row-link"><td class="rank"><span class="pos">—</span></td>'
    '<td class="tnum">21</td><td>洪稟詠<!-- --> </td>'
    '<td class="tnum">M<!-- --> / U23</td><td>TEAM CYTO TRIGON</td>'
    '<td class="tnum">—</td><td class="tnum">25</td>'
    '<td><span class="pill dnf"><span class="dot"></span>DNF</span></td></tr>'
    '<tr class="row-link"><td class="rank"><span class="pos">—</span></td>'
    '<td class="tnum">13</td><td>朱耿宏<!-- --> </td>'
    '<td class="tnum">M<!-- --> / ELITE</td><td>MSG CYCLING TEAM 衝線單車</td>'
    '<td class="tnum">—</td><td class="tnum">0</td>'
    '<td><span class="pill dnf"><span class="dot"></span>DNS</span></td></tr>'
    '<tr class="row-link"><td class="rank"><span class="pos">—</span></td>'
    '<td class="tnum">7</td><td>林大明<!-- --> </td>'
    '<td class="tnum">M<!-- --> / M40</td><td>Test Team A</td>'
    '<td class="tnum">—</td><td class="tnum">10</td>'
    '<td><span class="pill dnf"><span class="dot"></span>DQ</span></td></tr>'
    '<tr class="row-link"><td class="rank"><span class="pos">—</span></td>'
    '<td class="tnum">8</td><td>陳小華<!-- --> </td>'
    '<td class="tnum">M<!-- --> / M50</td><td>Test Team B</td>'
    '<td class="tnum">—</td><td class="tnum">0</td>'
    '<td><span class="pill "><span class="dot"></span>SRT</span></td></tr>'
    '<tr class="row-link"><td class="rank"><span class="pos">—</span></td>'
    '<td class="tnum">9</td><td>王阿強<!-- --> </td>'
    '<td class="tnum">M<!-- --> / U17</td><td>Test Team C</td>'
    '<td class="tnum">—</td><td class="tnum">0</td>'
    '<td><span class="pill "><span class="dot"></span>NYS</span></td></tr>'
    '</tbody></table>'
)

OVERVIEW_HTML = (
    '<h1>苗栗繞圈賽</h1>'
    '<script type="application/ld+json">{"@type":"SportsEvent",'
    '"name":"苗栗繞圈賽（第七屆）","startDate":"2026-06-28",'
    '"location":{"@type":"Place","name":"苗栗·後龍"}}</script>'
    '<a href="/races/19554/events/4">男子A組</a>'
    '<a href="/races/19554/events/5">男子B組</a>'
    '<a href="/races/19554/events/4">dup</a>'
)


def test_event_name():
    assert cp.event_name(EVENT_HTML) == "男子A組"


def test_parse_event_page_fin_row():
    rows = cp.parse_event_page(EVENT_HTML)
    assert len(rows) == 6
    fin = rows[0]
    assert fin["rank"] == 1
    assert fin["bib"] == "2"
    assert fin["name"] == "陳大文"        # ★ marker stripped
    assert fin["category"] == "M / M30"
    assert fin["team"] == ".UTSUNOMIYA BLITZEN 宇都宮車隊"
    assert fin["finish_time"] == "00:47:38"
    assert fin["laps"] == 35
    assert fin["status"] == "FIN"


def test_parse_event_page_dnf_and_dns():
    rows = cp.parse_event_page(EVENT_HTML)
    dnf, dns = rows[1], rows[2]
    assert dnf["status"] == "DNF" and dnf["rank"] is None
    assert dnf["finish_time"] is None and dnf["laps"] == 25
    # DNS row carries class "pill dnf" but TEXT "DNS" — text wins:
    assert dns["status"] == "DNS" and dns["laps"] == 0


def test_parse_category():
    assert cp.parse_category("M / M30") == ("M", "30")
    assert cp.parse_category("M / U23") == ("M", "U23")
    assert cp.parse_category("M / ELITE") == ("M", None)


def test_parse_race_meta():
    m = cp.parse_race_meta(OVERVIEW_HTML)
    assert m["name"] == "苗栗繞圈賽（第七屆）"
    assert m["date"] == "2026-06-28"
    assert m["year"] == 2026
    assert m["region"] == "苗栗"
    assert m["event_ids"] == [4, 5]   # de-duped, in order


def test_parse_event_page_dq_srt_nys():
    rows = cp.parse_event_page(EVENT_HTML)
    dq, srt, nys = rows[3], rows[4], rows[5]
    # DQ: disqualified — pill class "dnf" but text is "DQ"
    assert dq["status"] == "DQ" and dq["rank"] is None
    assert dq["finish_time"] is None
    # SRT: started but retired early — pill class has trailing space "pill "
    assert srt["status"] == "SRT" and srt["rank"] is None
    assert srt["finish_time"] is None
    # NYS: not yet started — pill class has trailing space "pill "
    assert nys["status"] == "NYS" and nys["rank"] is None
    assert nys["finish_time"] is None


def test_parse_event_page_malformed_time():
    """Regression: malformed time like '00:47:38junk' should not pass fullmatch."""
    malformed_html = (
        '<h1>test</h1>'
        '<table class="tbl"><thead><tr><th>#</th><th>BIB</th><th>姓名</th>'
        '<th>分組</th><th>隊伍</th><th style="text-align:right">完賽時間</th>'
        '<th style="text-align:right">圈數</th><th>狀態</th></tr></thead><tbody>'
        '<tr class="row-link"><td class="rank"><span class="pos pos-1">01</span></td>'
        '<td class="tnum">2</td><td>Test Rider</td>'
        '<td class="tnum">M / M30</td><td>Test Team</td>'
        '<td class="tnum">00:47:38junk</td><td class="tnum">35</td>'
        '<td><span class="pill fin"><span class="dot"></span>FIN</span></td></tr>'
        '</tbody></table>'
    )
    rows = cp.parse_event_page(malformed_html)
    assert len(rows) == 1
    row = rows[0]
    assert row["name"] == "Test Rider"
    assert row["finish_time"] is None  # malformed time must reject
    assert row["status"] == "FIN"  # but status should still parse
