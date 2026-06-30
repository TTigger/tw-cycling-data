from tw_cycling_data_mcp import server


class FakeClient:
    def manifest(self):
        return {"api_version": "v1", "stats": {"records": 10}}

    def athletes_index(self):
        return [{"id": "ff00ff00", "nm": "陳○明", "n": 9, "ny": 4, "best": 1}]

    def races_index(self):
        return [{"rk": "a", "y": 2024, "rn": "東三塔550", "s": "TBA", "file": "a__2024"}]

    def race(self, file_stem):
        return {"file": file_stem, "rows": []}

    def athlete(self, aid):
        return {"id": aid}

    def team(self, tid):
        return {"id": tid}


def test_tool_impls_use_query_and_client():
    c = FakeClient()
    assert server.dataset_overview_impl(c)["stats"]["records"] == 10
    assert server.search_athletes_impl(c, "明", 10)[0]["id"] == "ff00ff00"
    assert server.list_races_impl(c, 2024, None, "塔", 10)[0]["rk"] == "a"
    # get_race 接受 race_key,內部用 races_index 解析 file 後抓明細
    assert server.get_race_impl(c, "a")["file"] == "a__2024"
    assert server.get_athlete_impl(c, "abc")["id"] == "abc"


def test_server_registers_six_tools():
    # FastMCP 實例存在且註冊了預期工具名
    names = server.tool_names()
    assert set(names) == {
        "dataset_overview", "search_athletes", "get_athlete",
        "list_races", "get_race", "get_team",
    }
