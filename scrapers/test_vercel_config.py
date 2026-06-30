import json
import os

VERCEL = os.path.join(os.path.dirname(__file__), "..", "web", "vercel.json")


def test_vercel_sets_cors_and_cache_for_data():
    with open(VERCEL, encoding="utf-8") as f:
        cfg = json.load(f)
    headers = cfg["headers"]
    # 找到對 /data/ 路徑的設定
    data_rule = next(h for h in headers if "/data/" in h["source"])
    kv = {x["key"]: x["value"] for x in data_rule["headers"]}
    assert kv["Access-Control-Allow-Origin"] == "*"
    assert "max-age" in kv["Cache-Control"]
