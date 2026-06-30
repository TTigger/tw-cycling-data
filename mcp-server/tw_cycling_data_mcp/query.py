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
