# -*- coding: utf-8 -*-
"""cyclist_archive: column-by-position rows from old cyclist.org.tw PDFs.
Names below are placeholders, not riders."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import cyclist_archive as A  # noqa: E402
import cyclist_crawl  # noqa: E402


def W(text, x0, width=None):
    return {"text": text, "x0": x0, "x1": x0 + (width or 6 * len(text)), "top": 0}


def row(*words):
    return [W(t, x) for t, x in words]


HEADER = row(("編號", 40), ("總排名", 70), ("姓名", 145), ("組別", 215), ("車隊", 290), ("完成時間", 460))


def _parse(rows, header=HEADER):
    return A.parse_block(A._header(header), rows)


def test_multi_word_name_stays_apart_from_team():
    rows = [row(("12", 42), ("1", 75), ("John", 100), ("Doe", 130), ("Elite", 215), ("某某", 290), ("車隊", 305), ("03:20:00.00", 460)),
            row(("7", 42), ("2", 75), ("王小明", 100), ("M30組", 215), ("個人", 290), ("03:25:00.00", 460))]
    a, b = _parse(rows)
    assert a["name"] == "John Doe" and a["team"] == "某某 車隊" and a["div"] == "Elite"
    assert b["name"] == "王小明" and b["rank"] == 2 and b["secs"] == 3 * 3600 + 25 * 60


def test_label_over_the_wrong_number_column_is_swapped_back():
    # 編號 / 總排名 labels sit over the other number column: rank is the one counting up
    rows = [row(("2051", 42), ("1", 75), ("王小明", 100), ("M35組", 215), ("某隊", 290), ("05:12:07.06", 460)),
            row(("88", 42), ("2", 75), ("陳大文", 100), ("M35組", 215), ("某隊", 290), ("05:12:12.77", 460)),
            row(("9", 42), ("3", 75), ("李小華", 100), ("M40組", 215), ("某隊", 290), ("05:14:12.04", 460))]
    hdr = row(("總排名", 40), ("編號", 70), ("姓名", 145), ("組別", 215), ("車隊", 290), ("完成時間", 460))
    out = _parse(rows, hdr)
    assert [r["rank"] for r in out] == [1, 2, 3] and [r["bib"] for r in out] == ["2051", "88", "9"]


def test_page_titles_are_not_rider_rows():
    assert not A._is_data(row(("365KM", 40), ("Challenge", 80), ("06:00", 200)))
    assert A._is_data(row(("1", 40), ("12", 70), ("王小明", 100), ("00:37:14.58", 400)))
    assert A._is_data(row(("RM15", 40), ("185", 70), ("王小明", 100), ("2:52:29", 400)))
    assert A._is_data(row(("DNF", 40), ("12", 70), ("王小明", 100)))


def test_mm_ss_times_and_status_rows():
    r = A.parse_row({"rank": ["1"], "bib": ["5"], "name": ["王小明"], "time": ["57:33"]})
    assert r["time"] == "00:57:33" and r["secs"] == 57 * 60 + 33
    r = A.parse_row({"bib": ["9"], "name": ["陳大文"], "time": ["DNF"]})
    assert r["status"] == "DNF" and r["secs"] is None
    assert A.parse_row({"bib": ["9"], "name": ["陳大文"]}) is None


def test_pick_skips_copies_points_and_top_six():
    pdfs = [("請按此", "a.pdf"), ("4/21 總排名成績", "b.pdf"), ("4/21 分組排名成績", "c.pdf"),
            ("團體積分總排名", "d.pdf"), ("各分組前六名", "e.pdf")]
    assert A.pick(pdfs, ["總排名"]) == [("4/21 總排名成績", "b.pdf")]


def test_cache_names_keep_cjk_files_apart():
    a = cyclist_crawl.local_name("upfile/resultPDF/41/菁英組成績.pdf")
    b = cyclist_crawl.local_name("upfile/resultPDF/41/市民組成績.pdf")
    assert a != b
    assert cyclist_crawl.local_name("/upfile/file/20181009/1.pdf") == "upfile_file_20181009_1.pdf"
