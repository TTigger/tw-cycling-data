# -*- coding: utf-8 -*-
"""
Layout-tolerant parser for cycling.org.tw (中華民國自由車協會) result-book PDFs.

cycling_crawl.parse_pdf only understands the 114年 layout. Older and school books
(2016-2026) use about a dozen other layouts, but nearly all of them print one
category per page with a row per rider:

    名次 號碼 姓名 [證號] 隊名 [出發時間 抵達時間 [加秒]] 成績 [時速 ...]

This module reads those rows line by line:
  * the rider's name is the first 2-4 character CJK token near the start;
  * the 成績 column is picked by counting the clock-time columns that come
    before 成績 in the page header (start / finish / checkpoint times);
  * stage-race pages print the stage time as "05m 56.69s" and use that.

Skipped on purpose: podium summaries (總成績表 / 成績總表), start lists, team
classifications, team time trials (shared team times) and points-only tables.
"""
import re

TIME = r"\d{1,3}:\d{2}(?::\d{2})?(?:\.\d{1,3})?(?![.\d]*\d{5})(?!\.)"   # not glued to an id
TIME_RE = re.compile(TIME)
STAGE_TIME_RE = re.compile(r"(?:(\d+)h\s*)?(\d{1,2})m\s*(\d{1,2}(?:\.\d+)?)s")
NAME_RE = re.compile(r"^[一-鿿]{2,4}$")
STATUS = {"DNF", "DNS", "OTL", "DSQ", "DQ", "LAP"}
# header columns that hold a clock / split time *before* 成績
PRE_TIME_COLS = ("出發時間", "抵達時間", "終點時間", "開始", "出發檢查", "檢查一", "檢查二")
SKIP_PAGE = re.compile(r"總成績|成績總表|出發名單|出賽名單|團體成績|團隊積分|團隊計時|團計|積分賽排名|Team\s*欄1|"
                       r"成績總和|計時賽成績|Intermediate|出發序|[(（]選拔[)）]")   # 選拔 = elite+U23 re-ranking


def _seconds(t):
    parts = t.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    except ValueError:
        return None
    return None


def _norm_time(t):
    """'000:42:10.00' -> '00:42:10.00'; '41:08.731' -> '00:41:08.731'."""
    secs = _seconds(t)
    if secs is None:
        return None, None
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    frac = t.split(".")[1] if "." in t else ""
    txt = f"{int(h):02d}:{int(m):02d}:{int(s):02d}" + (f".{frac}" if frac else "")
    return txt, round(secs, 3)


def find_header(lines):
    for ln in lines[:14]:
        if re.search(r"名次|Rank|排名", ln) and re.search(r"姓名|Name", ln):
            return ln
    return None


def result_time_index(header):
    """How many clock-time columns come before 成績 in this header."""
    if not header:
        return 0
    cut = header.find("成績")
    before = header[:cut] if cut >= 0 else ""
    return sum(1 for c in PRE_TIME_COLS if c in before)


def page_category(lines):
    """-> (category, event_label, gender) from the first few lines."""
    top = re.sub(r"\s+", "", "".join(lines[:5]))
    top = re.sub(r"^.*?(錦標賽|選拔賽|排名賽|錦賽)", "", top, count=1) or top
    cat = None
    for pat in (r"[男女]子(?:U23|[^\d/（(：:公]){0,8}?組", r"[男女]生\d+歲", r"(?:小|國|高)[一二三四五六中]?[男女]生組",
                r"國小[一二三四五六]?[男女](?:子組)?", r"[男女]子\d+歲組", r"國小[男女]生組",
                r"[男女]子(?:U23|菁英|青年|少年)"):
        m = re.search(pat, top)
        if m:
            cat = m.group(0)
            break
    if cat is None:
        m = re.search(r"組別(\S{2,6}?)(?:日期|$)", top)
        cat = m.group(1) if m else None
    ev = None
    m = re.search(r"(\d+(?:\.\d+)?(?:公里|km|K)[^\d：:公告]{0,8}?(?:計時賽?|公路賽|繞圈賽|公路計時))", top)
    if m:
        ev = m.group(1)
    elif "計時" in top:
        ev = "個人計時賽"
    elif "公路" in top:
        ev = "個人公路賽"
    stage = re.search(r"Stage(\d+)", top)
    if stage:
        dist = re.search(r"距離(\d+(?:\.\d+)?)km", top)
        ev = f"Stage {stage.group(1)}" + (f" {dist.group(1)}km" if dist else "")
    gender = None
    if cat:
        if "女" in cat:
            gender = "F"
        elif "男" in cat:
            gender = "M"
    return cat, ev, gender


def _clean_team(mid):
    """Drop ids, stray times, status words and overlapping-text junk from the team cell."""
    t = re.sub(r"^[A-Z]{2,}\s+\d{1,2}:\d{2}\.\S*\s*", "", mid.strip())   # 'HSIEH 15:46.3100…' overlay
    t = re.sub(r"^\d{1,2}:\d{2}\.\d\.?\s*", "", t)
    t = re.sub(r"\bR\d{7}\b|\d{9,11}", " ", t)
    t = re.sub(TIME, " ", t)
    t = re.sub(r"\b(?:%s)\b" % "|".join(STATUS), " ", t)
    t = re.sub(r"\s+\d{1,2}$", "", re.sub(r"\s+", " ", t).strip())
    return t.strip(" -") or None


def parse_line(line, n_before, rank_first=True):
    """One rider row -> dict or None."""
    toks = line.split()
    if len(toks) < 3:
        return None
    # name = first short CJK token within the first 3 positions
    ni = next((i for i, t in enumerate(toks[:3]) if NAME_RE.match(t)), None)
    if ni is None or ni == 0:
        return None
    lead = toks[:ni]
    status = None
    rank = None
    if len(lead) == 2:
        r, bib = lead
        if r.upper() in STATUS:
            status = r.upper()
        elif r.isdigit():
            rank = int(r)
        else:
            return None
    else:
        bib = lead[0]
        if rank_first and not any(t.upper() in STATUS for t in toks):
            return None        # unranked row under a 名次-first header: laps only, no result
    if not re.fullmatch(r"[A-Za-z]?\d{1,4}", bib):
        return None
    name = toks[ni]
    rest = " ".join(toks[ni + 1:])

    stage = STAGE_TIME_RE.search(rest)
    times = list(TIME_RE.finditer(rest))
    if stage:
        h = int(stage.group(1) or 0)
        secs = h * 3600 + int(stage.group(2)) * 60 + float(stage.group(3))
        ft = f"{h:02d}:{int(stage.group(2)):02d}:{stage.group(3).zfill(2) if '.' not in stage.group(3) else stage.group(3).zfill(5)}"
        tstart = times[0].start() if times else stage.start()
    elif len(times) > n_before:
        raw = times[n_before].group(0)
        ft, secs = _norm_time(raw)
        tstart = times[0].start()
    else:
        ft = secs = None
        tstart = len(rest)
    for t in toks[ni + 1:]:
        if t.upper() in STATUS:
            status = t.upper()
    if status:
        ft = secs = None
    if secs is not None and secs <= 0:          # 00:00:00.00 = no result recorded
        ft = secs = None
    if ft is None and not status:
        return None
    if rank is None and not status and stage is None:
        # bib-first layouts (105年) put the rank right after the time
        after = rest[times[n_before].end():].split() if len(times) > n_before else []
        if after and after[0].isdigit():
            rank = int(after[0])
    mid = rest[:tstart].strip()
    uci = None
    m = re.match(r"^((?:\d{3}\s?){3}\d{2}|\d{9,11}|R\d{6}|TPE\d{8}|[-x0])(?=\s|$|[^\d])\s*(.*)$", mid)
    if m:
        tok = m.group(1).replace(" ", "")
        uci = tok if re.fullmatch(r"\d{9,11}", tok) else None
        mid = m.group(2)
    else:
        # 英文姓 英文名 between name and id (108年 NRC layout)
        m = re.match(r"^([A-Z][A-Za-z\-']+(?:\s+[A-Z][a-z\-']+)+)\s*(\d{9,11})?\s*(.*)$", mid)
        if m:
            uci = m.group(2)
            mid = m.group(3)
    tail = re.search(r"\s(\d{9,11})$", mid)          # 114年: UCI id printed after the team
    if tail:
        uci = uci or tail.group(1)
        mid = mid[:tail.start()]
    # 105年 layout repeats the category before the team and the event after it
    mid = re.sub(r"^[男女]子\S{0,6}組\s+", "", mid.strip())
    mid = re.sub(r"\s+(個人計時賽|個人公路賽|公路賽|計時賽)$", "", mid)
    team = _clean_team(mid)
    if team and status and team.upper() in STATUS:
        team = None
    return {"rank": rank, "bib": bib, "name": name, "uci": uci, "team": team,
            "time": ft, "secs": secs, "status": status}


def _join_split_rows(lines):
    """Some books print the bib on its own line above 'rank name ...' (112年
    國手選拔 女子組). Glue those back into 'rank bib name ...'. Also fix the
    odd '04:19;43.02' typo."""
    out, i = [], 0
    lines = [re.sub(r"(\d);(\d)", r"\1:\2", ln.strip()) for ln in lines]
    while i < len(lines):
        ln = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        m = re.match(r"^(\d{1,3})\s+([\u4e00-\u9fff]{2,4}\s.*)$", nxt)
        if re.fullmatch(r"\d{1,4}", ln) and m:
            out.append(f"{m.group(1)} {ln} {m.group(2)}")
            i += 2
            continue
        out.append(ln)
        i += 1
    return out


def parse_pages(pages_lines):
    """pages_lines: list of line lists (one per page). Yields row dicts with
    category / event / gender attached."""
    cat = ev = gender = None
    n_before = 0
    rank_first = True
    header = None
    for lines in pages_lines:
        head_txt = "\n".join(lines[:6])
        if SKIP_PAGE.search(head_txt):
            header = None
            continue
        h = find_header(lines)
        c, e, g = page_category(lines)
        if h:
            header = h
            n_before = result_time_index(h)
            rank_first = bool(re.match(r"\s*(名次|排名|Rank)", h))
            if re.search(r"團隊排名|Team\s*欄", h):
                header = None
        if c:
            cat, ev, gender = c, e or ev, g
        elif h is None and header is None:
            continue
        if header is None:
            continue
        if ev and re.search(r"團隊|團計|團體", ev):
            continue
        for ln in _join_split_rows(lines):
            r = parse_line(ln, n_before, rank_first)
            if r:
                r.update(category=cat, event=ev, gender=gender)
                yield r


def parse_dedup(pages_lines):
    """parse_pages minus repeated rows: some books print a category twice
    (108年 '男子菁英組' and '男子菁英組(選拔)' share the same riders)."""
    seen, out = set(), []
    for r in parse_pages(pages_lines):
        key = (r["category"], r["event"], r["bib"], r["name"])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
