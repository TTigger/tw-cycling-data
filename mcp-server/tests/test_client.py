from tw_cycling_data_mcp.client import ApiClient


def make_client(routes):
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return routes[url]

    return ApiClient(base_url="http://x/data/v1", fetch=fake_fetch), calls


def test_client_builds_urls_and_returns_json():
    routes = {
        "http://x/data/v1/manifest.json": {"api_version": "v1"},
        "http://x/data/v1/races.json": [{"rk": "a", "file": "a__2024"}],
        "http://x/data/v1/race/a__2024.json": {"rows": []},
        "http://x/data/v1/athlete/abc.json": {"id": "abc"},
    }
    client, calls = make_client(routes)
    assert client.manifest()["api_version"] == "v1"
    assert client.races_index()[0]["rk"] == "a"
    assert client.race("a__2024") == {"rows": []}
    assert client.athlete("abc") == {"id": "abc"}
    assert "http://x/data/v1/race/a__2024.json" in calls


def test_client_default_base_is_production():
    from tw_cycling_data_mcp import client
    assert client.DEFAULT_BASE == "https://tw-cycling-data.vercel.app/data/v1"
