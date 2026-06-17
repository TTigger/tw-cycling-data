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


def test_series_gravelfundo_and_tcu_circuit():
    assert nz.series_of("GravelFundo Stage1 台南玉井站") == "GravelFundo 礫石越野系列"
    assert nz.series_of("秋季TCU台中城市繞圈賽") == "TCU 台中城市繞圈賽"
    assert nz.series_of("春季TCU台中城市繞圈賽Y12組別") == "TCU 台中城市繞圈賽"
    # the 中寮 KOM climb is NOT a city criterium -> must not join the TCU series
    assert nz.series_of("TCU三發國王盃中寮KOM單車挑戰賽") != "TCU 台中城市繞圈賽"


def test_race_class_age_codes_incl_road_prefix():
    assert nz.race_class(category_raw="M35") == "分齡"
    assert nz.race_class(category_raw="RM35") == "分齡"     # road-prefixed (was 未分類)
    assert nz.race_class(category_raw="RW30") == "分齡"
    assert nz.race_class(category_raw="MASTER") == "分齡"
    assert nz.race_class(category_raw="MTB男子組") == "未分類"  # not an age code -> unchanged


def test_race_class_general_citizen_and_default():
    assert nz.race_class(category_raw="一般組") == "市民"
    assert nz.race_class(category_raw="北高360") == "未分類"   # class set via series in enrich
    assert nz.race_class(category_raw="A") == "未分類"          # criterium letter stays unclassified


def test_enrich_marks_long_distance_cert_series_as_認證():
    r = {"race_key": "x", "race_name_canonical": "北高360",
         "race_name_raw": "2025北高360雙塔520四極602自行車認證",
         "category_raw": "北高360", "result_label": None, "year": 2025}
    nz.enrich(r)
    assert r["series"] == "TBA 長途認證"
    assert r["race_class"] == "認證"


def test_enrich_canonicalizes_merged_race_keys():
    r = {"race_key": "美利達盃amp;單車嘉年華", "race_name_canonical": "美利達盃&amp;單車嘉年華",
         "category_raw": None, "result_label": None, "race_name_raw": "2023美利達盃&amp;單車嘉年華", "year": 2023}
    nz.enrich(r)
    assert r["race_key"] == "美利達盃單車嘉年華"
    assert r["race_name_canonical"] == "美利達盃單車嘉年華"


def test_enrich_leaves_unmapped_race_keys_untouched():
    r = {"race_key": "建大武嶺盃", "race_name_canonical": "建大武嶺盃",
         "category_raw": None, "result_label": None, "race_name_raw": "建大武嶺盃", "year": 2024}
    nz.enrich(r)
    assert r["race_key"] == "建大武嶺盃"


def test_canonical_map_keeps_distinct_events_separate():
    m = nz.RACE_KEY_CANONICAL
    # 崇越武嶺 dated rounds and different-organizer 武嶺 are NOT collapsed
    assert "TIS崇越盃武嶺自行車挑戰賽六月場次" not in m
    assert "TIS崇越盃武嶺自行車挑戰賽九月場次" not in m
    assert all("NeverStop" not in k and "96聯賽" not in k for k in m)
    # no key maps to itself-as-noise (every canonical is a real target)
    assert all(v and "屆" not in v and "amp;" not in v for v in m.values())


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
