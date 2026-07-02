"""Pick flagship races for the homepage ridgeline from the built benchmarks.
Each race contributes one node: peak height = normalized median finish time.
Upstream race names (rn) can be messy (leading date fragments, trailing years)
and one race family can appear under several race_keys (北高360 variants), so
labels are cleaned and families deduped before the top-N cut."""
import re


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


def clean_label(rn):
    """Hero-friendly label: drop leading punctuation/date junk and trailing
    year tokens. Falls back to the raw name if cleaning empties it."""
    s = (rn or "").strip()
    s = re.sub(r"^[^0-9A-Za-z一-鿿]+", "", s)                      # leading punctuation
    s = re.sub(r"^\d{1,2}\.\d{1,2}\s*", "", s)                             # leading MM.DD fragment
    s = re.sub(r"^((19|20)\d{2})?\s*年\s*", "", s)                         # leading "2024年"/orphan "年"
    s = re.sub(r"\s*(19|20)\d{2}(\s*[/／–-]\s*(19|20)\d{2})?\s*$", "", s)  # trailing year(s)
    s = s.strip()
    return s or (rn or "")


def family_key(label):
    """Race-family bucket for hero dedupe: the first two CJK characters
    (北高360 / 北高360認證式挑戰 / 北高 all bucket to 北高). Labels with
    fewer than two CJK chars stay their own bucket."""
    cjk = re.findall(r"[一-鿿]", label)
    return "".join(cjk[:2]) if len(cjk) >= 2 else label


def select_ridgeline(benchmarks, n=8):
    rows = []
    for race in benchmarks.values():
        a = _largest_all(race)
        if a is None:
            continue
        rows.append({"label": clean_label(race.get("rn", "")),
                     "median": int(a["median"]), "finishers": int(a["n"])})
    rows.sort(key=lambda r: r["finishers"], reverse=True)
    # one node per race family: keep the largest variant (rows already sorted)
    seen, deduped = set(), []
    for r in rows:
        fk = family_key(r["label"])
        if fk in seen:
            continue
        seen.add(fk)
        deduped.append(r)
    rows = deduped[:n]
    rows.sort(key=lambda r: r["median"])
    meds = [r["median"] for r in rows]
    lo, hi = (min(meds), max(meds)) if meds else (0, 1)
    span = (hi - lo) or 1
    return [{"label": r["label"], "x": i, "y": round((r["median"] - lo) / span, 4),
             "median": r["median"], "finishers": r["finishers"]} for i, r in enumerate(rows)]
