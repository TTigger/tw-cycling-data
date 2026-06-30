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


def test_get_race_resolves_latest_year_and_year_param():
    class MultiYear:
        def races_index(self):
            return [
                {"rk": "lianlian197", "y": 2022, "file": "lianlian197__2022"},
                {"rk": "lianlian197", "y": 2024, "file": "lianlian197__2024"},
                {"rk": "lianlian197", "y": 2023, "file": "lianlian197__2023"},
            ]
        def race(self, file_stem):
            return {"file": file_stem}
    c = MultiYear()
    # bare race_key -> latest edition (2024), not index-order first (2022)
    assert server.get_race_impl(c, "lianlian197")["file"] == "lianlian197__2024"
    # year param disambiguates
    assert server.get_race_impl(c, "lianlian197", 2023)["file"] == "lianlian197__2023"
    # a direct file stem is honored as-is
    assert server.get_race_impl(c, "lianlian197__2022")["file"] == "lianlian197__2022"


def test_server_registers_six_tools():
    # FastMCP 實例存在且註冊了預期工具名
    names = server.tool_names()
    assert set(names) == {
        "dataset_overview", "search_athletes", "get_athlete",
        "list_races", "get_race", "get_team",
    }
