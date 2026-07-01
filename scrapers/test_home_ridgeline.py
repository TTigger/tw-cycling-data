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
