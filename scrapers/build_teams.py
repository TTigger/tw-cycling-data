# -*- coding: utf-8 -*-
"""Build per-team rosters & records (Feature 🚴 車隊頁).

Reads  data/processed/master.json      (INTERNAL — name_raw for identity grouping)
Writes web/public/data/teams.json      (lean team index — de-identified)
       web/public/data/team/<id>.json  (per-team roster + record — de-identified)

A "team" is the free-text team field on a result row (coverage ~46%). We group
its rows by the SAME rider identity as build_athletes (tsu/UCI/name), so a team's
roster is distinct riders, and each links back to their athlete page. Only real
squads qualify: a team needs >=MIN_TEAM_RIDERS distinct trackable riders, and the
obvious non-teams (個人 / 無 …) are dropped.

PDPA: output carries only masked names + salted athlete ids, never name_raw.
"""
import hashlib
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

_SALT = "twcd-team-v1"
MIN_TEAM_RIDERS = 4          # fewer distinct riders than this isn't really a "team"
MIN_TEAM_RACES = 2           # a real squad races >1 event; a 1-race "team" with a huge
                             # roster is an event-assigned color group (自信寶藍隊…), not a team
TOP_HIGHLIGHTS = 10          # best results to feature on the team page
# free-text values that mean "no team" rather than a squad name
NOISE = {"個人", "個人組", "無", "無車隊", "自由", "自由車", "-", "--", "—", "N/A", "NA"}


def team_id(name):
    """Stable, salted 10-hex id for a team name (filename-safe; not reversible PII,
    but hashed anyway so ids match the rest of the data model)."""
    return hashlib.sha1((_SALT + "|" + name).encode("utf-8")).hexdigest()[:10]


def _clean_team(t):
    if not t:
        return None
    t = t.strip()
    return None if not t or t in NOISE else t


def build_teams(records, group_keys, field_sizes=None, min_riders=MIN_TEAM_RIDERS,
                min_races=MIN_TEAM_RACES, top_highlights=TOP_HIGHLIGHTS):
    """Return (index, details). index: lean team list; details: id -> roster+record.
    Both fully de-identified."""
    if field_sizes is None:
        field_sizes = Counter((r.get("race_key"), r.get("year")) for r in records)
    gsize = Counter(group_keys)

    # team -> rider_key -> aggregate, plus team-level row stats
    rider = defaultdict(lambda: defaultdict(
        lambda: {"nm": None, "n": 0, "best": None, "years": set()}))
    by_year = defaultdict(lambda: defaultdict(lambda: {"riders": set(), "races": set()}))
    rows = defaultdict(list)        # team -> all (de-id-able) result rows for stats/highlights

    for gk, r in zip(group_keys, records):
        t = _clean_team(r.get("team"))
        if not t or gk in ("n:", "u:", "t:"):
            continue
        rank, y, rk = r.get("rank_overall"), r.get("year"), r.get("race_key")
        nm = r.get("name_masked") or common.mask_name(r.get("name_raw"))
        d = rider[t][gk]
        if d["nm"] is None:
            d["nm"] = nm
        d["n"] += 1
        if rank and (d["best"] is None or rank < d["best"]):
            d["best"] = rank
        if y:
            d["years"].add(y)
            by_year[t][y]["riders"].add(gk)
            if rk:
                by_year[t][y]["races"].add(rk)
        f = field_sizes.get((rk, y))
        pct = (f - rank) / f * 100 if (rank and f and f >= 1 and rank <= f) else None
        rows[t].append({"gk": gk, "nm": nm, "rn": r.get("race_name_canonical"),
                        "rk": rk, "y": y, "rank": rank, "pct": pct})

    index, details = [], {}
    for t, riders in rider.items():
        if len(riders) < min_riders:
            continue
        tid = team_id(t)
        rl = rows[t]
        races = {x["rk"] for x in rl if x["rk"]}
        if len(races) < min_races:
            continue
        ranks = [x["rank"] for x in rl if x["rank"]]
        years = sorted(by_year[t].keys())
        wins = sum(1 for x in rl if x["rank"] == 1)
        podiums = sum(1 for x in rl if x["rank"] and x["rank"] <= 3)

        roster = sorted(
            ({"id": athlete_id(gk), "nm": d["nm"], "link": gsize[gk] >= MIN_RESULTS,
              "n": d["n"], "best": d["best"],
              "y0": min(d["years"]) if d["years"] else None,
              "y1": max(d["years"]) if d["years"] else None}
             for gk, d in riders.items()),
            key=lambda x: (-x["n"], x["best"] or 9999, x["id"]))

        highlights = sorted((x for x in rl if x["pct"] is not None),
                            key=lambda x: -x["pct"])[:top_highlights]
        highlights = [{"id": athlete_id(x["gk"]), "nm": x["nm"], "rn": x["rn"],
                       "rk": x["rk"], "y": x["y"], "rank": x["rank"],
                       "pct": round(x["pct"])} for x in highlights]

        details[tid] = {
            "id": tid, "name": t, "riders": len(roster), "rows": len(rl),
            "races": len(races), "wins": wins, "podiums": podiums,
            "best": min(ranks) if ranks else None,
            "y0": years[0] if years else None, "y1": years[-1] if years else None,
            "byYear": [{"y": y, "riders": len(by_year[t][y]["riders"]),
                        "races": len(by_year[t][y]["races"])} for y in years],
            "roster": roster, "highlights": highlights,
        }
        index.append({"id": tid, "name": t, "riders": len(roster),
                      "races": len(races), "wins": wins, "podiums": podiums,
                      "y0": years[0] if years else None, "y1": years[-1] if years else None})

    index.sort(key=lambda a: (-a["riders"], -a["races"], a["id"]))
    return index, details


def main():
    records = list(common.iter_records(IN))
    keys = build_group_keys(records)
    index, details = build_teams(records, keys)
    os.makedirs(os.path.join(OUT, "team"), exist_ok=True)
    with open(os.path.join(OUT, "teams.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    for tid, d in details.items():
        with open(os.path.join(OUT, "team", f"{tid}.json"), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    print(f"teams={len(index)} detailFiles={len(details)} -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
