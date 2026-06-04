# -*- coding: utf-8 -*-
"""
PoC step 3 — parse a cyclist.org.tw result PDF into structured rows via
line-based regex (extract_text is clean & regular; table detection is not).

Proves end-to-end: PDF -> normalized result records with rank/bib/name/
nationality/division(gender+age band)/team/times.
"""
import json
import os
import re
import sys
import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

TIME = r"\d{1,2}:\d{2}:\d{2}(?:\.\d{1,2})?"
# rank bib  name...  NAT(3 upper)  DIV(no-space)  team...  time [time...] total
ROW = re.compile(
    rf"^(?P<rank>\d{{1,4}})\s+"
    rf"(?P<bib>\d{{1,5}})\s+"
    rf"(?P<name>.+?)\s+"
    rf"(?P<nat>[A-Z]{{3}})\s+"
    rf"(?P<div>\S+)\s+"
    rf"(?P<team>.+?)\s+"
    rf"(?P<times>(?:{TIME}\s*)+)$"
)

DIV_RE = re.compile(r"^(?P<g>[MWmwＭＷ])\s?(?P<age>\d{1,2})$")


def parse_division(div):
    """M25 -> (male, '25-29'); W40 -> (female, '40-44'). Else passthrough."""
    m = DIV_RE.match(div)
    if not m:
        return None, div  # Chinese category like 菁英組/挑戰組 — keep raw
    g = m.group("g").upper()
    gender = "M" if g in ("M", "Ｍ") else "F"
    return gender, f"{m.group('age')}+"


def parse_pdf(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            for line in txt.splitlines():
                line = line.strip()
                m = ROW.match(line)
                if not m:
                    continue
                times = re.findall(TIME, m.group("times"))
                gender, age_group = parse_division(m.group("div"))
                rows.append({
                    "rank_overall": int(m.group("rank")),
                    "bib": m.group("bib"),
                    "name_raw": m.group("name").strip(),
                    "nationality": m.group("nat"),
                    "division_raw": m.group("div"),
                    "gender": gender,
                    "age_group": age_group,
                    "team": m.group("team").strip(),
                    "splits": times[:-1],
                    "finish_time": times[-1] if times else None,
                    "_page": pno,
                })
    return rows


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "data", "pdf", "2026050917190897897.pdf")
    rows = parse_pdf(path)
    print(f"PARSED {len(rows)} result rows from {os.path.basename(path)}\n")
    for r in rows[:12]:
        print(f"  #{r['rank_overall']:>3} bib={r['bib']:>4} {r['name_raw']:<12} "
              f"{r['nationality']} {r['division_raw']:<5} ({r['gender']}/{r['age_group']}) "
              f"{r['team'][:18]:<18} {r['finish_time']}")
    out = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                       "sample_cyclist_taipingshan2026_gc.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\n  -> wrote {len(rows)} rows to {os.path.relpath(out)}")
    # quick stats
    genders = {}
    ages = {}
    for r in rows:
        genders[r["gender"]] = genders.get(r["gender"], 0) + 1
        ages[r["age_group"]] = ages.get(r["age_group"], 0) + 1
    print(f"  gender dist: {genders}")
    print(f"  age-group dist: {dict(sorted(ages.items(), key=lambda x: str(x[0])))}")
