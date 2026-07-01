from tw_cycling_data_mcp import query


def test_normalize_strips_mask_and_whitespace_lowercases():
    assert query.normalize_search("林○宇") == "林宇"
    assert query.normalize_search("  AB cd ") == "abcd"


def test_match_athletes_by_visible_name_and_id_prefix():
    idx = [
        {"id": "1a2b3c4d", "nm": "林○宇", "n": 5, "ny": 3, "best": 2},
        {"id": "ff00ff00", "nm": "陳○明", "n": 9, "ny": 4, "best": 1},
    ]
    # 可見字「宇」要命中 林○宇
    out = query.match_athletes(idx, "宇", limit=10)
    assert [a["id"] for a in out] == ["1a2b3c4d"]
    # 16 進位 query 命中 id 前綴
    out = query.match_athletes(idx, "ff00", limit=10)
    assert [a["id"] for a in out] == ["ff00ff00"]
    # 空 query 依 n desc 排序回前 N
    out = query.match_athletes(idx, "", limit=1)
    assert out[0]["id"] == "ff00ff00"


def test_filter_races_by_year_and_query():
    idx = [
        {"rk": "a", "y": 2024, "rn": "東三塔550", "s": "TBA"},
        {"rk": "b", "y": 2025, "rn": "北高360", "s": "TBA"},
        {"rk": "c", "y": 2024, "rn": "苗栗繞圈賽", "s": None},
    ]
    assert {r["rk"] for r in query.filter_races(idx, 2024, None, None)} == {"a", "c"}
    assert [r["rk"] for r in query.filter_races(idx, None, None, "塔")] == ["a"]
    assert query.filter_races(idx, 2024, None, None, limit=1).__len__() == 1


def test_hms_to_seconds():
    assert query.hms_to_seconds("01:00:00") == 3600
    assert query.hms_to_seconds("10:30") == 630
    assert query.hms_to_seconds("90") == 90
    assert query.hms_to_seconds("nope") is None


def test_percentile_beaten_counts_strictly_slower():
    bp = [60, 70, 80, 90, 100]
    assert query.percentile_beaten(65, bp) == 80   # 4 of 5 slower
    assert query.percentile_beaten(60, bp) == 80   # tie not counted (4 strictly slower)
    assert query.percentile_beaten(50, bp) == 100  # faster than all
    assert query.percentile_beaten(100, bp) == 0   # slower than/equal all


def test_benchmark_lookup_group_and_cohort_fallback():
    bm = {"R": {"rn": "賽事R", "groups": {
        "130K": {"years": [2024], "cohorts": {
            "all": {"n": 100, "type": "all", "label": "全部完賽者", "bp": [60, 70, 80, 90, 100]},
            "age:40-49": {"n": 60, "type": "age", "label": "40-49 歲", "bp": [50, 60, 70, 80, 90]}}},
        "50K": {"years": [2024], "cohorts": {
            "all": {"n": 40, "type": "all", "label": "全部完賽者", "bp": [30, 40, 50, 60, 70]}}}}}}
    # explicit group + cohort
    r = query.benchmark_lookup(bm, "R", 55, result_label="130K", age_band="40-49")
    assert r["group"] == "130K" and r["cohort_label"] == "40-49 歲" and r["n"] == 60
    # no group given -> default largest (130K, all.n=100)
    r2 = query.benchmark_lookup(bm, "R", 75)
    assert r2["group"] == "130K" and r2["cohort_label"] == "全部完賽者"
    # explicit smaller group
    r3 = query.benchmark_lookup(bm, "R", 45, result_label="50K")
    assert r3["group"] == "50K" and r3["percentile_beat"] == 60
    # unknown race
    assert "error" in query.benchmark_lookup(bm, "NOPE", 75)
