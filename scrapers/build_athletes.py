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
import statistics
from collections import Counter, defaultdict

import common
from race_type import classify as race_type

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


def _traits(recs, field_sizes):
    """Per-discipline median in-field percentile for one athlete — the radar of
    climber (爬坡) vs rouleur (繞圈/公路) strength. Only types with >=2 results."""
    by_type = defaultdict(list)
    for r in recs:
        rank = r.get("rank_overall")
        f = field_sizes.get((r.get("race_key"), r.get("year")))
        if not rank or not f or f < 1 or rank > f:
            continue
        t = race_type(r.get("race_name_canonical") or r.get("race_name_raw"),
                      r.get("category_raw"))
        by_type[t].append((f - rank) / f * 100)
    return {t: {"pct": round(statistics.median(v), 1), "n": len(v)}
            for t, v in by_type.items() if len(v) >= 2}


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
            "teams": distinct_teams, "traits": _traits(recs, field_sizes),
            "history": hist,
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
        if len(recs) < MIN_RESULTS:
            continue
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


def build_course_records(records, profiles, top_n=50):
    """All-time fastest board PER profiled climb race (course records 2009→).
    Only the curated, route-stable climbs (climb_profiles.json) qualify, so times
    are comparable across editions. Dedups to each rider's single fastest ascent;
    ranks by finish time (≡ VAM rank for a fixed-elevation profile). Output keyed
    by race_key — each event keeps its own board (different events up the same
    mountain ride different courses)."""
    keys = build_group_keys(records)
    group_size = Counter(keys)
    best = {}  # (athlete_group, race_key) -> that rider's fastest ascent here
    for k, r in zip(keys, records):
        if k in ("n:", "u:", "t:"):       # unresolved identity / nameless — skip
            continue
        rk = r.get("race_key")
        prof = profiles.get(rk)
        if not prof:
            continue
        sec = r.get("finish_seconds")
        v = _vam(prof["elev_m"], sec)
        if not _plausible(v):
            continue
        key2 = (k, rk)
        cur = best.get(key2)
        if cur is None or sec < cur["_sec"]:
            best[key2] = {
                "_sec": sec, "_gk": k,
                "nm": r.get("name_masked") or common.mask_name(r.get("name_raw")),
                "t": int(sec), "vam": v, "wkg": _wkg(v, prof.get("grade")),
                "y": r.get("year"), "g": r.get("gender"),
                "cat": r.get("category_raw") or r.get("result_label"),
            }
    by_rk = defaultdict(list)
    for (gk, rk), e in best.items():
        by_rk[rk].append(e)
    out = {}
    for rk, entries in by_rk.items():
        prof = profiles[rk]
        entries.sort(key=lambda e: e["_sec"])
        recs = [
            {"rank": i, "nm": e["nm"], "t": e["t"], "vam": e["vam"], "wkg": e["wkg"],
             "y": e["y"], "g": e["g"], "cat": e["cat"],
             "id": athlete_id(e["_gk"]), "link": group_size[e["_gk"]] >= MIN_RESULTS}
            for i, e in enumerate(entries[:top_n], 1)
        ]
        out[rk] = {"name": prof["name"], "rk": rk, "dist_km": prof["dist_km"],
                   "elev_m": prof["elev_m"], "grade": prof["grade"],
                   "n": len(entries), "records": recs}
    return out


def build_head_to_head(records, details, min_results=6, min_meets=3, top_rivals=6):
    """Each athlete's top head-to-head rivals: opponents they've met in the same
    race-year >=min_meets times, with the win/loss split (lower rank = win).
    Bounded to 'active' athletes (>=min_results) to keep the pairwise pass cheap.
    Returns {athlete_id: [{id, nm, w, l, meets}, ...]}."""
    keys = build_group_keys(records)
    by_athlete = defaultdict(list)
    for k, r in zip(keys, records):
        if k in ("n:", "u:", "t:") or not r.get("rank_overall"):
            continue
        by_athlete[k].append((r.get("race_key"), r.get("year"), r["rank_overall"]))
    active = {k for k, v in by_athlete.items() if len(v) >= min_results}
    ry = defaultdict(list)                       # (race_key, year) -> [(key, rank)]
    for k in active:
        for rk, y, rank in by_athlete[k]:
            ry[(rk, y)].append((k, rank))
    h2h = defaultdict(lambda: [0, 0])            # (a<b) -> [a_wins, meets]
    for lst in ry.values():
        for i in range(len(lst)):
            ai, ari = lst[i]
            for j in range(i + 1, len(lst)):
                bi, bri = lst[j]
                if ari == bri:
                    continue                     # tie / same row guard
                pair = (ai, bi) if ai < bi else (bi, ai)
                e = h2h[pair]
                e[1] += 1
                winner = ai if ari < bri else bi
                if winner == pair[0]:
                    e[0] += 1
    rivals = defaultdict(list)
    for (a, b), (awins, meets) in h2h.items():
        if meets < min_meets:
            continue
        rivals[a].append((b, awins, meets))
        rivals[b].append((a, meets - awins, meets))
    out = {}
    for k, lst in rivals.items():
        aid = athlete_id(k)
        if aid not in details:
            continue
        # deterministic order: most meetings, then most wins, then a stable id —
        # without the id tiebreak, tied rivals fall back to set-iteration order
        # (randomized per process by PYTHONHASHSEED), churning every athlete file.
        lst.sort(key=lambda x: (-x[2], -x[1], athlete_id(x[0])))
        rows = []
        for b, w, m in lst[:top_rivals]:
            bid = athlete_id(b)
            if bid in details:
                rows.append({"id": bid, "nm": details[bid]["nm"], "w": w, "l": m - w, "meets": m})
        if rows:
            out[aid] = rows
    return out


def main():
    records = list(common.iter_records(IN))  # RAM-frugal streaming parse
    index, details = build_athletes(records)
    rivals = build_head_to_head(records, details)
    for aid, rows in rivals.items():
        details[aid]["rivals"] = rows
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
    course_records = build_course_records(records, profiles)
    with open(os.path.join(OUT, "course_records.json"), "w", encoding="utf-8") as f:
        json.dump(course_records, f, ensure_ascii=False, separators=(",", ":"))
    print(f"course_records={len(course_records)} boards "
          f"({sum(len(b['records']) for b in course_records.values())} rows)")


if __name__ == "__main__":
    main()
