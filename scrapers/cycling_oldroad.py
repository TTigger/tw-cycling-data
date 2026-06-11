# -*- coding: utf-8 -*-
"""Recover cycling.org.tw OLD wide-table road results (民國98–102 / 2009–2013).

These pre-2014 national-championship files are podium-WIDE Excel:
  row: 組別 | 賽事 | 第一名…第N名 (names across columns)
  next row:        | 隊伍…           (teams,  index 0 = 1st place)
  next row: 時間…                     (times,  index 0 = 1st place; only top finishers timed)
We reshape each 3-row category block to long (one row per rider). Times are
HH:MM:SS:mmm. No UCI ids, few fields — marked source_format='xls-wide'.

Output: data/processed/cycling_oldroad.json (merge.py globs cycling_* so it
integrates automatically).
"""
import io
import json
import os
import re
import ssl
import sys
import urllib.request

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}
LIST_URL = "https://cycling.org.tw/%e4%b8%8b%e8%bc%89%e5%8d%80/"
XLS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "xls", "cycling")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(XLS_DIR, exist_ok=True)

CAT = re.compile(r"(男子|女子|男|女).{0,2}(菁英|青年|U23|少年|大師|公開|甲組|乙組)")
TIME = re.compile(r"^\d{1,2}:\d{2}:\d{2}")


def roc_year(text):
    m = re.search(r"(\d{2,3})\s*年", text or "")
    if m and 90 <= int(m.group(1)) <= 130:
        return int(m.group(1)) + 1911
    return common.extract_year(text)


def _time(cell):
    """'04:29:40:060' -> seconds. Last ':' is the millisecond separator."""
    s = str(cell).strip()
    if not TIME.match(s):
        return None, None
    parts = s.split(":")
    try:
        h, mm, ss = int(parts[0]), int(parts[1]), int(parts[2])
        frac = float("0." + parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0.0
        secs = h * 3600 + mm * 60 + ss + frac
        disp = f"{h}:{mm:02d}:{ss:02d}"
        return disp, secs
    except (ValueError, IndexError):
        return None, None


def _clean(x):
    s = str(x).strip()
    return None if s in ("", "nan", "None") else s


def parse_xls(path, year, race_name):
    rows, out = [], []
    try:
        xl = pd.ExcelFile(path)
        sheet = "score" if "score" in xl.sheet_names else xl.sheet_names[0]
        rows = xl.parse(sheet, header=None).values.tolist()
    except Exception as e:
        print(f"   ! read error {os.path.basename(path)}: {e}")
        return out
    i = 0
    while i < len(rows):
        c0 = _clean(rows[i][0]) or ""
        if CAT.search(c0):
            cat = c0
            event = _clean(rows[i][1])
            # names / teams / times all start at col2 (第一名), index 0 = 1st place
            names = [_clean(x) for x in rows[i][2:]]
            teams = [_clean(x) for x in rows[i + 1][2:]] if i + 1 < len(rows) else []
            times = [str(x).strip() for x in rows[i + 2][2:]] if i + 2 < len(rows) else []
            timed = any(TIME.match(x) for x in times)
            gender = "F" if cat.startswith("女") else ("M" if cat.startswith("男") else None)
            for idx, nm in enumerate(names):
                if not nm:
                    continue
                team = teams[idx] if idx < len(teams) else None
                disp, secs = (None, None)
                if timed and idx < len(times):
                    disp, secs = _time(times[idx])
                out.append(common.make_record(
                    source_platform="cycling.org.tw", source_url=path,
                    source_format="xls-wide", race_name_raw=f"{year} {race_name}",
                    year=year, race_type="road", result_label=event, category_raw=cat,
                    gender=gender, rank_overall=idx + 1, name_raw=nm, team=team,
                    finish_time=disp, finish_seconds=secs, scraped_at="2026-06-11"))
            i += 3
        else:
            i += 1
    return out


def listing():
    h = urllib.request.urlopen(urllib.request.Request(LIST_URL, headers=H), timeout=40, context=_CTX
                               ).read().decode("utf-8", "replace")
    items = re.findall(r'<a[^>]+href="([^"]+\.(?:xls|xlsx))"[^>]*>(.*?)</a>', h, re.S | re.I)
    out = []
    for href, txt in items:
        t = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", txt))
        if "公路" in t and "場地" not in t and "登山車" not in t:
            y = roc_year(t)
            if not y:                                    # fall back to upload-path year
                m = re.search(r"/(20\d{2})/", href)
                y = int(m.group(1)) if m else None
            out.append((y, t[:40], href))
    return out


def download(href):
    fn = re.sub(r"[^0-9A-Za-z._-]", "_", href.rsplit("/", 1)[-1])
    path = os.path.join(XLS_DIR, fn)
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return path
    try:
        d = urllib.request.urlopen(urllib.request.Request(href, headers=H), timeout=40, context=_CTX).read()
        if d[:4] in (b"\xd0\xcf\x11\xe0", b"PK\x03\x04"):
            open(path, "wb").write(d)
            return path
    except Exception as e:
        print(f"   ! download failed {href}: {e}")
    return None


def main():
    files = listing()
    print(f"road Excel files: {len(files)}")
    records = []
    for year, name, href in files:
        path = download(href)
        if not path:
            continue
        rs = parse_xls(path, year, name)
        print(f"  {year} {name[:30]:<30} rows={len(rs)}")
        records.extend(rs)
    out = os.path.join(OUT_DIR, "cycling_oldroad.json")
    with io.open(out, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    from collections import Counter
    print(f"\n=== records={len(records)} ===")
    print(f"  years: {dict(sorted(Counter(r['year'] for r in records).items(), key=lambda x: str(x[0])))}")
    print(f"  gender: {dict(Counter(r['gender'] for r in records))}")
    print(f"  with time: {sum(1 for r in records if r['finish_seconds'])}")
    print(f"  -> {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
