# -*- coding: utf-8 -*-
"""Gap discovery: find races that EXIST but we haven't scraped — without anyone
enumerating them by hand. We mine public race CALENDARS (which are listable),
normalize the race names, fuzzy-diff against the master dataset, and emit a
worklist of missing races + a guessed results source + scrapability.

Calendars are listable even when the results platforms aren't; this flips the
discovery problem from "enumerate every results page" to "diff against a calendar".

Output: data/processed/_discover/missing_races.json  (+ printed report)
Add new calendars to CALENDARS as they're found (keep SOURCES.md in sync).
"""
import datetime as _dt
import html
import html as html_mod  # parse_* shadow `html` with their argument
import json
import os
import re
import ssl
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
     "Accept-Language": "zh-TW"}
MASTER = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "master.public.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "_discover")
WEB_DIR = common.PUBLIC_DATA_DIR
os.makedirs(OUT_DIR, exist_ok=True)

# Public calendars to mine (listable). Each: id, name, url, parser key.
CALENDARS = [
    {"id": "raceon2026", "name": "RACE ON 2026 自行車行事曆",
     "url": "https://www.raceon.com.tw/zh-TW/blogs/news/143647", "parser": "raceon",
     "year": 2026},  # dated: enables the per-year NOT_INGESTED check
    {"id": "biji2025", "name": "運動筆記 自行車賽事行事曆",
     "url": "https://running.biji.co/index.php?q=news&act=info&id=112100", "parser": "biji"},
    {"id": "ensage2026", "name": "ensage 2026 自行車&三鐵行事曆",
     "url": "https://blog.ensage.tours/blogs/cycling-event-calendar-2026/", "parser": "ensage"},
]

# triathlon / running — drop even if a date matches (ensage is cycling+tri mixed)
TRI_RUN = re.compile(r"鐵人|三項|馬拉松|路跑|超馬|超級馬拉松|游泳|越野跑|健行|健走|"
                     r"IRON|Triathlon|swimrun|duathlon|TRI\b", re.I)

_TAGS = re.compile(r"<[^>]+>")
_NOISE = re.compile(r"\d+(?:\.\d+)?\s*K\w*|春季|夏季|秋季|冬季|第[\w一二三四五六七八九十]{1,3}屆|"
                    r"第[\w一二三四五六七八九十]{1,3}站|Stage\s*\d+|年度系列|報名連結|&\w+;|挑戰組|經典組")


def _fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=40,
                                  context=_CTX).read().decode("utf-8", "replace")


def _clean(html):
    return re.sub(r"\s+", " ", _TAGS.sub("", html)).strip()


def parse_raceon_dated(html, year):
    """RACE ON calendar: <li> items 'M.D｜<race name>：<dist>／報名連結'.
    Returns [(name, date)] where date is the event's first day. The list runs in
    date order, so a month that goes backwards (12 → 1) means the next year."""
    out, prev_month = [], 0
    for li in re.findall(r"<li[ >].*?</li>", html, re.S):
        t = html_mod.unescape(_clean(li))  # decode first: stripping &Eacute; turned L’Étape into Ltape
        m = re.match(r"(\d{1,2})[/.．](\d{1,2})", t)
        if not m:
            continue
        month, day = int(m.group(1)), int(m.group(2))
        if month < prev_month:
            year += 1
        prev_month = month
        after = re.split(r"[｜|]", t, maxsplit=1)
        if len(after) < 2:
            continue
        name = re.split(r"[：:／/]", after[1], maxsplit=1)[0].strip()
        name = re.sub(r"&\w+;|報名連結", "", name).strip()
        if len(name) >= 4:
            try:
                out.append((name, _dt.date(year, month, day)))
            except ValueError:
                out.append((name, None))
    return out


def parse_raceon(html):
    return [n for n, _ in parse_raceon_dated(html, 2026)]


def parse_biji(html_doc):
    """運動筆記 article: race lines are 'M.D｜<name>：<dist>' but HTML-entity
    encoded (｜ = &#65372;). Decode entities, then line-extract by date｜name."""
    text = html.unescape(re.sub(r"<br\s*/?>", "\n", html_doc, flags=re.I))
    text = re.sub(r"<[^>]+>", "\n", text)
    out = []
    for ln in text.splitlines():
        t = ln.strip()
        if not re.match(r"\d{1,2}[.／/]\d{1,2}\s*[｜|]", t):
            continue
        after = re.split(r"[｜|]", t, maxsplit=1)
        if len(after) < 2:
            continue
        name = re.split(r"[：:／/]", after[1], maxsplit=1)[0].strip()
        name = re.sub(r"&\w+;|報名連結", "", name).strip()
        if len(name) >= 4:
            out.append(name)
    return out


def parse_ensage(html_doc):
    """ensage blog calendar: <tr> rows 'M/D<race name>' (cycling + triathlon
    mixed). Drop triathlon/running; keep cycling-ish race names."""
    out = []
    for tr in re.findall(r"<tr[ >].*?</tr>", html_doc, re.S):
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", tr))).strip()
        m = re.match(r"\d{1,2}/\d{1,2}\s*(.+)", t)
        if not m:
            continue
        name = m.group(1).strip()
        if TRI_RUN.search(name):
            continue
        # drop ensage's own tour/shuttle/overseas products (not competitive races)
        if name.startswith("ensage") or re.search(
                r"保母車|接駁|順騎|約騎|賞櫻|神掌|trip|東南旅遊|佐渡|新潟|SADO|海外", name, re.I):
            continue
        if not re.search(r"賽|挑戰|盃|車|KOM|繞圈|武嶺|環|登山|騎|P字|塔|gravel|Gravel", name):
            continue
        name = re.sub(r"【[^】]*】|&\w+;|^\W+", "", name).strip()
        if len(name) >= 4:
            out.append(name[:48])
    return out


PARSERS = {"raceon": parse_raceon, "biji": parse_biji, "ensage": parse_ensage}


def core(name):
    """Comparable core key: strip year/season/distance/edition/punctuation."""
    s = _NOISE.sub("", name or "")
    s = common.race_key(s) or s
    return re.sub(r"[\s2026202520242023]", "", s)


def _overlap(a, b):
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def is_known(cal_core, master_cores):
    for mc in master_cores:
        if not cal_core or not mc:
            continue
        if cal_core in mc or mc in cal_core or _overlap(cal_core, mc) >= 0.6:
            return True
    return False


def guess_source(name):
    if re.search(r"96聯賽|96Cycling|96Heroes", name):
        return "96sporter PDF(2026起) / Bravelog / tsu(96系列)"
    if re.search(r"全國|錦標賽|國手|選拔|自由車", name):
        return "cycling.org.tw / tsu"
    if re.search(r"縣長盃|市長盃|繞圈|計時|越野|大專", name):
        return "tsu.com.tw"
    if re.search(r"Gravel|gravel|礫石|Dirty|輪耀|林道", name):
        return "FB / 主辦頁(可能需 OCR)"
    if re.search(r"崇越|武嶺|登山王|KOM|塔塔加|挑戰賽|盃|經典|落日|銅礦|環", name):
        return "Bravelog / cyclist / tsu(查驗)"
    return "未知(需查主辦頁)"


# Curated triage for calendar races we've already investigated, so each run shows
# WHY a race isn't ingested instead of re-surfacing it as a generic 查驗 candidate
# every week. Match = substring in the calendar race name (first hit wins).
#   COLLECTED    — already in master under a different canonical name (discover
#                  fuzzy-match false positive); dropped from the gap list.
#   NO_RANKING   — held, but organizer publishes no per-rider ranking (challenge/
#                  tour ride, or 瘋系列 "無總排" + ATSport chip timing).
#   OTHER_LEAGUE — calendar mis-tags it; actually belongs to another series.
#   NOT_HELD     — event date still in the future; re-check after it runs.
#   HELD_UNCHECKED — date has passed; nobody has checked yet whether results exist.
#   BLOCKED      — ranked results exist, but on a platform we don't scrape yet.
# Computed (not curated): NOT_INGESTED — dated calendar race already held this
#   year, earlier editions are in master, but this year's edition is not.
# Last verified 2026-06-22; dates refreshed 2026-11-02 (see also SOURCES.md).
KNOWN_TRIAGE = [
    # already in master under our canonical name (verified by row counts 2026-06-22)
    ("陽明山登山王", "COLLECTED", "= 陽明山王公路賽(cyclist.org.tw, 2026 已收 665 筆)"),
    ("春季登山王之路", "COLLECTED", "= 臺灣KOM登山王之路-春季(cyclist.org.tw, 2026 已收)"),
    ("環花東", "COLLECTED", "= 環花東國際自行車賽(cyclist.org.tw, 2026 已收 580 筆)"),
    ("太平山", "COLLECTED", "= 太平山王公路賽(cyclist.org.tw, 2026 已收)"),
    # held but no scrapeable per-rider ranking
    ("八卦山傳奇", "NO_RANKING", "瘋系列：主辦明示「所有成績沒有總排」+ ATSport 計時"),
    ("谷關雪見", "NO_RANKING", "瘋系列：無總排 + ATSport(封鎖平台)"),
    ("環海岸山脈", "NO_RANKING", "挑戰/團騎,無逐筆排名"),
    ("環湖饗宴", "NO_RANKING", "明德競技 樂遊騎跑,休閒性質無排名(ctrun.com.tw)"),
    ("西進武嶺圓夢團", "NO_RANKING", "aYa 嚮導團騎,非計時賽"),
    # calendar mis-tag: these are 96聯賽 (96sporter.com), not 騎士協會. Since 2026 the
    # 96 league posts results only as PDF (scrapers/sporter96_pdf.py worklist).
    ("北進武嶺", "COLLECTED", "= 96聯賽武嶺站(96sporter PDF, 2026 已收 294 筆)"),
    ("仙山KOM", "HELD_UNCHECKED", "實為 96聯賽 苗栗站,2026-10-18 已辦;成績 PDF 尚未在 96sporter.com 公布,公布後加入 data/raw/sporter96_pdfs.json"),
    # HELD_UNCHECKED — date has passed; check whether a per-rider ranking was published
    ("無眠征途", "HELD_UNCHECKED", "2026-07-18 已辦;瘋系列限時挑戰,恐無總排,待查驗"),
    ("小台灣縮時環島", "HELD_UNCHECKED", "2026-09-26 已辦;瘋系列 300K 限時挑戰,恐無總排,待查驗"),
    ("TIS桃園台南", "HELD_UNCHECKED", "2026-10-31 已辦;往屆僅發完賽獎座/證書,恐無排名,待查驗"),
    ("騎遊茂林", "HELD_UNCHECKED", "2026-10-24 已辦;挑戰70K/騎玩40K 活動型,待查是否有排名"),
    # not yet held — re-check after the date; remove from this list once ingested
    ("花蓮太平洋盃", "NOT_HELD", "2026-12-04~05 未辦;聯賽末站,辦完應有 cyclist.org.tw PDF 成績"),
    ("環騎5COOL", "NOT_HELD", "2026-11-07 未辦;新出現於 RACE ON,辦完查驗"),
    ("鯉魚潭山光水色", "NOT_HELD", "2026-12-12 未辦;限時挑戰(菁英5h/挑戰7h),辦完查驗"),
    ("超級騎士挑戰", "NOT_HELD", "2027-01-01~02 未辦;瘋系列,恐無總排"),
    # --- ranked per-rider results EXIST but on a platform we don't scrape yet ---
    #     (verified 2026-06-29; future-source lead: add twbike.org/focusline parsing)
    #     NOTE: "TWB" must stay above the 瘋系列 "東三塔" NO_RANKING rule below.
    ("TWB", "BLOCKED", "台灣自行車協會 雙塔/三塔/北高360/騎福:成績在 twbike.org PDF + score.focusline(非可爬平台)"),
    ("輪霸西濱", "BLOCKED", "TBA 中華民國自行車協會 西濱挑戰:成績為 taiwanbike.org Google Sheets(非可爬平台)"),
    # --- 瘋系列 challenge: organizer states 無總排, timing on ATSport (blocked) ---
    ("中雙塔", "NO_RANKING", "瘋系列:無總排 + ATSport(封鎖)"),
    ("東三塔", "NO_RANKING", "瘋系列東三塔/東雙塔:無總排 + ATSport(封鎖)"),
    ("白毛山", "NO_RANKING", "瘋系列白毛山巔峰騎跡:完賽獎牌制,無總排 + ATSport"),
    ("瘋911", "HELD_UNCHECKED", "瘋系列 極限東征:2026-09-11 已辦;瘋系列恐無總排,待查驗"),
    # --- leisure / guided-tour / festival rides: no per-rider ranking (verified 2026-06-29) ---
    ("樂遊苗栗", "NO_RANKING", "ensage 樂遊苗栗一騎跑:嚮導團騎/集點健康活動,無排名"),
    ("Light One Bike", "NO_RANKING", "低碳慢遊生態團騎,明示非競賽,無排名(報名在伊貝特)"),
    ("騎輪節", "NO_RANKING", "時代騎輪節 Wheels Ride Festival:明示非競賽,計時僅供參考"),
    ("萬眾騎", "NO_RANKING", "萬眾騎BIKE:媽祖遶境群眾騎乘,非競賽"),
    ("探索汐鴿", "NO_RANKING", "汐鴿休閒認證路線社交團騎,無排名"),
    ("中央山脈極致挑戰", "NO_RANKING", "多日極致挑戰:僅完賽英雄榜/關門時間,無排名"),
    ("南投旅遊百", "NO_RANKING", "南投旅遊百K:休閒小鎮漫遊,無排名"),
    ("屏東來義", "NO_RANKING", "之心山嵐單車行:休閒團騎,查無成績頁"),
    ("關子嶺鐵馬行", "NO_RANKING", "友誼萬歲 鐵馬行:休閒團騎(lohasnet),無排名"),
    ("雲林單車遊", "NO_RANKING", "梅好騎跡咖啡探索:休閒團騎;2025 停辦"),
    ("雙潭騎跡", "NO_RANKING", "單車嘉義休閒遊:免費計時查詢「不排名」"),
]


def triage(name):
    """Return (status, note) if a curated verdict matches this race, else (None, None)."""
    for sub, status, note in KNOWN_TRIAGE:
        if sub in name:
            return status, note
    return None, None


KNOWN_RACES = os.path.join(os.path.dirname(__file__), "..", "data", "known_races.json")


def known_race_gaps(by_year, seen_this_year, this_year):
    """Gaps from data/known_races.json, the hand-kept list of races we know exist
    but can't collect. Calendars only list upcoming races and forget them after,
    so this list is what keeps a missing race-year on record.
    Returns (gaps, done): entries now in master (done) are reported, not shown."""
    if not os.path.exists(KNOWN_RACES):
        return [], []
    gaps, done = [], []
    for k in json.load(open(KNOWN_RACES, encoding="utf-8"))["races"]:
        c, y = core(k["race"]), k.get("year")
        # strict name containment: years_known's fuzzy overlap lumps stations
        # of one series together (俱樂部聯賽 第2站 vs 第3站)
        if y and k["status"] != "EXCLUDED" and any(
                y in ys and (c in mc or mc in c) for mc, ys in by_year.items() if mc):
            done.append(k)
            continue
        if y == this_year and c in seen_this_year:
            continue  # a calendar already reports it
        g = {"race": k["race"], "calendar": "known_races", "status": k["status"],
             "guess_source": (k.get("last_seen") or {}).get("source") or "",
             "note": k.get("note", ""), "year": y}
        if k.get("date"):
            g["date"] = k["date"]
        if k.get("links"):
            g["url"] = k["links"][0]
        gaps.append(g)
    return gaps, done


RACES_JSON = os.path.join(WEB_DIR, "races.json")


def load_master():
    """(records, summary_from_master). master.public.json is gitignored and only
    lives on the machine that ran merge.py. Without it, fall back to the deployed
    races.json (one row per race-year): good enough for the name/year diff, but
    row counts are wrong, so the caller keeps the previous coverage summary."""
    if os.path.exists(MASTER):
        return list(common.iter_records(MASTER)), True  # RAM-frugal streaming parse
    print(f"  ! {os.path.relpath(MASTER)} 不存在 → 改用 races.json 比對(摘要沿用上一版 coverage.json)")
    races = json.load(open(RACES_JSON, encoding="utf-8"))
    return [{"race_name_canonical": r["rn"], "race_key": r["rk"], "year": r["y"]} for r in races], False


def cores_by_year(recs):
    out = {}
    for r in recs:
        c = core(r.get("race_name_canonical"))
        if c:
            out.setdefault(c, set()).add(r.get("year"))
    return out


def years_known(cal_core, by_year):
    """Years in master for the BEST-matching race only. is_known()'s any-match rule
    is fine for "have we ever seen this race", but for "do we have THIS year" it
    lumps e.g. all 96聯賽 stops together, hiding a missing stop behind another
    stop's current-year results. Substring = score 1; ties are unioned."""
    best, ys = 0.6, set()
    for mc, years in by_year.items():
        if not cal_core or not mc:
            continue
        sc = 1.0 if (cal_core in mc or mc in cal_core) else _overlap(cal_core, mc)
        if sc > best:
            best, ys = sc, set(years)
        elif sc == best and ys:
            ys |= years
    return ys


def not_ingested(name, date, today, by_year):
    """A held, dated race whose earlier editions we have but this year's we don't."""
    if date is None or date >= today:
        return None
    ys = years_known(core(name), by_year)
    if not ys or date.year in ys:
        return None
    return {"race": name, "date": date.isoformat(), "guess_source": guess_source(name),
            "status": "NOT_INGESTED",
            "note": f"{date.isoformat()} 已辦;往年已收錄({max(ys)}),今年成績尚未 ingest"}


def carry_forward(prev_gaps, cal_id):
    """Gaps from the last successful run for a calendar we couldn't fetch now —
    so a site outage doesn't silently wipe its gaps off the /coverage page.
    Triage is re-applied so curated verdict updates still land."""
    out = []
    for g in prev_gaps:
        if g.get("calendar") != cal_id:
            continue
        g = {k: v for k, v in g.items() if k not in ("status", "note")}
        status, note = triage(g["race"])
        if status == "COLLECTED":
            continue
        if status:
            g["status"], g["note"] = status, note
        g["stale"] = True
        out.append(g)
    return out


def main():
    today = _dt.date.today()
    recs, summary_from_master = load_master()
    master_cores = {core(r.get("race_name_canonical")) for r in recs if r.get("race_name_canonical")}
    master_cores.discard("")
    by_year = cores_by_year(recs)

    cov = os.path.join(WEB_DIR, "coverage.json")
    prev_cov = {}
    if os.path.exists(cov):
        try:
            prev_cov = json.load(open(cov, encoding="utf-8"))
        except Exception:
            pass

    all_missing, seen, collected, failed = [], set(), 0, []
    for cal in CALENDARS:
        try:
            html = _fetch(cal["url"])
        except Exception as e:
            print(f"  ! calendar fetch failed {cal['id']}: {e}")
            kept = carry_forward(prev_cov.get("gaps", []), cal["id"])
            for g in kept:
                seen.add(core(g["race"]))
            all_missing.extend(kept)
            failed.append(cal["id"])
            print(f"    → 沿用上次的 {len(kept)} 筆缺漏(標記 stale)")
            continue
        if cal["parser"] == "raceon":
            dated = parse_raceon_dated(html, cal["year"])
        else:
            dated = [(n, None) for n in PARSERS[cal["parser"]](html)]
        miss = []
        for nm, date in dated:
            c = core(nm)
            if c in seen:
                continue
            if is_known(c, master_cores):
                rec = not_ingested(nm, date, today, by_year)
                if rec and triage(nm)[0] not in ("NO_RANKING", "COLLECTED"):
                    seen.add(c)
                    rec["calendar"] = cal["id"]
                    miss.append(rec)
                continue
            seen.add(c)
            status, note = triage(nm)
            if status == "COLLECTED":
                collected += 1  # already in master under a canonical name — not a real gap
                continue
            rec = {"race": nm, "calendar": cal["id"], "guess_source": guess_source(nm)}
            if date:
                rec["date"] = date.isoformat()
            if status:
                rec["status"] = status
                rec["note"] = note
            miss.append(rec)
        all_missing.extend(miss)
        print(f"  {cal['name']}: {len(dated)} 賽事,{len(miss)} 缺漏")

    known, done = known_race_gaps(by_year, seen, today.year)
    all_missing.extend(known)
    print(f"  data/known_races.json: {len(known)} 場已知未收錄")
    for k in done:
        print(f"  ✓ 已收錄,可從 known_races.json 刪除:{k['year']} {k['race']}")

    out = os.path.join(OUT_DIR, "missing_races.json")
    # Diff against the previous run so the radar can alert only on CHANGE: a race
    # that appears now but wasn't here last time is genuinely new and needs triage.
    prev_names = set()
    if os.path.exists(out):
        try:
            prev_names = {p["race"] for p in json.load(open(out, encoding="utf-8"))}
        except Exception:
            pass
    new_races = [m for m in all_missing if m["race"] not in prev_names]

    json.dump(all_missing, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n=== 缺漏賽事 {len(all_missing)} 場(行事曆有、master 沒有;"
          f"另 {collected} 場已收錄,自動略過)===")
    for m in all_missing:
        tag = f" [{m['status']}]" if m.get("status") else ""
        tag += " (stale)" if m.get("stale") else ""
        print(f"  ✗ {m['race'][:40]:<40} → {m['guess_source']}{tag}")
    if prev_names:  # skip on first-ever run (no baseline to diff against)
        print(f"\n=== 🆕 本次新增 {len(new_races)} 場(上次沒有,需查驗/triage)===")
        for m in new_races:
            print(f"  🆕 {m['race'][:40]:<40} → {m['guess_source']}")
    print(f"\n  -> {os.path.relpath(out)}")

    # Deploy-ready coverage transparency file for the /coverage page.
    from collections import Counter
    if summary_from_master:
        years = [r["year"] for r in recs if r.get("year")]
        ov_path = os.path.join(WEB_DIR, "overseas", "runnet_383993.json")
        overseas = len(json.load(open(ov_path, encoding="utf-8"))) if os.path.exists(ov_path) else 0
        summary = {
            "rows": len(recs),
            "races": len({r["race_key"] for r in recs if r.get("race_key")}),
            "by_source": dict(Counter(r["source_platform"] for r in recs).most_common()),
            "y0": min(years), "y1": max(years), "overseas": overseas,
        }
    else:
        summary = {k: v for k, v in prev_cov.get("summary", {}).items()
                   if k not in ("calendars", "checked", "failed_calendars")}
    summary["calendars"] = [c["name"] for c in CALENDARS]
    summary["checked"] = today.isoformat()
    if failed:
        summary["failed_calendars"] = failed
    coverage = {"summary": summary, "gaps": all_missing}
    json.dump(coverage, open(cov, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"  -> {os.path.relpath(cov)} (deploy)")


if __name__ == "__main__":
    main()
