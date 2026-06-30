import benchmarks as B


def test_percentile_breakpoints_length_and_monotonic():
    bp = B.percentile_breakpoints(list(range(1, 101)))  # 100 values 1..100
    assert len(bp) == 101
    assert bp == sorted(bp)                # monotonic non-decreasing
    assert bp[0] == 1 and bp[100] == 100   # fastest / slowest
    # single-value cohort -> all breakpoints equal
    assert B.percentile_breakpoints([42]) == [42] * 101


def test_cohort_keys_age_gender_cat_and_missing():
    row = {"age_band": "40-49", "gender": "M", "category_raw": "M / M40"}
    keys = {k for (k, _t, _l) in B.cohort_keys(row)}
    assert keys == {"all", "age:40-49", "age:40-49|g:M", "cat:M / M40"}
    # missing age/gender -> only all + cat
    row2 = {"age_band": None, "gender": None, "category_raw": "菁英組"}
    keys2 = {k for (k, _t, _l) in B.cohort_keys(row2)}
    assert keys2 == {"all", "cat:菁英組"}
    # types tagged correctly
    types = {k: t for (k, t, _l) in B.cohort_keys(row)}
    assert types["all"] == "all" and types["age:40-49"] == "age" and types["cat:M / M40"] == "cat"


def test_build_index_filters_small_cohorts_and_shapes_output():
    rows = []
    # 25 M 40-49 finishers of race R (seconds 3600..)
    for i in range(25):
        rows.append({"race_key": "R", "year": 2024, "age_band": "40-49", "gender": "M",
                     "category_raw": "M40", "finish_seconds": 3600 + i,
                     "race_name_canonical": "賽事R", "status": None})
    # 5 F finishers -> age:40-49|g:F has n=5 -> dropped; but they still count toward all + age:40-49
    for i in range(5):
        rows.append({"race_key": "R", "year": 2025, "age_band": "40-49", "gender": "F",
                     "category_raw": "F40", "finish_seconds": 4000 + i,
                     "race_name_canonical": "賽事R", "status": None})
    idx = B.build_index(rows, min_n=20)
    assert "R" in idx
    cohorts = idx["R"]["cohorts"]
    assert "all" in cohorts and cohorts["all"]["n"] == 30
    assert "age:40-49" in cohorts and cohorts["age:40-49"]["n"] == 30
    assert "age:40-49|g:M" in cohorts and cohorts["age:40-49|g:M"]["n"] == 25
    assert "age:40-49|g:F" not in cohorts        # n=5 < 20 dropped
    assert len(cohorts["all"]["bp"]) == 101
    assert idx["R"]["years"] == [2024, 2025]
    assert idx["R"]["rn"] == "賽事R"


def test_build_index_drops_race_without_enough_finishers():
    rows = [{"race_key": "TINY", "year": 2024, "age_band": None, "gender": None,
             "category_raw": None, "finish_seconds": 3600, "race_name_canonical": "小賽",
             "status": None}]
    assert "TINY" not in B.build_index(rows, min_n=20)
