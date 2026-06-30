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
