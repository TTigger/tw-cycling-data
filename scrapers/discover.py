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


def main():
    recs = json.load(open(MASTER, encoding="utf-8"))
    master_cores = {core(r.get("race_name_canonical")) for r in recs if r.get("race_name_canonical")}
    master_cores.discard("")

    all_missing, seen = [], set()
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
            miss.append({"race": nm, "calendar": cal["id"], "guess_source": guess_source(nm)})
        all_missing.extend(miss)
        print(f"  {cal['name']}: {len(races)} 賽事,{len(miss)} 缺漏")

    out = os.path.join(OUT_DIR, "missing_races.json")
    json.dump(all_missing, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n=== 缺漏賽事 {len(all_missing)} 場(行事曆有、master 沒有)===")
    for m in all_missing:
        print(f"  ✗ {m['race'][:40]:<40} → {m['guess_source']}")
    print(f"\n  -> {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
