# -*- coding: utf-8 -*-
"""Pure query helpers for the MCP server — no HTTP, fully unit-testable.
Mirrors the frontend web/src/lib/athletes.ts search semantics."""
import re

_ID_RE = re.compile(r"^[0-9a-f]{4,}$")


def normalize_search(s):
    """Strip the PDPA mask glyph ○ and whitespace, lowercase — so a query of the
    visible characters matches a masked name (mirrors frontend normalizeSearch)."""
    return re.sub(r"[○\s]", "", s or "").lower()


def match_athletes(index, query, limit=20):
    q = (query or "").strip()
    nq = normalize_search(q)
    id_query = bool(_ID_RE.match(nq))
    if q:
        pool = [a for a in index
                if nq in normalize_search(a.get("nm", ""))
                or (id_query and a.get("id", "").startswith(nq))]
    else:
        pool = list(index)
    pool.sort(key=lambda a: (-(a.get("n") or 0), -(a.get("ny") or 0),
                             a.get("best") if a.get("best") is not None else 9999))
    return pool[:limit]


def filter_races(index, year=None, race_type=None, query=None, limit=50):
    nq = normalize_search(query) if query else None
    out = []
    for r in index:
        if year is not None and r.get("y") != year:
            continue
        if race_type is not None and (r.get("s") or "") != race_type:
            continue
        if nq and nq not in normalize_search(r.get("rn", "")):
            continue
        out.append(r)
    return out[:limit]


def hms_to_seconds(s):
    """Parse 'HH:MM:SS' / 'MM:SS' / plain seconds -> int, or None if unparseable."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        if ":" in s:
            parts = [int(p) for p in s.split(":")]
            if len(parts) == 3:
                h, m, sec = parts
            elif len(parts) == 2:
                h, m, sec = 0, parts[0], parts[1]
            else:
                return None
            return h * 3600 + m * 60 + sec
        return int(s)
    except (TypeError, ValueError):
        return None


def percentile_beaten(seconds, sorted_times):
    """Percent of the cohort strictly slower than `seconds` (ties not counted)."""
    if not sorted_times:
        return 0
    slower = sum(1 for t in sorted_times if t > seconds)
    return round(slower / len(sorted_times) * 100)


def benchmark_lookup(benchmarks, race_key, seconds, result_label=None, age_band=None, gender=None):
    """Pick a distance/event group (given, else the largest by `all` count) then
    the most-specific available cohort (age|gender -> age -> all) within it."""
    race = benchmarks.get(race_key)
    if not race:
        return {"error": f"no benchmark for race_key '{race_key}'"}
    groups = race["groups"]
    if result_label and result_label in groups:
        group_key = result_label
    else:
        group_key = max(groups, key=lambda g: groups[g]["cohorts"].get("all", {}).get("n", 0))
    cohorts = groups[group_key]["cohorts"]
    candidates = []
    if age_band and gender:
        candidates.append(f"age:{age_band}|g:{gender}")
    if age_band:
        candidates.append(f"age:{age_band}")
    candidates.append("all")
    key = next((k for k in candidates if k in cohorts), None)
    if key is None:
        return {"error": f"no usable cohort for race '{race_key}' group '{group_key}'"}
    c = cohorts[key]
    return {"race_key": race_key, "rn": race["rn"], "group": group_key,
            "years": groups[group_key]["years"], "cohort_label": c["label"],
            "cohort_type": c["type"], "n": c["n"],
            "percentile_beat": percentile_beaten(seconds, c["bp"])}
