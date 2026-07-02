import home_ridgeline as H


def _bm():
    # {race_key: {rn, groups: {g: {cohorts: {all: {n, bp}}}}}}
    def race(rn, n, median):
        bp = list(range(median - 50, median + 51))  # 101 pts, bp[50] == median
        return {"rn": rn, "groups": {"A": {"years": [2024], "cohorts": {"all": {"n": n, "bp": bp}}}}}
    return {
        "r1": race("小賽", 30, 3600),
        "r2": race("大賽", 500, 9000),
        "r3": race("中賽", 120, 6000),
    }


def test_select_ridgeline_picks_top_by_finishers_and_sorts_by_median():
    nodes = H.select_ridgeline(_bm(), n=2)
    # top-2 by finishers = 大賽(500), 中賽(120); sorted by median ascending
    assert [nd["label"] for nd in nodes] == ["中賽", "大賽"]
    assert [nd["x"] for nd in nodes] == [0, 1]
    assert nodes[0]["median"] == 6000 and nodes[1]["median"] == 9000
    # y normalized 0..1 across the selected set (min->0, max->1)
    assert nodes[0]["y"] == 0.0 and nodes[1]["y"] == 1.0


def test_select_ridgeline_single_race_y_is_zero_no_div_by_zero():
    nodes = H.select_ridgeline({"r": {"rn": "唯一", "groups": {"A": {"cohorts": {"all": {"n": 40, "bp": [100]*101}}}}}}, n=8)
    assert len(nodes) == 1 and nodes[0]["y"] == 0.0


def test_clean_label_strips_junk_and_trailing_years():
    assert H.clean_label(".11.18 TBA北高360認證成績表 2023") == "TBA北高360認證成績表"
    assert H.clean_label("北高360認證式挑戰 2024/2025") == "北高360認證式挑戰"
    assert H.clean_label("彰化經典百K") == "彰化經典百K"
    assert H.clean_label("2023") == "2023"  # cleaning would empty it -> falls back


def test_select_ridgeline_dedupes_race_families_keep_largest():
    def race(rn, n, median):
        bp = list(range(median - 50, median + 51))
        return {"rn": rn, "groups": {"A": {"years": [2024], "cohorts": {"all": {"n": n, "bp": bp}}}}}
    bm = {
        "r1": race("北高360 2023", 2883, 60000),
        "r2": race("北高 2024", 2894, 61000),
        "r3": race(".11.18 TBA北高360認證成績表 2023", 2513, 60700),
        "r4": race("武嶺挑戰", 500, 15000),
    }
    nodes = H.select_ridgeline(bm, n=8)
    labels = [nd["label"] for nd in nodes]
    # only the largest 北高 variant survives (r2, n=2894), label cleaned
    assert labels.count("北高") == 1
    assert sum(1 for l in labels if "北高" in l) == 1
    assert "武嶺挑戰" in labels
    assert len(nodes) == 2


def test_clean_label_strips_leading_year_particle():
    assert H.clean_label("年 NeverStop永不放棄 紫南宮一騎來發財 環縣自行車 99.9K") \
        == "NeverStop永不放棄 紫南宮一騎來發財 環縣自行車 99.9K"
    assert H.clean_label("2024年 環花東") == "環花東"
