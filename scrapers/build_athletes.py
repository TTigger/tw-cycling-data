# -*- coding: utf-8 -*-
"""Build per-athlete tracking data from the master dataset (Phase 3).

Reads  data/processed/master.json          (INTERNAL — has name_raw, needed to
                                             link the same person across races)
Writes web/public/data/athletes.json       (de-identified athlete index, >=2 results)
       web/public/data/athlete/<id>.json    (de-identified per-athlete history)

Identity resolution (owner-approved policy):
  * Primary grouping is by name_raw, so a rider's whole career stays in ONE
    athlete even when they switch teams year to year.
  * A UCI ID, when present, is a strong unique anchor: rows whose name maps to a
    single UCI ID are unified under that UCI group (joins their UCI + non-UCI
    rows), and UCI-anchored athletes are marked high confidence.
  * Team SPREAD is a homonym signal, not a split key: a name appearing across
    many distinct teams is likely several different people, so its confidence is
    downgraded and the UI flags it ("可能為同名不同人").

PDPA: output carries only masked names (李○ / 王○明), a salted non-reversible
athlete id, and a has_uci boolean — never name_raw or the raw UCI ID.
"""
import hashlib
import json
import os
from collections import Counter, defaultdict

import common

HERE = os.path.dirname(__file__)
IN = os.path.join(HERE, "..", "data", "processed", "master.json")
OUT = os.path.join(HERE, "..", "web", "public", "data")

# Fixed project salt so athlete ids are not a plain sha1(name) rainbow lookup.
_SALT = "twcd-athlete-v1"
MIN_RESULTS = 2  # singletons aren't "trackable" — excluded from the index

PROFILES_PATH = os.path.join(OUT, "climb_profiles.json")
VAM_MIN, VAM_MAX = 100, 3000


def _vam(elev_m, seconds):
    if not elev_m or not seconds or seconds <= 0:
        return None
    return round(elev_m / (seconds / 3600))


def _wkg(vam_value, grade_pct):
    if vam_value is None or not grade_pct:
        return None
    return round(vam_value / (100 * (2 + grade_pct / 10)), 1)


def _plausible(v):
    return v is not None and VAM_MIN <= v <= VAM_MAX


def load_profiles():
    if not os.path.exists(PROFILES_PATH):
        return {}
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return {p["race_key"]: p for p in json.load(f)}


def athlete_id(group_key):
    """Stable, salted, non-reversible 10-hex id for a group key (u:<uci> / n:<name>)."""
    h = hashlib.sha1((_SALT + "|" + group_key).encode("utf-8")).hexdigest()
    return h[:10]


def build_group_keys(records):
    """Assign each record a grouping key, anchoring on a stable rider id where a
    name ties to exactly one. Two id sources: tsu.com.tw rider ids (t:, broadest)
    and UCI ids (u:); a bare name falls back to n:. Returns a list parallel to
    `records`."""
    # name_raw -> set of ids ever seen with it, per id type
    name_tsus, name_ucis = defaultdict(set), defaultdict(set)
    for r in records:
        nm = r.get("name_raw")
        if nm and r.get("tsu_rider_id"):
            name_tsus[nm].add(str(r["tsu_rider_id"]))
        if nm and r.get("uci_id"):
            name_ucis[nm].add(str(r["uci_id"]))
    # a name unambiguously anchored to one id
    tsu_anchor = {nm: next(iter(s)) for nm, s in name_tsus.items() if len(s) == 1}
    uci_anchor = {nm: next(iter(s)) for nm, s in name_ucis.items() if len(s) == 1}

    keys = []
    for r in records:
        nm, uci, tsu = r.get("name_raw"), r.get("uci_id"), r.get("tsu_rider_id")
        if tsu:
            keys.append(f"t:{tsu}")
        elif uci:
            keys.append(f"u:{uci}")
        elif nm in tsu_anchor:
            keys.append(f"t:{tsu_anchor[nm]}")
        elif nm in uci_anchor:
            keys.append(f"u:{uci_anchor[nm]}")
        elif nm:
            keys.append(f"n:{nm}")
        else:
            keys.append("n:")  # nameless rows lump together; dropped later
    return keys


def confidence(is_anchored, distinct_teams, name_len, mixed_gender=False):
    """high / med / low identity confidence.
    Anchored to a stable rider id (tsu/UCI) -> high. A single identity that races
    as BOTH M and F is almost certainly two people sharing a name -> low.
    Otherwise team spread is the homonym signal, and very short (<=2 char) names
    collide more so they downgrade one extra level. (Most bravelog citizen rows
    carry no team, so the team signal is weak there — gender mixing catches some
    of those collisions.)"""
    if mixed_gender and not is_anchored:
        return "low"
    if is_anchored:
        return "high"
    level = "high"
    if distinct_teams >= 5:
        level = "low"
    elif distinct_teams >= 3:
        level = "med"
    if name_len <= 2 and distinct_teams >= 3:
        level = "low"
    return level


def _history_row(r, field=None):
    """One de-identified result in an athlete's career. `field` = number of
    finishers in that (race_key, year), so the UI can show a comparable
    percentile (rank within field) across races of very different sizes."""
    return {"y": r.get("year"), "rk": r.get("race_key"),
            "rn": r.get("race_name_canonical"), "cat": r.get("category_raw"),
            "g": r.get("gender"), "ag": r.get("age_group"),
            "team": r.get("team"), "rank": r.get("rank_overall"),
            "t": r.get("finish_seconds"), "label": r.get("result_label"),
            "d": r.get("date"), "field": field}


def build_athletes(records):
    """Return (index, details): index is the athlete list (>=2 results),
    details maps id -> per-athlete detail dict. Both fully de-identified."""
    keys = build_group_keys(records)
    groups = defaultdict(list)
    for k, r in zip(keys, records):
        if k in ("n:", "u:"):
            continue
        groups[k].append(r)
    # finishers per (race_key, year) -> comparable percentile in each history row
    field_sizes = Counter((r.get("race_key"), r.get("year")) for r in records)

    index, details = [], {}
    for gk, recs in groups.items():
        if len(recs) < MIN_RESULTS:
            continue
        aid = athlete_id(gk)
        is_tsu = gk.startswith("t:")
        is_uci = gk.startswith("u:")
        is_anchored = is_tsu or is_uci
        # representative masked name: most common masked form in the group
        masked = Counter(r.get("name_masked") or common.mask_name(r.get("name_raw"))
                         for r in recs).most_common(1)[0][0]
        teams = [t for t in (r.get("team") for r in recs) if t]
        distinct_teams = sorted(set(teams))
        years = sorted({r.get("year") for r in recs if r.get("year")})
        races = {r.get("race_key") for r in recs}
        name_len = len([c for c in (recs[0].get("name_raw") or "") if not c.isspace()])
        genders = {r.get("gender") for r in recs if r.get("gender") in ("M", "F")}
        conf = confidence(is_anchored, len(distinct_teams), name_len,
                          mixed_gender=len(genders) > 1)
        ranks = [r.get("rank_overall") for r in recs if r.get("rank_overall")]

        hist = sorted(
            (_history_row(r, field_sizes.get((r.get("race_key"), r.get("year"))))
             for r in recs),
            key=lambda h: (h["y"] or 0, h["d"] or "", h["rank"] or 9999))
        details[aid] = {
            "id": aid, "nm": masked, "conf": conf,
            "has_uci": is_uci, "has_rider": is_tsu,
            "teams": distinct_teams, "history": hist,
        }
        index.append({
            # Kept lean: shipped to every /athletes visit for client-side search.
            # Team names + full history live in the per-athlete detail file (id).
            "id": aid, "nm": masked, "n": len(recs),
            "ny": len(years), "nr": len(races),
            "y0": years[0] if years else None, "y1": years[-1] if years else None,
            "best": min(ranks) if ranks else None,
            "conf": conf, "uci": is_uci, "rid": is_tsu,
        })
    # most-tracked athletes first
    index.sort(key=lambda a: (-a["n"], -a["ny"], str(a["id"])))
    return index, details


def build_climb_vam(records, profiles):
    """Best VAM per athlete across profiled climb races. Uses the same identity
    grouping as build_athletes (tsu/UCI/name)."""
    keys = build_group_keys(records)
    groups = defaultdict(list)
    for k, r in zip(keys, records):
        if k not in ("n:", "u:", "t:"):
            groups[k].append(r)
    out = []
    for gk, recs in groups.items():
        best = None
        for r in recs:
            prof = profiles.get(r.get("race_key"))
            if not prof:
                continue
            v = _vam(prof["elev_m"], r.get("finish_seconds"))
            if not _plausible(v):
                continue
            if best is None or v > best["best_vam"]:
                best = {"best_vam": v, "best_wkg": _wkg(v, prof.get("grade")),
                        "climb": prof["name"], "y": r.get("year"),
                        "conf": prof.get("conf"), "g": r.get("gender")}
        if best is None:
            continue
        masked = Counter(r.get("name_masked") or common.mask_name(r.get("name_raw"))
                         for r in recs).most_common(1)[0][0]
        out.append({"id": athlete_id(gk), "nm": masked, **best})
    out.sort(key=lambda e: -e["best_vam"])
    return out


def main():
    with open(IN, encoding="utf-8") as f:
        records = json.load(f)
    index, details = build_athletes(records)
    os.makedirs(os.path.join(OUT, "athlete"), exist_ok=True)
    with open(os.path.join(OUT, "athletes.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    for aid, d in details.items():
        with open(os.path.join(OUT, "athlete", f"{aid}.json"), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    conf = Counter(a["conf"] for a in index)
    print(f"athletes={len(index)} (of trackable) detailFiles={len(details)} "
          f"conf={dict(conf)} -> {os.path.relpath(OUT)}")
    profiles = load_profiles()
    climb_vam = build_climb_vam(records, profiles)
    with open(os.path.join(OUT, "climb_vam.json"), "w", encoding="utf-8") as f:
        json.dump(climb_vam, f, ensure_ascii=False, separators=(",", ":"))
    print(f"climb_vam={len(climb_vam)} (across {len(profiles)} profiled climbs)")


if __name__ == "__main__":
    main()
