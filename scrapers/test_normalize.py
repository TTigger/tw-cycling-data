# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import normalize as nz


def test_age_band_five_year_codes():
    assert nz.age_band("20") == "19-29"
    assert nz.age_band("25") == "19-29"
    assert nz.age_band("30") == "30-39"
    assert nz.age_band("35") == "30-39"
    assert nz.age_band("40") == "40-49"
    assert nz.age_band("55") == "50-59"
    assert nz.age_band("60") == "60+"


def test_age_band_ranges_by_lower_bound():
    assert nz.age_band("19-23") == "19-29"
    assert nz.age_band("24-35") == "19-29"   # bucketed by lower bound
    assert nz.age_band("30-39") == "30-39"
    assert nz.age_band("40-49") == "40-49"


def test_age_band_youth_and_master():
    assert nz.age_band("U13") == "U19"
    assert nz.age_band("U15") == "U19"
    assert nz.age_band("15") == "U19"
    assert nz.age_band("16") == "U19"
    assert nz.age_band("36") == "30-39"
    assert nz.age_band("MASTER") == "MASTER"


def test_age_band_junk_and_empty():
    assert nz.age_band("4-1") is None    # implausible -> parse junk
    assert nz.age_band(None) is None
    assert nz.age_band("") is None
    assert nz.age_band("abc") is None


def test_enrich_sets_age_band():
    r = {"age_group": "40", "result_label": "分齡", "category_raw": "M40",
         "race_name_raw": "2025 太平山王"}
    nz.enrich(r)
    assert r["age_band"] == "40-49"
    assert "race_class" in r and "series" in r
