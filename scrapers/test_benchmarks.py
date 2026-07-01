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
    # 25 M 40-49 finishers of race R (seconds 3600..) — no result_label → group "全部"
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
    cohorts = idx["R"]["groups"]["全部"]["cohorts"]
    assert "all" in cohorts and cohorts["all"]["n"] == 30
    assert "age:40-49" in cohorts and cohorts["age:40-49"]["n"] == 30
    assert "age:40-49|g:M" in cohorts and cohorts["age:40-49|g:M"]["n"] == 25
    assert "age:40-49|g:F" not in cohorts        # n=5 < 20 dropped
    assert len(cohorts["all"]["bp"]) == 101
    assert idx["R"]["groups"]["全部"]["years"] == [2024, 2025]
    assert idx["R"]["rn"] == "賽事R"


def test_build_index_excludes_non_finishers():
    rows = [{"race_key": "R", "year": 2024, "age_band": None, "gender": None,
             "category_raw": None, "finish_seconds": 3600 + i,
             "race_name_canonical": "賽事R",
             "status": ("DNF" if i % 5 == 0 else "FIN")} for i in range(25)]
    idx = B.build_index(rows, min_n=20)
    # 5 DNF excluded -> 20 finishers remain (still meets min_n)
    assert idx["R"]["groups"]["全部"]["cohorts"]["all"]["n"] == 20


def test_build_index_drops_race_without_enough_finishers():
    rows = [{"race_key": "TINY", "year": 2024, "age_band": None, "gender": None,
             "category_raw": None, "finish_seconds": 3600, "race_name_canonical": "小賽",
             "status": None}]
    assert "TINY" not in B.build_index(rows, min_n=20)


def test_build_index_nests_by_result_label_group():
    rows = []
    for i in range(25):   # group "130K" — 25 finishers
        rows.append({"race_key": "R", "year": 2024, "age_band": "40-49", "gender": "M",
                     "category_raw": "M40", "finish_seconds": 3600 + i, "result_label": "130K",
                     "race_name_canonical": "賽事R", "status": None})
    for i in range(22):   # group "50K" — 22 finishers
        rows.append({"race_key": "R", "year": 2024, "age_band": "30-39", "gender": "M",
                     "category_raw": "M30", "finish_seconds": 1800 + i, "result_label": "50K",
                     "race_name_canonical": "賽事R", "status": None})
    idx = B.build_index(rows, min_n=20)
    assert set(idx["R"]["groups"]) == {"130K", "50K"}
    g130 = idx["R"]["groups"]["130K"]
    assert g130["cohorts"]["all"]["n"] == 25 and len(g130["cohorts"]["all"]["bp"]) == 101
    # each group's `all` uses ONLY that group's times (not blended)
    assert g130["cohorts"]["all"]["bp"][0] == 3600
    assert idx["R"]["groups"]["50K"]["cohorts"]["all"]["bp"][0] == 1800
    assert idx["R"]["rn"] == "賽事R"


def test_build_index_drops_group_without_enough_finishers():
    rows = [{"race_key": "R", "year": 2024, "age_band": None, "gender": None,
             "category_raw": None, "finish_seconds": 3600, "result_label": "tiny",
             "race_name_canonical": "賽事R", "status": None}]
    assert "R" not in B.build_index(rows, min_n=20)  # only 1 finisher in the only group


def test_build_index_keeps_race_when_one_group_qualifies():
    # one group meets n>=20, a sibling group does not -> race kept, only the
    # qualifying group appears (final-review coverage gap).
    rows = [{"race_key": "R", "year": 2024, "age_band": None, "gender": None,
             "category_raw": None, "finish_seconds": 3600 + i, "result_label": "big",
             "race_name_canonical": "賽事R", "status": None} for i in range(25)]
    rows += [{"race_key": "R", "year": 2024, "age_band": None, "gender": None,
              "category_raw": None, "finish_seconds": 1800 + i, "result_label": "small",
              "race_name_canonical": "賽事R", "status": None} for i in range(5)]
    idx = B.build_index(rows, min_n=20)
    assert set(idx["R"]["groups"]) == {"big"}
