# -*- coding: utf-8 -*-
"""
Shared helpers for the TW cycling data pipeline:
HTTP session, division/category normalization, name de-identification (PDPA),
time parsing, and the unified result-record builder.
"""
import gzip
import hashlib
import json
import os
import re
import time
from urllib.parse import urlparse

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Single source of truth for the versioned public API output directory.
# All build_*/discover/overseas scripts write here; the frontend reads /data/v1/.
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "public", "data", "v1")


def iter_records(path, chunk=1 << 18):
    """Stream a top-level JSON array of objects one record at a time, never holding
    the whole file string in memory. `list(iter_records(p))` peaks at ~the result
    list (no extra 80 MB file-str + parse spike) — survives RAM-tight machines where
    json.load() of the 80 MB master OOMs."""
    dec = json.JSONDecoder()
    with open(path, encoding="utf-8") as f:
        buf = ""
        while "[" not in buf:
            more = f.read(chunk)
            if not more:
                return
            buf += more
        buf = buf[buf.index("[") + 1:]
        while True:
            buf = buf.lstrip()
            while buf[:1] == ",":
                buf = buf[1:].lstrip()
            if buf[:1] == "]":
                return
            if buf == "":
                more = f.read(chunk)
                if not more:
                    return
                buf += more
                continue
            try:
                obj, end = dec.raw_decode(buf)
            except ValueError:
                more = f.read(chunk)
                if not more:
                    return
                buf += more
                continue
            yield obj
            buf = buf[end:]


def make_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9"})
    return s


_last = {"t": 0.0}


def polite_get(session, url, delay=0.6, **kw):
    """GET with a minimum spacing between requests (be a good citizen)."""
    dt = time.monotonic() - _last["t"]
    if dt < delay:
        time.sleep(delay - dt)
    kw.setdefault("timeout", 40)
    r = session.get(url, **kw)
    _last["t"] = time.monotonic()
    if r.ok:
        archive_response(url, r.content)
    return r


# ---- raw archive (roadmap D5) ------------------------------------------------
# Source sites take old results down; the parsers improve over time. Keeping the
# raw bytes of every successful fetch means history can always be re-parsed.
# Layout: data/raw_archive/<netloc>/<YYYY-MM-DD>/<sha1-12>.gz + manifest.jsonl
# (one line per fetch event; identical payloads dedupe to one blob per day).
# Off-site sync to R2 is backup.py's job. Opt out with TWCD_RAW_ARCHIVE=0.

RAW_ARCHIVE_DIR = os.environ.get(
    "TWCD_RAW_ARCHIVE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data", "raw_archive"),
)


def archive_response(url, content, when=None):
    """Persist one fetched payload; returns the blob path or None if disabled."""
    if os.environ.get("TWCD_RAW_ARCHIVE", "1") == "0":
        return None
    if not content:
        return None
    if isinstance(content, str):
        content = content.encode("utf-8")
    source = urlparse(url).netloc or "unknown"
    day = time.strftime("%Y-%m-%d", time.localtime(when))
    sha = hashlib.sha1(content).hexdigest()[:12]
    day_dir = os.path.join(RAW_ARCHIVE_DIR, source, day)
    os.makedirs(day_dir, exist_ok=True)
    blob = os.path.join(day_dir, sha + ".gz")
    if not os.path.exists(blob):
        with gzip.open(blob, "wb") as f:
            f.write(content)
    entry = {"ts": int(when if when is not None else time.time()),
             "url": url, "sha1": sha, "bytes": len(content)}
    with open(os.path.join(day_dir, "manifest.jsonl"), "a", encoding="utf-8") as m:
        m.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return blob


# ---- normalization ----------------------------------------------------------

# division token patterns seen across TCF PDF layouts (road races AND KOM hill-climbs):
#   M25 / M20            (road: gender+age-band-start)
#   M24-35 / M40-49      (KOM: gender + age range)
#   MASTER               (KOM masters)
#   女子 / 女子組 / W40    (female)
#   U13 / U15            (youth, no gender)
#   菁英組 / 挑戰組 / 市民組 (Chinese category, no encoded gender/age)
DIV_TOKEN = (
    r"(?:MASTER|男子組|女子組|男子|女子"
    r"|電動輔助自行車組?|電輔車組?|電輔組?"
    r"|菁英組?|挑戰組?|競賽組?|市民組?|巿民組?|國中組?|高中組?|青年組?|社會組?|公開組?"
    r"|[MWFmwf]\d{1,2}-\d{1,2}|[MWFmwf]\d{1,2}|[Uu]\d{1,2})"
)
_DIV_HEAD = re.compile(r"^\s*(" + DIV_TOKEN + r")")
_RANGE = re.compile(r"(\d{1,2})\s*-\s*(\d{1,2})")
_SINGLE = re.compile(r"[MWFmwf](\d{1,2})$")


def split_division_team(segment):
    """Given the text right after nationality (div may be glued to team with no space),
    return (division_raw, team). e.g. 'M24-35宜蘭培訓隊' -> ('M24-35','宜蘭培訓隊')."""
    if not segment:
        return None, None
    m = _DIV_HEAD.match(segment)
    if not m:
        return None, segment.strip() or None
    div = m.group(1)
    team = segment[m.end():].strip()
    return div, (team or None)


def parse_division(div):
    """Return (gender, age_group). 'M24-35'->('M','24-35'); '女子'->('F',None);
    'U15'->(None,'U15'); 'MASTER'->('M','MASTER'); Chinese category->(None,None)."""
    if not div:
        return None, None
    div = div.strip()
    # gender
    if div.startswith(("W", "w", "F", "f")) or "女" in div:
        gender = "F"
    elif div.startswith(("M", "m", "Ｍ")) or "男" in div:
        gender = "M"
    else:
        gender = None
    # age band
    mr = _RANGE.search(div)
    if mr:
        age = f"{mr.group(1)}-{mr.group(2)}"
    elif re.match(r"^[Uu]\d{1,2}$", div):
        age = div.upper()
    elif div == "MASTER":
        age = "MASTER"
    else:
        ms = _SINGLE.match(div)
        age = ms.group(1) if ms else None
    return gender, age


def gender_from_group(group):
    """'男子組' -> 'M', '女子組' -> 'F'."""
    if not group:
        return None
    if "男" in group:
        return "M"
    if "女" in group:
        return "F"
    return None


def mask_name(name):
    """PDPA de-identification for public output.
    CJK: keep head+tail char, mask the middle -> 2-char '李○', 3-char '王○明',
    4+ '歐○○菲' (owner-chosen rule: surname + last given-name char stay visible,
    enough to disambiguate homonyms in athlete tracking without exposing full name).
    Latin/other: order-agnostic — every token -> first letter + ○ (e.g. 'A○ D○'); junk -> ''."""
    if not name:
        return name
    name = name.strip()
    if re.search(r"[一-鿿]", name):
        chars = [c for c in name if not c.isspace()]
        if len(chars) <= 1:
            return name
        if len(chars) == 2:
            return chars[0] + "○"
        return chars[0] + "○" * (len(chars) - 2) + chars[-1]
    # latin / other scripts -> order-agnostic: EVERY token -> first letter + ○.
    # Hides every given name regardless of name order (Surname-first, "Surname,
    # Given", and Western are all safe). Output contains ○ so it is recognisably
    # masked (and kept by the dataset safeguard). Scraping junk (< or > anywhere,
    # or tokens with no letters) -> empty string.
    if "<" in name or ">" in name:
        return ""
    masked = []
    for token in name.split():
        first = next((c for c in token if c.isalpha()), None)
        if first:
            masked.append(first + "○")
    if not masked:
        return ""
    return " ".join(masked)


_TIME_RE = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d{1,2}))?")


def time_to_seconds(t):
    if not t:
        return None
    m = _TIME_RE.search(t)
    if not m:
        return None
    h, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
    frac = float("0." + m.group(4)) if m.group(4) else 0.0
    return h * 3600 + mm * 60 + ss + frac


_YEAR_RE = re.compile(r"(20[0-2]\d)")


def extract_year(text):
    m = _YEAR_RE.search(text or "")
    return int(m.group(1)) if m else None


def canonical_race_name(raw):
    """Light normalization: strip leading year, collapse spaces, unify punctuation.
    NOTE: this is a stub — a real race-name normalization TABLE is a Phase-1 task
    (see recon risks: 3 different 武嶺 races must NOT be merged)."""
    if not raw:
        return raw
    s = re.sub(r"\s+", " ", raw).strip()
    s = re.sub(r"^成績紀錄[-—]\s*", "", s)
    s = re.sub(r"^20[0-2]\d[\s​]*", "", s)  # strip leading year (incl. zero-width)
    s = s.replace("．", ".").replace("、", ".").replace("&", "&")
    return s.strip()


def race_key(raw):
    """A merge key for the same race listed under different categories / with
    punctuation or date-prefix variants. Strips year, leading date ranges
    (e.g. '1114-15'), all spaces and separators -> bare CJK/alnum string.
    NOTE: deliberately conservative — distinct races (太平山王 vs 陽明山王) stay distinct."""
    if not raw:
        return raw
    s = canonical_race_name(raw)
    s = re.sub(r"^\d{1,4}[-‑]\d{1,2}\s*", "", s)      # leading date range like 1114-15
    s = re.sub(r"[\s．.、&·,／/\-‑—_()（）]", "", s)      # drop spaces + separators
    s = s.replace("巿", "市")
    return s


def make_record(**kw):
    """Build a unified result record; fills missing keys with None and masks the name."""
    rec = {
        "source_platform": None, "source_url": None, "source_format": None,
        "race_name_raw": None, "race_name_canonical": None, "race_key": None, "year": None,
        "date": None, "race_type": None, "region": None,
        "result_label": None, "category_raw": None, "gender": None, "age_group": None,
        "rank_overall": None, "bib": None, "uci_id": None, "tsu_rider_id": None,
        "name_raw": None, "name_masked": None, "nationality": None, "team": None,
        "finish_time": None, "finish_seconds": None, "splits": None,
        "status": None, "laps": None,
        "scraped_at": None,
    }
    rec.update(kw)
    if rec["name_raw"] and not rec["name_masked"]:
        rec["name_masked"] = mask_name(rec["name_raw"])
    if rec["finish_time"] and rec["finish_seconds"] is None:
        rec["finish_seconds"] = time_to_seconds(rec["finish_time"])
    if rec["race_name_raw"] and not rec["race_name_canonical"]:
        rec["race_name_canonical"] = canonical_race_name(rec["race_name_raw"])
    if rec["race_name_raw"] and not rec["race_key"]:
        rec["race_key"] = race_key(rec["race_name_raw"])
    if rec["year"] is None and rec["race_name_raw"]:
        rec["year"] = extract_year(rec["race_name_raw"])
    return rec
