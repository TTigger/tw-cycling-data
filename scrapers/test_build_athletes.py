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
