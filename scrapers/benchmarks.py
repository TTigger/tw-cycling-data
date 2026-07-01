# -*- coding: utf-8 -*-
"""Pure helpers for the age/gender benchmark dataset. No I/O — unit-testable.
A cohort is `all`, an age band, an age band x gender, or a race category.
Each cohort stores 101 finish-second breakpoints (the time at each percentile)."""

MIN_COHORT_N = 20


def _age_label(ab):
    return ab if ab.startswith("U") else f"{ab} 歲"


def cohort_keys(row):
    """Return [(key, type, label)] for the cohorts this finisher belongs to."""
    out = [("all", "all", "全部完賽者")]
    ab = row.get("age_band")
    if ab:
        out.append((f"age:{ab}", "age", _age_label(ab)))
        g = row.get("gender")
        if g in ("M", "F"):
            out.append((f"age:{ab}|g:{g}", "age",
                        f"{_age_label(ab)} {'男' if g == 'M' else '女'}"))
    cat = row.get("category_raw")
    if cat:
        out.append((f"cat:{cat}", "cat", cat))
    return out


def percentile_breakpoints(sorted_seconds):
    """101 breakpoints: bp[p] = time at percentile p (0=fastest..100=slowest).
    Input must be ascending. Returns [] for empty input; otherwise length is
    always 101, monotonic non-decreasing."""
    n = len(sorted_seconds)
    if n == 0:
        return []
    return [sorted_seconds[int(round(p / 100 * (n - 1)))] for p in range(101)]


def _is_finisher(row):
    return row.get("status") in (None, "FIN")


def build_index(rows, min_n=MIN_COHORT_N):
    """Group finishers by (race_key, result_label); within each group accumulate
    per-cohort finish seconds; emit only cohorts with n>=min_n. A group is kept
    only if its `all` cohort reaches min_n; a race is kept if it has >=1 group."""
    races = {}   # rk -> {rn, groups: {group: {years:set, cohorts:{key:{type,label,_secs}}}}}
    for r in rows:
        rk = r.get("race_key")
        fs = r.get("finish_seconds")
        if not rk or fs is None or not _is_finisher(r):
            continue
        try:
            fs = int(fs)
        except (TypeError, ValueError):
            continue
        group = r.get("result_label") or "全部"
        race = races.setdefault(rk, {
            "rn": r.get("race_name_canonical") or r.get("race_name_raw") or rk, "groups": {}})
        grp = race["groups"].setdefault(group, {"years": set(), "cohorts": {}})
        if r.get("year") is not None:
            grp["years"].add(r["year"])
        for key, ctype, label in cohort_keys(r):
            c = grp["cohorts"].setdefault(key, {"type": ctype, "label": label, "_secs": []})
            c["_secs"].append(fs)

    out = {}
    for rk, race in races.items():
        groups = {}
        for group, grp in race["groups"].items():
            cohorts = {}
            for key, c in grp["cohorts"].items():
                if len(c["_secs"]) < min_n:
                    continue
                secs = sorted(c["_secs"])
                cohorts[key] = {"n": len(secs), "type": c["type"], "label": c["label"],
                                "bp": percentile_breakpoints(secs)}
            if "all" not in cohorts:            # group too small
                continue
            groups[group] = {"years": sorted(grp["years"]), "cohorts": cohorts}
        if groups:
            out[rk] = {"rn": race["rn"], "groups": groups}
    return out
