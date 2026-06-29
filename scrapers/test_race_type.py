# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import race_type as rt


def test_classify():
    assert rt.classify("臺灣KOM登山王挑戰") == "climb"
    assert rt.classify("建大武嶺盃") == "climb"
    assert rt.classify("台中城市繞圈賽") == "crit"
    assert rt.classify("市長盃公路賽", "37.7KM個人公路賽") == "road"
    assert rt.classify("某盃", "個人計時賽") == "tt"
    assert rt.classify("戀戀197") == "road"
    assert rt.classify(None) == "road"
    # climb wins over other keywords
    assert rt.classify("武嶺繞圈計時") == "climb"


def test_criterium_name_classifies_as_crit():
    import race_type
    assert race_type.classify("苗栗繞圈賽（第七屆）") == "crit"
