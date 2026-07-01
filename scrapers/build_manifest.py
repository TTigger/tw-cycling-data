# -*- coding: utf-8 -*-
"""Generate /data/v1/manifest.json: api version, dataset stats (derived from
build products, never hard-coded), and the endpoint catalog. Run AFTER the
other build_* scripts so the index files exist."""
import json
import os
import common

ENDPOINTS = [
    {"path": "manifest.json", "kind": "meta", "description": "This file: version, stats, endpoint catalog."},
    {"path": "overview.json", "kind": "meta", "description": "Dataset KPIs, heatmap, trend, gender composition."},
    {"path": "races.json", "kind": "index", "description": "Race index: race_key, year, name, series, finisher rows."},
    {"path": "race/{race_key}.json", "kind": "detail", "description": "One race leaderboard (re-ranked by category + finish time)."},
    {"path": "athletes.json", "kind": "index", "description": "Athlete index (>=2 results): masked name, team, counts."},
    {"path": "athlete/{athlete_id}.json", "kind": "detail", "description": "One athlete's de-identified result history."},
    {"path": "teams.json", "kind": "index", "description": "Team index: id, name, roster size."},
    {"path": "team/{team_id}.json", "kind": "detail", "description": "One team's roster + record."},
    {"path": "series.json", "kind": "index", "description": "Race series aggregates."},
    {"path": "benchmarks.json", "kind": "index", "description": "Per-race finish-time percentile breakpoints, grouped by distance/event (result_label) then age/gender/category cohort."},
    {"path": "coverage.json", "kind": "meta", "description": "Source/calendar coverage and gap triage."},
]


def _read_json(data_dir, name):
    with open(os.path.join(data_dir, name), encoding="utf-8") as f:
        return json.load(f)


def compute_manifest(data_dir):
    kpi = _read_json(data_dir, "overview.json")["kpi"]
    races = _read_json(data_dir, "races.json")
    athletes = _read_json(data_dir, "athletes.json")
    teams = _read_json(data_dir, "teams.json")
    return {
        "api_version": "v1",
        "dataset": "tw-cycling-data",
        "homepage": "https://tw-cycling-data.vercel.app/",
        "license": "CC-BY-4.0",
        "attribution": "tw-cycling-data (https://github.com/TTigger/tw-cycling-data)",
        "stats": {
            "records": kpi["records"],
            "races": kpi["races"],            # distinct races (matches overview kpi)
            "race_editions": len(races),      # per-year editions (= len races.json)
            "series": kpi.get("series"),
            "athletes": len(athletes),
            "teams": len(teams),
            "sources": kpi.get("sources"),
            "year_min": kpi["minYear"],
            "year_max": kpi["maxYear"],
        },
        "endpoints": ENDPOINTS,
    }


def main():
    m = compute_manifest(common.PUBLIC_DATA_DIR)
    out = os.path.join(common.PUBLIC_DATA_DIR, "manifest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print(f"manifest: records={m['stats']['records']} races={m['stats']['races']} "
          f"athletes={m['stats']['athletes']} -> {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
