import json, os
import home_ridgeline

HERE = os.path.dirname(__file__)
BM = os.path.join(HERE, "..", "web", "public", "data", "v1", "benchmarks.json")
OUT = os.path.join(HERE, "..", "web", "public", "data", "v1", "home_ridgeline.json")


def main():
    with open(BM, encoding="utf-8") as f:
        benchmarks = json.load(f)
    nodes = home_ridgeline.select_ridgeline(benchmarks, n=8)
    payload = {"unit": "median_finish_seconds_normalized", "nodes": nodes}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print(f"home_ridgeline.json: {len(nodes)} nodes")


if __name__ == "__main__":
    main()
