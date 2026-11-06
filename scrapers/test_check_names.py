# -*- coding: utf-8 -*-
"""check_names: finds real rider names in files. Names below are placeholders."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import check_names as C  # noqa: E402

NAMES = {"王大明", "陳小美", C.latin_key("Jane Q Public")}


def test_text_finds_names_inside_longer_strings():
    text = 'row = ["1", "王大明", "某車隊"]\n# rider Jane q PUBLIC finished\n'
    assert C.find_in_text(text, NAMES) == {"王大明", "Jane q PUBLIC"}
    assert C.find_in_text("王○明 和 J○ Q○ P○", NAMES) == set()


def test_json_checks_whole_values_and_words_only():
    data = {"team": "陳小美", "race": "大明湖王大明盃", "rows": [{"n": "Jane Q Public"}]}
    assert C.find_in_json(data, NAMES) == {"陳小美", "Jane Q Public"}


def test_hits_print_masked():
    assert C.common.mask_name("王大明") == "王○明"
