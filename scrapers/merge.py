# -*- coding: utf-8 -*-
"""
Merge all source datasets into one master dataset, applying cross-source
normalization (race_class + series). Auto-discovers every source file matching
cyclist_*.json / bravelog_*.json / cycling_*.json (excluding .public + _summary),
so adding a new year range or source needs no edit here.

Outputs:
  data/processed/master.json         (full, internal — has name_raw)
  data/processed/master.public.json  (de-identified — for frontend/Vercel)
  data/processed/master_summary.json (stats for QC + viz)
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402
import normalize  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
SOURCE_PREFIXES = ("criterium_", "cyclist_", "bravelog_", "cycling_", "irunner_",
                   "focusline_", "taiwanbike_", "sporter96_", "sport_result_", "ebetter_",
                   "atsport_")


def discover_sources():
    """Every full source dataset: <source>_*.json minus .public.json / _summary.json."""
    out = []
    for p in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        b = os.path.basename(p)
        if b.startswith(SOURCE_PREFIXES) and not b.endswith((".public.json", "_summary.json")):
            out.append(p)
    return out


# Races superseded by a better source — their rows are skipped at merge.
# bravelog's combined 2025 TBA cert (北高360+雙塔520+四極602 in one race_key) is
# replaced by taiwanbike.org's authoritative per-distance results.
# Entries are (platform, race_key) or (platform, race_key, year).
SUPERSEDED = {("bravelog.tw", "TBA北高360雙塔520四極602自行車認證"),
              # 彰化經典百K 2023 is on both bravelog (gun time) and iRunner (net
              # time, ~minutes apart, so the exact-dup check can't pair them).
              # The published dataset used bravelog; keep it, drop the twin.
              ("irunner.biji.co", "彰化經典百K", 2023),
              # 96 武嶺 2026: the organizer's PDF covers part of the field; the
              # timer's own site (sport-result.com) has all of it.
              ("96sporter.com", "96聯賽武嶺站競賽組及市民競賽組", 2026)}


def is_superseded(r):
    return ((r["source_platform"], r["race_key"]) in SUPERSEDED
            or (r["source_platform"], r["race_key"], r.get("year")) in SUPERSEDED)

iter_records = common.iter_records  # streaming JSON-array reader (RAM-frugal)


def should_drop_zero_time(r):
    """Drop genuine zero/negative-time noise, but KEEP explicit DNF/DNS rows —
    criterium.tw reports non-finishers, which legitimately have no finish time."""
    if r.get("status") in ("DNF", "DNS"):
        return False
    fs = r.get("finish_seconds")
    return fs is not None and fs <= 0


def is_dup(r, fs, seen, seen_masked, seen_src_masked):
    """Cross-source exact duplicate? Keyed on (year, name, whole seconds).
    A source that masks names itself (bravelog '黃*翔') can't match the real name
    another source has for the same result, so when EITHER side is source-masked
    compare masked forms instead. Real-vs-real still needs the exact real name, so
    two different 黃○翔 with the same time in real-named sources aren't merged."""
    name = r["name_raw"]
    mk = (r.get("year"), common.mask_name(name), fs)
    if "*" in name or "＊" in name:
        if mk in seen_masked:
            return True
        seen_src_masked.add(mk)
        seen_masked.add(mk)
        return False
    k = (r.get("year"), name, fs)
    if k in seen or mk in seen_src_masked:
        return True
    seen.add(k)
    seen_masked.add(mk)
    return False


PERSON_NAME = re.compile(r"[\u4e00-\u9fff]{2,4}")


def _table_key(r):
    return (r.get("year"), r.get("source_url"), r.get("result_label"))


def cross_listed_tables(records, min_rows=10, share=0.95):
    """Result tables one source posted under two different events.

    cyclist.org.tw linked the 2026-11-01 ITT from both 花蓮太平洋盃 (pno=170) and
    臺灣KOM登山王 (pno=172); the plain (year, name, seconds) dedup then split that
    one ITT 47/19 between the two races. A table whose finishers are (almost) all
    inside a strictly larger table of ANOTHER race in the same year is the copy:
    drop it whole, so the result stays with one race. Returns the table keys."""
    tables, race_of = defaultdict(set), {}
    for r in records:
        fs = r.get("finish_seconds")
        if r.get("name_raw") and fs and r.get("status") in (None, "FIN"):
            k = _table_key(r)
            tables[k].add((r["name_raw"], int(fs)))
            race_of[k] = r.get("race_key")
    by_year = defaultdict(list)
    for k, rows in tables.items():
        by_year[k[0]].append((k, rows))
    drop = set()
    for lst in by_year.values():
        for k, rows in lst:
            if len(rows) < min_rows:
                continue
            for k2, rows2 in lst:
                if race_of[k2] != race_of[k] and len(rows2) > len(rows) \
                        and len(rows & rows2) >= share * len(rows):
                    drop.add(k)
                    break
    return drop


def rider_names(paths):
    """Every real rider name across all sources (one cheap streaming pass)."""
    names = set()
    for p in paths:
        for r in iter_records(p):
            nm = r.get("name_raw")
            if nm and PERSON_NAME.fullmatch(nm):
                names.add(nm)
    return names


_CJK_RUN = re.compile(r"[\u4e00-\u9fff]{3,}")


def mask_person_team(team, names):
    """Riders sometimes enter a person's name (their own or a friend's) as their
    team, alone or inside a longer string ("王大明&陳小美親友團", "狂抽猛送王大明").
    The team field is published, so any 3–4 character stretch of it that is some
    rider's real name is masked like a name (PDPA). Two-character names are left
    alone: too many ordinary words would match."""
    t = (team or "").strip()
    if t in names:
        return common.mask_name(t)
    if not team:
        return team

    def fix(m):
        s, out, i = m.group(0), [], 0
        while i < len(s):
            for n in (4, 3):
                if i + n <= len(s) and s[i:i + n] in names:
                    out.append(common.mask_name(s[i:i + n]))
                    i += n
                    break
            else:
                out.append(s[i])
                i += 1
        return "".join(out)

    return _CJK_RUN.sub(fix, team)


def main():
    print("merging sources (streaming):")
    import gc
    mf = open(os.path.join(OUT, "master.json"), "w", encoding="utf-8")
    pf = open(os.path.join(OUT, "master.public.json"), "w", encoding="utf-8")
    mf.write("[\n")
    pf.write("[\n")

    # Stream one source at a time: filter → cross-source dedup → enrich → re-mask →
    # write each record straight to disk, then free the source. Peak memory stays at
    # ~one source instead of the whole corpus (RAM-tight machines OOM'd otherwise).
    # Dedup keeps the first-loaded source (sources load in sorted-glob order, as before).
    seen, seen_masked, seen_src_masked = set(), set(), set()
    n_out = n_zero = n_dup = n_superseded = n_cross = 0
    races = defaultdict(lambda: {"rows": 0, "years": set(), "series": None, "platform": None})
    by_platform, by_year, by_gender, by_class, by_series = (Counter() for _ in range(5))
    by_status, finishers_by_platform = Counter(), Counter()

    sources = discover_sources()
    names = rider_names(sources)
    n_team_masked = 0
    for p in sources:
        src_n = 0
        cross = cross_listed_tables(iter_records(p))
        for r in iter_records(p):
            src_n += 1
            if cross and _table_key(r) in cross:   # same table posted under 2 events
                n_cross += 1
                continue
            fs = r.get("finish_seconds")
            if should_drop_zero_time(r):      # zero-time noise, but keep DNF/DNS
                n_zero += 1
                continue
            if r.get("name_raw") and fs:        # cross-source exact-dup dedup
                if is_dup(r, int(fs), seen, seen_masked, seen_src_masked):
                    n_dup += 1
                    continue
            normalize.enrich(r)
            if is_superseded(r):
                n_superseded += 1
                continue
            if r.get("name_raw"):               # re-mask at merge time (policy applied here)
                r["name_masked"] = common.mask_name(r["name_raw"])
            if r.get("team"):
                t = mask_person_team(r["team"], names)
                if t != r["team"]:
                    r["team"] = t
                    n_team_masked += 1
            rk = r["race_key"]
            races[rk]["rows"] += 1
            races[rk]["years"].add(r["year"])
            races[rk]["series"] = r.get("series")
            races[rk]["platform"] = r["source_platform"]
            by_platform[r["source_platform"]] += 1
            by_year[r["year"]] += 1
            by_gender[r["gender"]] += 1
            by_class[r["race_class"]] += 1
            by_series[r["series"]] += 1
            by_status[r.get("status")] += 1
            if r.get("status") in (None, "FIN"):
                finishers_by_platform[r["source_platform"]] += 1
            sep = ",\n" if n_out else ""
            mf.write(sep)
            json.dump(r, mf, ensure_ascii=False)
            r.pop("name_raw", None)             # public: de-identified
            pf.write(sep)
            json.dump(r, pf, ensure_ascii=False)
            n_out += 1
        print(f"  loaded {src_n:>6}  {os.path.basename(p)}")
        gc.collect()

    mf.write("\n]\n"); mf.close()
    pf.write("\n]\n"); pf.close()
    if n_zero:
        print(f"  dropped {n_zero} zero-time (DNF/未計時) rows")
    if n_dup:
        print(f"  dropped {n_dup} cross-source exact-duplicate rows")
    if n_team_masked:
        print(f"  masked {n_team_masked} team values that were a rider's real name")
    if n_superseded:
        print(f"  dropped {n_superseded} superseded rows (bravelog races replaced by a better source)")
    if n_cross:
        print(f"  dropped {n_cross} rows of result tables posted under two events (kept with the larger one)")

    summary = {
        "total_records": n_out,
        # finishers = rows the site counts (status None/FIN); the rest are
        # DNF/DNS-style rows kept for completion rates (criterium.tw "NF").
        "finishers": sum(v for k, v in by_status.items() if k in (None, "FIN")),
        "by_platform": dict(by_platform),
        "finishers_by_platform": dict(finishers_by_platform),
        "by_year": dict(sorted(by_year.items(), key=lambda x: str(x[0]))),
        "by_gender": dict(by_gender),
        "by_race_class": dict(by_class),
        "by_series": dict(by_series.most_common()),
        "by_status": dict(by_status),
        "distinct_races": len(races),
        "races": [
            {"race_key": k, "series": v["series"], "platform": v["platform"],
             "years": sorted(y for y in v["years"] if y), "rows": v["rows"]}
            for k, v in sorted(races.items(), key=lambda x: -x[1]["rows"])
        ],
    }
    json.dump(summary, open(os.path.join(OUT, "master_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print(f"\n=== MASTER === records={summary['total_records']}  finishers={summary['finishers']}  races={summary['distinct_races']}")
    print(f"  platform: {summary['by_platform']}")
    print(f"  year:     {summary['by_year']}")
    print(f"  gender:   {summary['by_gender']}")
    print(f"  class:    {summary['by_race_class']}")
    print(f"  series ({len(summary['by_series'])}):")
    for k, v in list(summary["by_series"].items())[:20]:
        print(f"     {v:>6}  {k}")
    print(f"\n  -> master.json (+ .public.json, master_summary.json)")


if __name__ == "__main__":
    main()
