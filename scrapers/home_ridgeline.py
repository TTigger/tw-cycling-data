"""Pick flagship races for the homepage ridgeline from the built benchmarks.
Each race contributes one node: peak height = normalized median finish time."""


def _largest_all(race):
    """The race's biggest distance/event group's `all` cohort (n, median)."""
    best = None
    for g in race.get("groups", {}).values():
        allc = g.get("cohorts", {}).get("all")
        if not allc:
            continue
        if best is None or allc["n"] > best["n"]:
            best = allc
    if best is None:
        return None
    bp = best.get("bp") or []
    median = bp[len(bp) // 2] if bp else 0
    return {"n": best["n"], "median": median}


def select_ridgeline(benchmarks, n=8):
    rows = []
    for race in benchmarks.values():
        a = _largest_all(race)
        if a is None:
            continue
        rows.append({"label": race.get("rn", ""), "median": int(a["median"]), "finishers": int(a["n"])})
    rows.sort(key=lambda r: r["finishers"], reverse=True)
    rows = rows[:n]
    rows.sort(key=lambda r: r["median"])
    meds = [r["median"] for r in rows]
    lo, hi = (min(meds), max(meds)) if meds else (0, 1)
    span = (hi - lo) or 1
    return [{"label": r["label"], "x": i, "y": round((r["median"] - lo) / span, 4),
             "median": r["median"], "finishers": r["finishers"]} for i, r in enumerate(rows)]
