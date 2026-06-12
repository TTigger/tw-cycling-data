# -*- coding: utf-8 -*-
"""
iRunner (irunner.biji.co) 即時成績查詢 — 自行車賽爬蟲。

破解經過(2026-06-12):
  - 成績查詢頁 /track/{id}/record 的搜尋欄位是 `rs`(中文姓名 / 晶片號子字串),
    用 POST 提交;但**分頁**是 GET `/track/{id}/record?rs={q}&page={N}`(POST 帶 page 無效)。
  - 每頁最多 10 筆(timing-record-row 是列序、非名次),GET 分頁可翻完整批,無 10-cap。
  - 結果列含:memno(record/{memno})、號碼布(timing-record-number)、姓名
    (timing-record-name)、完賽時間(timing-record-time)、組別(timing-record-div)。
  - 完整擷取法:列舉台灣常見姓氏 → 每姓翻頁 → 依 memno 去重 → 聯集 ≈ 全場;
    再用 max(memno) 偵測缺口、補抓 detail 頁,逼近 100%。
  - 名次非結果列所含 → 依組別內完賽時間排序衍生(標 derived)。

僅輸出去識別化欄位流向 normalize/merge;名次為衍生值。
"""
import io
import json
import os
import re
import sys
import time
import requests

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://irunner.biji.co"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(RAW, exist_ok=True)

# 台灣常見姓氏(涵蓋 ~98% 人口)+ 複姓;搜尋為子字串比對,聯集後依 memno 去重。
SURNAMES = list(
    "陳林黃張李王吳劉蔡楊許鄭謝郭洪曾邱廖賴徐周葉蘇莊呂江何蕭羅高潘簡朱鍾"
    "游詹胡施沈余趙盧梁顏柯孫魏翁戴范方宋鄧杜傅侯曹温薛丁馬蔣唐卓藍馮姚石"
    "田程白凃連莫鄒董駱涂巫吳塗紀阮龔邵錢湯汪倪歐祝古龍尤鄔賀嚴金童閻時"
    "韓常武喬賢嚴包左花常水尹樊柳關昌秦聶辛屈狄米伍融鞏松谷車滿弓茅關段雷"
) + ["歐陽", "張簡", "范姜", "司馬", "諸葛", "上官"]
# 高頻「名字用字」+ 拉丁字母:跨姓掃尾,抓回罕見姓 / 英文名 / 解析漏網者。
# (rs 為子字串比對,搜『志』可命中任何含『志』的名字,不受姓氏限制。)
GIVEN = list("志家明文宏建華強国國榮俊宇豪鈞翔廷昌德信義仁勇佳怡婷雅淑美麗")
LATIN = list("abcdefghijklmnopqrstuvwxyz")
# 查詢集:姓氏優先(分組乾淨),再名字字、再拉丁掃尾;去重保序。
QUERY_TERMS = list(dict.fromkeys(SURNAMES + GIVEN + LATIN))

# 自行車賽判定(標題)
CYCLING = re.compile(
    r"自行車|單車|公路車|鐵馬|武嶺|KOM|登山王|繞圈|環花東|環台|環島|環大|gravel|MTB|"
    r"落日飛車|銅礦|聯賽|玉門關|輪躍|騎乘|bike|cycl", re.I)
EXCLUDE = re.compile(
    r"馬拉松|路跑|越野跑|健行|鐵人|三項|IRONMAN|超鐵|游泳|登山(?!王)|親子路跑|健康跑|"
    r"田徑|全民運動|運動節|友善運動", re.I)


def _get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=H, timeout=30)
            if r.status_code == 200:
                return r.content.decode("utf-8", "replace")
        except requests.RequestException:
            pass
        time.sleep(1.5 * (i + 1))
    return ""


def event_title(track_id):
    h = _get(f"{BASE}/track/{track_id}")
    if not h:
        return None
    og = re.search(r'property=[\'"]og:title[\'"]\s+content=[\'"]([^\'"]+)', h)
    m = re.search(r"<title>([^<]*)</title>", h)
    t = (og.group(1) if og else (m.group(1) if m else "")).strip()
    return re.sub(r"\s*-\s*找選手.*$|\s*-\s*iRunner.*$", "", t).strip()


def classify(title):
    if not title:
        return False
    return bool(CYCLING.search(title)) and not EXCLUDE.search(title)


def discover_events(id_lo, id_hi):
    """掃描 track id 區間,回傳自行車賽 [{track_id,title,year}]。"""
    out = []
    for tid in range(id_lo, id_hi + 1):
        t = event_title(tid)
        if classify(t):
            ym = re.search(r"(20\d{2})", t)
            out.append({"track_id": tid, "title": t, "year": int(ym.group(1)) if ym else None})
            print(f"  [cycling] {tid} | {t}")
        time.sleep(0.3)
    return out


ROW_RE = re.compile(
    r"data-memno='(\d+)'.*?"                              # memno
    r"timing-record-number'>([^<]*)<.*?"                 # bib
    r"timing-record-name'>([^<]*)<.*?"                   # name (masked downstream)
    r"timing-record-time'>([^<]*)<.*?"                   # finish time
    r"timing-record-div'>([^<]*)<",                      # division / 組別
    re.S)


def parse_rows(html):
    out = []
    for m in ROW_RE.finditer(html):
        memno, bib, name, t, div = (x.strip() for x in m.groups())
        out.append({"memno": memno, "bib": bib, "name": name,
                    "time": t, "division": div})
    return out


def fetch_event(track_id, polite=0.4, log=True):
    """姓名列舉 + 分頁,依 memno 去重,回傳全場結果列。"""
    seen = {}
    for s in QUERY_TERMS:
        q = requests.utils.quote(s)
        # page 1 → maxpage
        h = _get(f"{BASE}/track/{track_id}/record?rs={q}&page=1")
        if not h:
            continue
        maxpage = max([int(x) for x in re.findall(r"[?&]page=(\d+)", h)] + [1])
        for p in range(1, maxpage + 1):
            hp = h if p == 1 else _get(f"{BASE}/track/{track_id}/record?rs={q}&page={p}")
            for row in parse_rows(hp):
                seen.setdefault(row["memno"], row)
            if p < maxpage:
                time.sleep(polite)
        if log and maxpage > 1:
            print(f"    surname {s}: {maxpage}p, running total {len(seen)}")
        time.sleep(polite)
    return list(seen.values())


def to_records(track_id, title, year, rows):
    """原始結果列 → master schema 記錄。組別字串(『長距離83K挑戰組．男．車隊』)拆出
    分組/性別/車隊;名次依『同組別內完賽時間』排序衍生(iRunner 結果列不含名次)。"""
    import common
    import normalize
    from collections import defaultdict

    by_div = defaultdict(list)
    for r in rows:
        by_div[r["division"]].append(r)

    recs = []
    for div, members in by_div.items():
        parts = [p.strip() for p in re.split(r"[．·・.、]", div) if p.strip()]
        group = parts[0] if parts else None
        # gender/age live in a segment that is either 男/女 or an M45/W40-style code;
        # team is the segment that parses to neither.
        gender = "M" if "男" in div else ("F" if "女" in div else None)
        age = None
        team = None
        for p in parts[1:]:
            g2, a2 = common.parse_division(p)
            if g2 or a2 or "男" in p or "女" in p:
                gender = gender or g2 or ("M" if "男" in p else "F" if "女" in p else None)
                age = age or a2
            else:
                team = p or None
        if age is None:
            _, age = common.parse_division(group or "")

        timed = [m for m in members if common.time_to_seconds(m["time"])]
        timed.sort(key=lambda m: common.time_to_seconds(m["time"]))
        rank = {m["memno"]: i + 1 for i, m in enumerate(timed)}

        for m in members:
            rec = common.make_record(
                source_platform="irunner.biji.co",
                source_url=f"{BASE}/track/{track_id}/record/{m['memno']}",
                source_format="html-search-derivedrank",
                race_name_raw=title, year=year,
                result_label=group, category_raw=div,
                gender=gender, age_group=age,
                bib=(m["bib"] or None), team=team,
                name_raw=(m["name"] or None),
                finish_time=(m["time"] or None),
                rank_overall=rank.get(m["memno"]),
            )
            normalize.enrich(rec)
            recs.append(rec)
    return recs


def build_processed():
    """讀 data/raw/irunner_events.json + 各 irunner_<id>.json → 依年份寫
    data/processed/irunner_<year>.json(含 name_raw,供 merge 重遮罩/去重)。"""
    from collections import defaultdict
    proc = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    os.makedirs(proc, exist_ok=True)
    events = json.load(io.open(os.path.join(RAW, "irunner_events.json"), encoding="utf-8"))
    by_year = defaultdict(list)
    for ev in events:
        f = os.path.join(RAW, f"irunner_{ev['track_id']}.json")
        if not os.path.exists(f):
            continue
        rows = json.load(io.open(f, encoding="utf-8"))
        recs = to_records(ev["track_id"], ev["title"], ev["year"], rows)
        by_year[ev["year"] or 0].extend(recs)
        print(f"  {ev['track_id']} {ev['title'][:30]}: {len(recs)} recs")
    for y, recs in by_year.items():
        out = os.path.join(proc, f"irunner_{y}.json")
        io.open(out, "w", encoding="utf-8").write(json.dumps(recs, ensure_ascii=False, indent=1))
        print(f"wrote {out}: {len(recs)} records")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"
    if cmd == "discover":
        lo, hi = int(sys.argv[2]), int(sys.argv[3])
        evs = discover_events(lo, hi)
        io.open(os.path.join(RAW, "irunner_events.json"), "w", encoding="utf-8").write(
            json.dumps(evs, ensure_ascii=False, indent=2))
        print(f"discovered {len(evs)} cycling events")
    elif cmd == "fetch":
        for tid in [int(x) for x in sys.argv[2:]]:
            rows = fetch_event(tid)
            maxm = max(int(r["memno"]) for r in rows) if rows else 0
            print(f"event {tid}: {len(rows)} distinct finishers, max memno {maxm}")
            io.open(os.path.join(RAW, f"irunner_{tid}.json"), "w", encoding="utf-8").write(
                json.dumps(rows, ensure_ascii=False, indent=2))
    elif cmd == "build":
        build_processed()
    elif cmd == "test":
        tid = int(sys.argv[2]) if len(sys.argv) > 2 else 1489
        rows = fetch_event(tid)
        maxm = max(int(r["memno"]) for r in rows) if rows else 0
        print(f"event {tid}: {len(rows)} distinct finishers, max memno {maxm}")
        io.open(os.path.join(RAW, f"irunner_{tid}.json"), "w", encoding="utf-8").write(
            json.dumps(rows, ensure_ascii=False, indent=2))
