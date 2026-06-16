# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import build_athletes as ba


def _rec(name, uci=None, tsu=None, team=None, year=2024, rk="alpha", rn="Alpha", rank=1,
         t=3600.0, cat="M30", g="M", ag="30", label="總排名", date=None):
    return {"name_raw": name, "name_masked": None, "uci_id": uci, "tsu_rider_id": tsu,
            "team": team, "year": year, "race_key": rk, "race_name_canonical": rn,
            "rank_overall": rank, "finish_seconds": t, "category_raw": cat,
            "gender": g, "age_group": ag, "result_label": label,
            "date": date or f"{year}-05-01"}


def test_athlete_id_stable_and_salted():
    a = ba.athlete_id("u:12345")
    b = ba.athlete_id("u:12345")
    assert a == b and len(a) == 10
    # different inputs -> different ids; not a bare sha1 of the raw value
    assert ba.athlete_id("n:王小明") != ba.athlete_id("n:王大明")


def test_group_key_uci_anchors_name():
    # same person: UCI in one race, none (but same name) in another -> one group
    recs = [_rec("王大明", uci="10012345678", team="A", year=2023),
            _rec("王大明", uci=None, team="A", year=2024)]
    gk = ba.build_group_keys(recs)
    assert gk[0] == gk[1]
    assert gk[0].startswith("u:")


def test_group_key_distinct_names_separate():
    recs = [_rec("李四", team="A"), _rec("張三", team="B")]
    gk = ba.build_group_keys(recs)
    assert gk[0] != gk[1]


def test_confidence():
    assert ba.confidence(is_anchored=True, distinct_teams=9, name_len=2) == "high"
    assert ba.confidence(is_anchored=False, distinct_teams=1, name_len=3) == "high"
    assert ba.confidence(is_anchored=False, distinct_teams=3, name_len=3) == "med"
    assert ba.confidence(is_anchored=False, distinct_teams=6, name_len=3) == "low"
    # short common name with several teams is downgraded
    assert ba.confidence(is_anchored=False, distinct_teams=3, name_len=2) == "low"


def test_head_to_head_record():
    recs = []

    def add(name, tsu, rk, rank):
        recs.append({"name_raw": name, "name_masked": None, "tsu_rider_id": tsu,
                     "uci_id": None, "race_key": rk, "year": 2024, "rank_overall": rank,
                     "gender": "M", "finish_seconds": 3600.0 + rank})
    # 甲 beats 乙 in r1, r2; 乙 beats 甲 in r3
    for rk, (ra, rb) in {"r1": (1, 2), "r2": (1, 2), "r3": (2, 1)}.items():
        add("甲", "TCU-a", rk, ra)
        add("乙", "TCU-b", rk, rb)
    aid_a, aid_b = ba.athlete_id("t:TCU-a"), ba.athlete_id("t:TCU-b")
    details = {aid_a: {"nm": "甲"}, aid_b: {"nm": "乙"}}
    out = ba.build_head_to_head(recs, details, min_results=2, min_meets=2)
    assert out[aid_a][0]["nm"] == "乙"
    assert out[aid_a][0]["w"] == 2 and out[aid_a][0]["l"] == 1 and out[aid_a][0]["meets"] == 3
    assert out[aid_b][0]["w"] == 1 and out[aid_b][0]["l"] == 2  # mirror


def test_traits_per_discipline():
    fs = {("climbR", 2024): 100, ("roadR", 2024): 100}
    recs = [
        {"race_key": "climbR", "race_name_canonical": "武嶺盃", "year": 2024,
         "rank_overall": 5, "category_raw": None},     # climb, pct 95
        {"race_key": "climbR", "race_name_canonical": "武嶺盃", "year": 2024,
         "rank_overall": 15, "category_raw": None},    # climb, pct 85
        {"race_key": "roadR", "race_name_canonical": "戀戀197", "year": 2024,
         "rank_overall": 60, "category_raw": None},    # road, pct 40
        {"race_key": "roadR", "race_name_canonical": "戀戀197", "year": 2024,
         "rank_overall": 80, "category_raw": None},    # road, pct 20 -> only 1? need 2
    ]
    tr = ba._traits(recs, fs)
    assert tr["climb"]["pct"] == 90.0 and tr["climb"]["n"] == 2   # median(95,85)
    assert tr["road"]["pct"] == 30.0 and tr["road"]["n"] == 2     # median(40,20)


def test_tsu_rider_id_anchors_over_name():
    # same tsu rider id across two different masked-name spellings -> one athlete
    recs = [_rec("王大明", tsu="TCU-abc", year=2023, rk="r1", rank=3),
            _rec("王大铭", tsu="TCU-abc", year=2024, rk="r2", rank=1)]
    gk = ba.build_group_keys(recs)
    assert gk[0] == gk[1] and gk[0] == "t:TCU-abc"
    index, details = ba.build_athletes(recs)
    assert len(index) == 1 and index[0]["rid"] is True
    assert details[index[0]["id"]]["has_rider"] is True


def test_build_athletes_filters_singletons():
    recs = [
        _rec("王大明", team="A", year=2023, rk="r1", rank=3),
        _rec("王大明", team="A", year=2024, rk="r2", rank=1),
        _rec("一次郎", team="B", year=2024, rk="r1", rank=9),  # only one result
    ]
    index, details = ba.build_athletes(recs)
    names = {a["nm"] for a in index}
    assert "王○明" in names           # head+tail masking applied
    assert all(a["n"] >= 2 for a in index)
    assert "一" not in "".join(names)  # singleton excluded from index
    # every index entry has a matching detail file keyed by id
    for a in index:
        assert a["id"] in details
        d = details[a["id"]]
        assert d["id"] == a["id"]
        assert len(d["history"]) == a["n"]
        assert "name_raw" not in d and "uci_id" not in d  # de-identified


def test_history_sorted_and_deidentified():
    recs = [
        _rec("王大明", team="A", year=2024, rk="r2", rank=1, date="2024-09-01"),
        _rec("王大明", team="A", year=2023, rk="r1", rank=3, date="2023-05-01"),
    ]
    _, details = ba.build_athletes(recs)
    d = next(iter(details.values()))
    years = [h["y"] for h in d["history"]]
    assert years == sorted(years)  # chronological
    assert all("name" not in h for h in d["history"])
    assert d["has_uci"] is False


def test_vam_helpers():
    assert ba._vam(3275, 3600 * 4) == 819
    assert ba._vam(2900, 0) is None
    assert ba._wkg(1500, 5) == 6.0
    assert ba._plausible(1200) and not ba._plausible(50) and not ba._plausible(5000)


def test_build_climb_vam_best_per_athlete():
    profiles = {"climbA": {"name": "Climb A", "elev_m": 3000, "grade": 6.0, "conf": "high"}}
    # one athlete, two climbA results: faster time -> higher VAM is the one kept
    recs = [
        _rec("王大明", tsu="TCU-x", rk="climbA", year=2023, t=3600 * 3),   # 1000 VAM
        _rec("王大明", tsu="TCU-x", rk="climbA", year=2024, t=3600 * 2.5), # 1200 VAM (best)
        _rec("王大明", tsu="TCU-x", rk="other", year=2024, t=3600),         # not a climb
    ]
    rows = ba.build_climb_vam(recs, profiles)
    assert len(rows) == 1
    e = rows[0]
    assert e["best_vam"] == 1200 and e["y"] == 2024 and e["climb"] == "Climb A"
    assert e["conf"] == "high" and e["g"] == "M" and e["best_wkg"] is not None
    assert "id" in e and e["nm"] == "王○明"  # de-identified


def test_feature_raw_medians_by_class():
    # field=100 for every (rk, year) so pct = 100 - rank
    fs = {("climbR", 2024): 100, ("roadR", 2024): 100, ("ttR", 2024): 100}
    recs = [
        {"race_key": "climbR", "race_name_canonical": "武嶺盃", "year": 2024,
         "rank_overall": 5, "category_raw": None},                 # climb pct 95
        {"race_key": "climbR", "race_name_canonical": "武嶺盃", "year": 2024,
         "rank_overall": 15, "category_raw": None},                # climb pct 85
        {"race_key": "roadR", "race_name_canonical": "戀戀197", "year": 2024,
         "rank_overall": 60, "category_raw": None},                # flat (road) pct 40
        {"race_key": "ttR", "race_name_canonical": "個人計時賽", "year": 2024,
         "rank_overall": 10, "category_raw": None},                # tt pct 90
    ]
    raw = ba._feature_raw(recs, fs)
    assert raw["n"] == 4
    assert raw["overall"] == 87.5            # median(95,85,40,90)
    assert raw["climb"] == 90.0             # median(95,85)
    assert raw["flat"] == 40.0             # single road sample
    assert raw["tt"] == 90.0
    # too few in-field samples -> None
    assert ba._feature_raw(recs[:1], fs) is None


def test_age_mid_from_band():
    recs = [{"age_band": "30-39"}, {"age_band": "30-39"}, {"age_band": "40-49"}]
    assert ba._age_mid(recs) == 34
    assert ba._age_mid([{"age_band": "MASTER"}, {"age_band": None}]) is None


def test_standardize_imputes_missing_discipline_and_age():
    # 3 athletes; C has no climb/tt -> those z must equal C's overall z; age missing -> 0
    raws = [
        {"overall": 90.0, "climb": 95.0, "flat": 50.0, "tt": None, "age": 34},
        {"overall": 70.0, "climb": 50.0, "flat": 95.0, "tt": None, "age": 44},
        {"overall": 30.0, "climb": None, "flat": 30.0, "tt": None, "age": None},
    ]
    vecs = ba._standardize(raws)
    # vector order: [climb_z, flat_z, tt_z, overall_z, age_z]
    assert len(vecs) == 3 and all(len(v) == 5 for v in vecs)
    # overall z-scores sum to ~0 (standardized about the mean)
    assert abs(sum(v[3] for v in vecs)) < 1e-6
    # athlete C: missing climb -> climb_z == overall_z; missing tt -> tt_z == overall_z
    assert vecs[2][0] == vecs[2][3]
    assert vecs[2][2] == vecs[2][3]
    # all tt missing -> column imputed to each one's overall_z
    assert [v[2] for v in vecs] == [v[3] for v in vecs]
    # C age missing -> 0
    assert vecs[2][4] == 0.0
    # stronger overall -> higher overall_z
    assert vecs[0][3] > vecs[1][3] > vecs[2][3]


def test_build_features_per_gender_and_eligibility():
    fs = {("r1", 2024): 100, ("r2", 2024): 100, ("r3", 2024): 100}
    recs = [
        # M athlete A: climb-strong (anchored by tsu id)
        _rec("男甲", tsu="A", rk="r1", rn="武嶺盃", rank=5, g="M", year=2024, ag=None),
        _rec("男甲", tsu="A", rk="r2", rn="戀戀197", rank=50, g="M", year=2024, ag=None),
        # M athlete B: flat-strong
        _rec("男乙", tsu="B", rk="r1", rn="武嶺盃", rank=50, g="M", year=2024, ag=None),
        _rec("男乙", tsu="B", rk="r2", rn="戀戀197", rank=5, g="M", year=2024, ag=None),
        # F athlete C: standardized in its own (F) pool
        _rec("女丙", tsu="C", rk="r1", rn="武嶺盃", rank=20, g="F", year=2024, ag=None),
        _rec("女丙", tsu="C", rk="r2", rn="戀戀197", rank=30, g="F", year=2024, ag=None),
        # gender-unknown D: excluded
        _rec("無名", tsu="D", rk="r1", rn="武嶺盃", rank=10, g=None, year=2024, ag=None),
        _rec("無名", tsu="D", rk="r2", rn="戀戀197", rank=10, g=None, year=2024, ag=None),
    ]
    # inject age_band on A's recs only
    for r in recs[:2]:
        r["age_band"] = "30-39"
    out = ba.build_features(recs, field_sizes=fs)
    by_id = {e["id"]: e for e in out}
    aid_a, aid_b = ba.athlete_id("t:A"), ba.athlete_id("t:B")
    aid_c, aid_d = ba.athlete_id("t:C"), ba.athlete_id("t:D")
    assert aid_d not in by_id                       # unknown gender excluded
    assert by_id[aid_a]["g"] == "M" and by_id[aid_c]["g"] == "F"
    # A is climb>flat, B is flat>climb (climb_z vs flat_z)
    assert by_id[aid_a]["v"][0] > by_id[aid_a]["v"][1]
    assert by_id[aid_b]["v"][0] < by_id[aid_b]["v"][1]
    # C alone in F pool -> all z = 0
    assert by_id[aid_c]["v"] == [0.0, 0.0, 0.0, 0.0, 0.0]


def test_build_course_records_alltime_fastest():
    profiles = {"wuling": {"name": "武嶺", "dist_km": 50.0, "elev_m": 3000, "grade": 6.0, "conf": "high"}}
    recs = [
        _rec("選手A", tsu="A1", year=2022, rk="wuling", t=7200.0),   # VAM 1500
        _rec("選手A", tsu="A1", year=2023, rk="wuling", t=6000.0),   # VAM 1800 — A's best
        _rec("選手B", tsu="B1", year=2022, rk="wuling", t=8000.0),   # B's best
        _rec("選手B", tsu="B1", year=2023, rk="wuling", t=9000.0),
        _rec("選手A", tsu="A1", year=2023, rk="other", t=100.0),     # non-profiled → ignored
    ]
    out = ba.build_course_records(recs, profiles)
    assert set(out) == {"wuling"}
    board = out["wuling"]
    assert board["name"] == "武嶺" and board["n"] == 2
    rows = board["records"]
    # deduped to each rider's fastest ascent, ranked by time
    assert [r["t"] for r in rows] == [6000, 8000]
    assert rows[0]["rank"] == 1 and rows[0]["vam"] == ba._vam(3000, 6000)  # record holder = A
    assert rows[1]["rank"] == 2
    assert rows[0]["link"] is True   # ≥2 results → trackable/linkable
