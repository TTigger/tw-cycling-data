# -*- coding: utf-8 -*-
"""Build multi-station series standings (Feature 🏆 賽事系列總標).

Reads  data/processed/master.json   (INTERNAL — needs identity grouping)
Writes web/public/data/v1/series.json  (aggregate + masked names — de-identified)

A "series" (96聯賽 / 捷安特自行車嘉年華 / TIS崇越盃 / 臺灣自行車聯賽 …) runs several
stations a season. We give each rider a season total = the sum of their best
in-field percentile ("贏過全場 %") per station, so consistent strong results
across many stations rank highest. This is a COMPOSITE-PERFORMANCE board, not an
official points table (organizer point systems vary and aren't published here).

Only seasons with >=2 distinct stations qualify, and a rider must have raced
>=2 of them to appear (a single-station result isn't a "series" placing).
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402
from build_athletes import build_group_keys, athlete_id, MIN_RESULTS  # noqa: E402

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.json")
OUT = common.PUBLIC_DATA_DIR

MIN_STATIONS = 2
TOP_N = 50


def series_standings(records, group_keys, field_sizes=None, min_stations=MIN_STATIONS, top_n=TOP_N):
    """{series: {name, seasons: {year: {stations:[{rk,name,n}], standings:[...]}}}}.
    Points = sum of best in-field percentile per station. De-identified output."""
    if field_sizes is None:
        field_sizes = Counter((r.get("race_key"), r.get("year")) for r in records)
    gsize = Counter(group_keys)

    stations = defaultdict(dict)                     # (series, year) -> {rk: {name, n}}
    rider = defaultdict(lambda: {"by_rk": {}, "nm": None})  # (series, year, gk) -> ...
    for gk, r in zip(group_keys, records):
        s, y, rk = r.get("series"), r.get("year"), r.get("race_key")
        if not s or y is None or not rk:
            continue
        f = field_sizes.get((rk, y))
        st = stations[(s, y)]
        if rk not in st:
            st[rk] = {"name": r.get("race_name_canonical") or r.get("race_name_raw"), "n": f}
        rank = r.get("rank_overall")
        if gk in ("n:", "u:", "t:") or not rank or not f or f < 1 or rank > f:
            continue
        pct = (f - rank) / f * 100
        d = rider[(s, y, gk)]
        if d["nm"] is None:
            d["nm"] = r.get("name_masked") or common.mask_name(r.get("name_raw"))
        if rk not in d["by_rk"] or pct > d["by_rk"][rk]:
            d["by_rk"][rk] = pct                     # best of a rider's rows in that station

    by_sy = defaultdict(list)
    for (s, y, gk), d in rider.items():
        n = len(d["by_rk"])
        if n < min_stations:
            continue
        by_sy[(s, y)].append((gk, d["nm"], sum(d["by_rk"].values()), n, max(d["by_rk"].values())))

    out = {}
    for (s, y), lst in by_sy.items():
        st = stations[(s, y)]
        if len(st) < min_stations:                   # not a multi-station season
            continue
        lst.sort(key=lambda x: (-x[2], -x[3], athlete_id(x[0])))
        standings = [
            {"id": athlete_id(gk), "nm": nm, "pts": round(pts), "n": n,
             "best": round(best), "link": gsize[gk] >= MIN_RESULTS}
            for gk, nm, pts, n, best in lst[:top_n]
        ]
        d = out.setdefault(s, {"name": s, "seasons": {}})
        d["seasons"][str(y)] = {
            "stations": [{"rk": rk, "name": v["name"], "n": v["n"]}
                         for rk, v in sorted(st.items(), key=lambda kv: -(kv[1]["n"] or 0))],
            "standings": standings,
        }
    return {s: d for s, d in out.items() if d["seasons"]}


def main():
    records = list(common.iter_records(IN))
    keys = build_group_keys(records)
    data = series_standings(records, keys)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "series.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    seasons = sum(len(d["seasons"]) for d in data.values())
    print(f"series={len(data)} ({seasons} season-standings) -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
