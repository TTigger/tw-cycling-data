# -*- coding: utf-8 -*-
import sporter96_pdf as s

HEADER = [(663.4, [(45.7, "Rank"), (115.7, "BIB"), (158.0, "Name"), (233.2, "Team"),
                   (366.6, "Time"), (428.6, "Gap"), (496.3, "Points")]),
          (647.7, [(48.2, "名次"), (106.0, "號碼布"), (158.0, "姓名"), (237.0, "隊伍")])]


def page(*body, category="男⼦ M30"):
    return ([(721.2, [(225.1, category)]), (694.9, [(200.1, "本站成績 / Stage Results")])]
            + HEADER + list(body)
            + [(52.9, [(34.0, "Report Created 2026/9/11 "), (155.3, "下午 05:50:52")])])


def test_rows_status_and_category_normalised():
    cat, rows = s.parse_stage_lines(page(
        (616.2, [(58.8, "1"), (109.0, "32"), (162.5, "何硯宜"), (220.0, "Equipo Kern Pharma"),
                 (366.6, "02:24:54"), (428.6, "+00:00"), (496.3, "65")]),
        (600.0, [(50.1, "DNS"), (109.0, "27"), (162.5, "洪坤弘"), (220.0, "個⼈"), (496.3, "0")]),
        (580.0, [(50.1, "Participants")]),
        (560.0, [(50.1, "DNF 退賽 4 OTL 超時 0")])))
    assert cat == "男子 M30"                     # NFKC folds the ⼦ radical
    assert [r["Rank"] for r in rows] == ["1", "DNS"]   # footer ignored
    rec = s.to_record(rows[1], cat, {"url": "u", "race": "2026 96聯賽武嶺站", "year": 2026,
                                     "date": "2026-09-07"})
    assert rec["status"] == "DNS" and rec["finish_seconds"] is None and rec["team"] is None
    fin = s.to_record(rows[0], cat, {"url": "u", "race": "2026 96聯賽武嶺站", "year": 2026,
                                     "date": "2026-09-07"})
    assert fin["finish_seconds"] == 8694 and fin["age_group"] == "30"
    assert fin["result_label"] == "市民競賽組" and fin["gender"] == "M"


def test_wrapped_name_above_and_below_rank_line():
    # long names are drawn vertically centred: part above, part below the rank line
    _cat, rows = s.parse_stage_lines(page(
        (592.2, [(136.0, " BAENGSANTHIA")]),                       # starts in BIB column
        (585.0, [(58.8, "53"), (109.0, "207"), (220.0, "Hungchen-2Y3"),
                 (366.6, "03:26:23"), (428.6, "+01:01:29"), (496.3, "2")]),
        (577.9, [(151.5, "SANYALAK")])))
    assert len(rows) == 1
    assert rows[0]["Name"] == "BAENGSANTHIA SANYALAK"
    assert rows[0]["Team"] == "Hungchen-2Y3"


def test_non_result_page_is_skipped():
    assert s.parse_stage_lines([(700.0, [(50.0, "團隊積分")])]) == (None, [])
