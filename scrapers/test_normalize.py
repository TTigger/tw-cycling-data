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


def test_gender_from_category_codes():
    assert nz.gender_from_category("RM35") == "M"
    assert nz.gender_from_category("M40") == "M"
    assert nz.gender_from_category("RW30") == "F"
    assert nz.gender_from_category("W20") == "F"
    assert nz.gender_from_category("Ｍ45") == "M"
    assert nz.gender_from_category("男子組") == "M"
    assert nz.gender_from_category("女子菁英") == "F"


def test_gender_from_category_none_when_unsexed_or_mixed():
    for c in ("107K單車自我挑戰", "經典組", "一般組", "挑戰組", "雙塔520",
              "市民組78KM", "U15", "A", "F", "MTB越野", "100KM挑戰組-第二梯", None):
        assert nz.gender_from_category(c) is None, c
    assert nz.gender_from_category("男女混合") is None     # explicit mixed -> None


def test_age_from_category():
    assert nz.age_from_category("RM35") == "35"
    assert nz.age_from_category("W20") == "20"
    assert nz.age_from_category("一般組") is None


def test_enrich_backfills_gender_and_ageband_when_missing():
    r = {"category_raw": "RM35", "gender": None, "age_group": None,
         "result_label": None, "race_name_raw": "某盃"}
    nz.enrich(r)
    assert r["gender"] == "M"
    assert r["age_band"] == "30-39"          # 35 from the code


def test_enrich_does_not_override_existing_gender_or_agegroup():
    r = {"category_raw": "RW30", "gender": "M", "age_group": "40",
         "result_label": None, "race_name_raw": "某盃"}
    nz.enrich(r)
    assert r["gender"] == "M"                 # existing kept, code (F) ignored
    assert r["age_band"] == "40-49"           # from existing age_group, not code
