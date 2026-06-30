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
import html
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
     "url": "https://www.raceon.com.tw/zh-TW/blogs/news/143647", "parser": "raceon"},
    {"id": "biji2025", "name": "運動筆記 自行車賽事行事曆",
     "url": "https://running.biji.co/index.php?q=news&act=info&id=112100", "parser": "biji"},
    {"id": "ensage2026", "name": "ensage 2026 自行車&三鐵行事曆",
     "url": "https://blog.ensage.tours/blogs/cycling-event-calendar-2026/", "parser": "ensage"},
]

# triathlon / running — drop even if a date matches (ensage is cycling+tri mixed)
TRI_RUN = re.compile(r"鐵人|三項|馬拉松|路跑|超馬|超級馬拉松|游泳|越野跑|健行|健走|"
                     r"IRON|Triathlon|swimrun|duathlon|TRI\b", re.I)

_TAGS = re.compile(r"<[^>]+>")
_DATE = re.compile(r"^\d{1,2}[/.．]\d{1,2}")
_NOISE = re.compile(r"\d+(?:\.\d+)?\s*K\w*|春季|夏季|秋季|冬季|第[\w一二三四五六七八九十]{1,3}屆|"
                    r"第[\w一二三四五六七八九十]{1,3}站|Stage\s*\d+|年度系列|報名連結|&\w+;|挑戰組|經典組")


def _fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=40,
                                  context=_CTX).read().decode("utf-8", "replace")


def _clean(html):
    return re.sub(r"\s+", " ", _TAGS.sub("", html)).strip()


def parse_raceon(html):
    """RACE ON calendar: <li> items 'M.D｜<race name>：<dist>／報名連結'."""
    out = []
    for li in re.findall(r"<li[ >].*?</li>", html, re.S):
        t = _clean(li)
        if not _DATE.match(t):
            continue
        after = re.split(r"[｜|]", t, maxsplit=1)
        if len(after) < 2:
            continue
        name = re.split(r"[：:／/]", after[1], maxsplit=1)[0].strip()
        name = re.sub(r"&\w+;|報名連結", "", name).strip()
        if len(name) >= 4:
            out.append(name)
    return out


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
        return "Bravelog / tsu(96系列)"
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
# Last verified 2026-06-22 (see also SOURCES.md). Extend as races are triaged.
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
    # calendar mis-tag: these are 96聯賽 (96sporter.com), not 騎士協會, and not yet held
    ("仙山KOM", "OTHER_LEAGUE", "實為 96聯賽 苗栗站(96sporter.com),2026-10-18 尚未舉辦"),
    ("北進武嶺", "OTHER_LEAGUE", "實為 96聯賽 武嶺站(96sporter.com),2026-09-07 尚未舉辦"),
    # not yet held — re-check after the date; remove from this list once ingested
    ("無眠征途", "NOT_HELD", "2026-07-18 未辦;瘋系列限時挑戰,完賽後恐無總排(屆時查驗)"),
    ("小台灣縮時環島", "NOT_HELD", "2026-09-26 未辦;瘋系列 300K 限時挑戰,恐無總排"),
    ("TIS桃園台南", "NOT_HELD", "2026-10-31 未辦;往屆僅發完賽獎座/證書,恐無排名"),
    ("花蓮太平洋盃", "NOT_HELD", "2026-12-04~05 未辦;聯賽末站,辦完應有 cyclist.org.tw PDF 成績"),
    # --- ranked per-rider results EXIST but on a platform we don't scrape yet ---
    #     (verified 2026-06-29; future-source lead: add twbike.org/focusline parsing)
    #     NOTE: "TWB" must stay above the 瘋系列 "東三塔" NO_RANKING rule below.
    ("TWB", "BLOCKED", "台灣自行車協會 雙塔/三塔/北高360/騎福:成績在 twbike.org PDF + score.focusline(非可爬平台)"),
    ("輪霸西濱", "BLOCKED", "TBA 中華民國自行車協會 西濱挑戰:成績為 taiwanbike.org Google Sheets(非可爬平台)"),
    # --- 瘋系列 challenge: organizer states 無總排, timing on ATSport (blocked) ---
    ("中雙塔", "NO_RANKING", "瘋系列:無總排 + ATSport(封鎖)"),
    ("東三塔", "NO_RANKING", "瘋系列東三塔/東雙塔:無總排 + ATSport(封鎖)"),
    ("白毛山", "NO_RANKING", "瘋系列白毛山巔峰騎跡:完賽獎牌制,無總排 + ATSport"),
    ("瘋911", "NOT_HELD", "瘋系列 極限東征:2026-09-11 未辦;瘋系列恐無總排"),
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


def main():
    recs = list(common.iter_records(MASTER))  # RAM-frugal streaming parse
    master_cores = {core(r.get("race_name_canonical")) for r in recs if r.get("race_name_canonical")}
    master_cores.discard("")

    all_missing, seen, collected = [], set(), 0
    for cal in CALENDARS:
        try:
            html = _fetch(cal["url"])
        except Exception as e:
            print(f"  ! calendar fetch failed {cal['id']}: {e}")
            continue
        races = PARSERS[cal["parser"]](html)
        miss = []
        for nm in races:
            c = core(nm)
            if is_known(c, master_cores):
                continue
            if c in seen:
                continue
            seen.add(c)
            status, note = triage(nm)
            if status == "COLLECTED":
                collected += 1  # already in master under a canonical name — not a real gap
                continue
            rec = {"race": nm, "calendar": cal["id"], "guess_source": guess_source(nm)}
            if status:
                rec["status"] = status
                rec["note"] = note
            miss.append(rec)
        all_missing.extend(miss)
        print(f"  {cal['name']}: {len(races)} 賽事,{len(miss)} 缺漏")

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
        print(f"  ✗ {m['race'][:40]:<40} → {m['guess_source']}{tag}")
    if prev_names:  # skip on first-ever run (no baseline to diff against)
        print(f"\n=== 🆕 本次新增 {len(new_races)} 場(上次沒有,需查驗/triage)===")
        for m in new_races:
            print(f"  🆕 {m['race'][:40]:<40} → {m['guess_source']}")
    print(f"\n  -> {os.path.relpath(out)}")

    # Deploy-ready coverage transparency file for the /coverage page.
    from collections import Counter
    years = [r["year"] for r in recs if r.get("year")]
    ov_path = os.path.join(WEB_DIR, "overseas", "runnet_383993.json")
    overseas = len(json.load(open(ov_path, encoding="utf-8"))) if os.path.exists(ov_path) else 0
    coverage = {
        "summary": {
            "rows": len(recs),
            "races": len({r["race_key"] for r in recs if r.get("race_key")}),
            "by_source": dict(Counter(r["source_platform"] for r in recs).most_common()),
            "y0": min(years), "y1": max(years), "overseas": overseas,
            "calendars": [c["name"] for c in CALENDARS],
        },
        "gaps": all_missing,
    }
    cov = os.path.join(WEB_DIR, "coverage.json")
    json.dump(coverage, open(cov, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"  -> {os.path.relpath(cov)} (deploy)")


if __name__ == "__main__":
    main()
