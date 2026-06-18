# -*- coding: utf-8 -*-
"""
Cross-source normalization tables (recon-flagged Phase-1 task):
  - race_class():  the awarded-group bucket (競賽/市民/挑戰/青少年/團體/電輔車/認證)
  - series_of():   group races into series for analysis (96聯賽 / 登山大滿貫 / 臺灣自行車聯賽 …)
  - age_band():    coarse decade band unifying the heterogeneous raw age_group
  - enrich():      add race_class + series + age_band to a unified record (in place)

These are CURATED keyword tables built from the real 2024-26 race/category values.
IMPORTANT (recon): distinct races must NOT be merged — the three "武嶺" races
(TIS崇越盃 / 96聯賽 / NeverStop) are different events; series labels group them
for browsing but each keeps its own race_key. KOM登山王之路 ≠ KOM太平洋經典賽 ≠ KOM登山王挑戰.
"""
import re


# ---- curated canonical race_key map (reviewed 2026-06-16) ------------------
# Collapse the SAME annual event that source naming split across editions by
# 屆次 / HTML-entity / English transliteration tail / sponsor word-order. Each
# member keeps its own year, so merging only re-keys (no row loss) and lets the
# cross-year / DNA / series / H2H views see one race across years.
# DELIBERATELY NOT merged: the three 武嶺 by organizer (崇越 ≠ NeverStop ≠ 96聯賽),
# KOM 春季/夏季, Day1/Day2 stages, 崇越武嶺 六月/九月 rounds, GravelFundo stages/heats.
RACE_KEY_CANONICAL = {
    '第13屆美利達‧兆豐銀行彰化經典百K': '彰化經典百K',
    '第14屆兆豐銀行‧美利達彰化經典百KChanghuaClassic100單車自我挑戰': '彰化經典百K',
    '第15屆兆豐銀行‧美利達彰化經典百KChanghuaClassic100單車自我挑戰': '彰化經典百K',
    '第16屆兆豐銀行‧美利達彰化經典百KChanghuaClassic100單車自我挑戰': '彰化經典百K',
    '美利達盃amp;單車嘉年華': '美利達盃單車嘉年華',
    '美利達盃單車嘉年華': '美利達盃單車嘉年華',
    '輪躍台南單車嘉年華': '輪躍台南單車嘉年華',
    '輪躍台南單車嘉年華TainanCyclingFestival': '輪躍台南單車嘉年華',
    '瘋系列環台賽西部段': '瘋系列環台賽-西部段',
    '瘋系列第二屆環台賽西部段': '瘋系列環台賽-西部段',
    '瘋系列環台賽蘇花段': '瘋系列環台賽-蘇花段',
    '瘋系列第二屆環台賽蘇花段': '瘋系列環台賽-蘇花段',
    '瘋系列環台賽東部段': '瘋系列環台賽-東部段',
    '瘋系列第二屆環台賽東部段': '瘋系列環台賽-東部段',
    'TIS崇越盃武嶺自行車挑戰賽': '崇越盃武嶺挑戰賽',
    '崇越盃武嶺自行車挑戰賽': '崇越盃武嶺挑戰賽',

    # ---- review batch (per-group human sign-off 2026-06-18) ------------------
    # candidate table from suggest_race_merges.py; only the approved groups added.
    # 扶輪盃陽明山登山王: the 2021 edition dropped the 挑戰 tail — same event.
    '扶輪盃陽明山自行車登山王': '扶輪盃陽明山自行車登山王挑戰',
    # 桃園市運動會 市長盃: 分齡組 is an age-category split of one championship.
    # (96聯賽 挑戰組/競賽組 NOT merged — different courses/field, kept distinct.)
    '115年桃園市運動會市長盃自由車錦標賽暨國手積分賽分齡組': '115年桃園市運動會-市長盃自由車錦標賽暨國手積分賽',
    '115年桃園市運動會市長盃自由車錦標賽暨國手積分賽': '115年桃園市運動會-市長盃自由車錦標賽暨國手積分賽',
    # GravelFundo: collapse Stage no. + qualifying heats (S1/S2/S3) into one race
    # per 地點+賽別 across years (heats become rows within the race). 年終站
    # (already cross-year) and 頂成ZIPP盃 (different organizer) left untouched.
    'GravelFundoStage1台南玉井站【GravelRace礫石車賽】': 'GravelFundo-台南玉井-礫石車賽',
    'GravelFundoStage2台南玉井站【GravelRace礫石車賽】': 'GravelFundo-台南玉井-礫石車賽',
    'GravelFundoStage1台南玉井站【MTBXCORace越野林道賽】': 'GravelFundo-台南玉井-越野林道賽',
    'GravelFundoStage2台南玉井站【MTBXCORace越野林道賽】': 'GravelFundo-台南玉井-越野林道賽',
    'GravelFundoStage1台南玉井站【MiniEnduroRace迷你全地形賽】': 'GravelFundo-台南玉井-迷你全地形賽',
    'GravelFundoStage1台南玉井站【MiniEnduroRace迷你全地形賽】S1': 'GravelFundo-台南玉井-迷你全地形賽',
    'GravelFundoStage1台南玉井站【MiniEnduroRace迷你全地形賽】S2': 'GravelFundo-台南玉井-迷你全地形賽',
    'GravelFundoStage2台南玉井站【MiniEnduroRace迷你全地形賽】': 'GravelFundo-台南玉井-迷你全地形賽',
    'GravelFundoStage2台南玉井站【MiniEnduroRace迷你全地形賽】S1': 'GravelFundo-台南玉井-迷你全地形賽',
    'GravelFundoStage2台南玉井站【MiniEnduroRace迷你全地形賽】S2': 'GravelFundo-台南玉井-迷你全地形賽',
    'GravelFundoStage2台南玉井站【MiniEnduroRace迷你全地形賽】S3': 'GravelFundo-台南玉井-迷你全地形賽',
    'GravelFundoStage1彰化員林站【GravelRace礫石車賽】': 'GravelFundo-彰化員林-礫石車賽',
    'GravelFundoStage2彰化員林站【GravelRace礫石車賽】': 'GravelFundo-彰化員林-礫石車賽',
    'GravelFundoStage1彰化員林站【MTBXCORace越野林道賽】': 'GravelFundo-彰化員林-越野林道賽',
    'GravelFundoStage2彰化員林站【MTBXCORace越野林道賽】': 'GravelFundo-彰化員林-越野林道賽',
    'GravelFundo年度系列Stage1台中老外林道站【MiniEnduro迷你全地形賽】': 'GravelFundo-台中老外林道-迷你全地形賽',
    'GravelFundo年度系列Stage1台中老外林道站【MiniEnduro迷你全地形賽S1】': 'GravelFundo-台中老外林道-迷你全地形賽',
    'GravelFundo年度系列Stage1台中老外林道站【MiniEnduro迷你全地形賽S2】': 'GravelFundo-台中老外林道-迷你全地形賽',
}


# ---- race_class: the awarded competition bucket ----------------------------
def race_class(result_label=None, category_raw=None):
    lab = result_label or ""
    cat = category_raw or ""
    if "電輔" in cat or "電動輔助" in cat:
        return "電輔車"
    if "挑戰" in lab or cat in ("挑戰組", "挑戰") or "挑戰組" in cat:
        return "挑戰"
    if "國中" in lab or "高中" in lab or re.match(r"^[Uu]\d", cat):
        return "青少年"
    if "團隊" in lab or "團體" in lab or "TTT" in lab.upper():
        return "團體計時"
    if "競賽" in lab or "菁英" in lab or "精英" in lab:
        return "競賽"
    if "經典" in lab or "經典組" in cat:
        return "市民經典"
    if "市民" in lab or "巿民" in lab or "一般" in cat or "一般" in lab:
        return "市民"
    if "認證" in lab or "完賽" in lab:
        return "認證"
    # age-group codes: M35 / W30 and the road-prefixed RM35 / RW30 (same convention
    # as gender_from_category — the R prefix used to fall through to 未分類).
    if re.match(r"^[Rr]?[MWＭＷ]\d", cat) or cat == "MASTER" or "分齡" in lab:
        return "分齡"
    if "女子" in cat:
        return "女子"
    return "未分類"


# ---- series: group races for browsing (keyword -> series label) -------------
# order matters: first match wins
_SERIES = [
    (r"登山大滿貫|大滿貫", "台灣登山大滿貫(雪巴)"),
    (r"96聯賽|96CyclingRace|96Heroes|96 ", "96聯賽"),
    (r"瘋系列.*環台|瘋系列", "瘋系列環台賽"),
    (r"崇越盃|TIS|石羅佛|石門環湖|羅馬公路|佛陀KOM", "TIS崇越盃系列"),
    (r"KOM太平洋經典|太平洋經典賽", "臺灣KOM太平洋經典賽"),
    (r"登山王之路", "臺灣KOM登山王之路"),
    (r"登山王挑戰|Taiwan KOM Challenge", "臺灣KOM登山王挑戰"),
    (r"太平山王|陽明山王|臺灣自行車聯賽|台灣自行車聯賽", "臺灣自行車聯賽(TCL)"),
    (r"環花東|花東縱谷|East Taiwan", "環花東國際自行車賽"),
    (r"花蓮太平洋盃|太平洋盃", "花蓮太平洋盃"),
    (r"環大臺北|環大台北", "環大臺北自行車挑戰"),
    (r"L['’]?Étape|L['’]?Etape|環法", "L'Étape 環法日月潭"),
    (r"銅礦88|銅礦", "銅礦88經典挑戰賽"),
    (r"落日飛車|350自行車挑戰|LAVanLife|LAVA", "LAVA 落日飛車350"),
    (r"自由車錦標賽|市長盃自由車|國手選拔|青年盃|全國公路", "自由車錦標賽/選拔"),
    (r"自行車嘉年華|GIANT CUP|LIVDAY", "捷安特自行車嘉年華"),
    (r"北高360|雙塔520|四極|TBA.*認證|認證", "TBA 長途認證"),
    (r"戀戀197", "戀戀197"),
    (r"仙山|一輪盃", "仙山單車挑戰賽"),
    (r"鵬灣|世界自行車日", "世界自行車日"),
    (r"四重溪", "屏東四重溪自行車挑戰賽"),
    (r"Gravel\s?Fundo", "GravelFundo 礫石越野系列"),
    (r"台中城市繞圈", "TCU 台中城市繞圈賽"),   # 中寮KOM 不含「城市繞圈」-> 不誤收
]
_SERIES = [(re.compile(p, re.I), label) for p, label in _SERIES]


def series_of(race_name):
    name = race_name or ""
    for rx, label in _SERIES:
        if rx.search(name):
            return label
    return None


_AGE_INT = re.compile(r"\d+")


def age_band(age_group):
    """Unify the heterogeneous raw age_group into one coarse decade band for
    cross-source analysis (the raw age_group is preserved separately). Schemes
    seen across sources: 5-year-start codes (20/25/30…), explicit ranges
    (24-35/40-49/19-23…), youth (U13-U15 / 15 / 16), MASTER, and parse junk
    ('4-1'). Bucketed by lower-bound age. Returns one of
    U19 / 19-29 / 30-39 / 40-49 / 50-59 / 60+ / MASTER, else None."""
    if not age_group:
        return None
    s = str(age_group).strip().upper()
    if s == "MASTER":
        return "MASTER"
    if s.startswith("U"):
        return "U19"
    m = _AGE_INT.search(s)
    if not m:
        return None
    n = int(m.group())
    if n < 13:          # implausible as an age band -> parse junk (e.g. '4-1')
        return None
    if n <= 18:
        return "U19"
    if n <= 29:
        return "19-29"
    if n <= 39:
        return "30-39"
    if n <= 49:
        return "40-49"
    if n <= 59:
        return "50-59"
    return "60+"


# ---- gender / age back-fill from the organizer's category code -------------
# Same convention as race_class above: M=male, W=women, optional R(oad) prefix,
# age as the trailing number — e.g. RM35 / M40 / RW30 / W20 / Ｍ45, plus the
# 男/女 keywords. A digit MUST follow the letter so criterium classes 'A'/'F'/'M'
# aren't misread, and bare 'F' is not treated as female (this dataset codes women
# as W, and 'F' is a criterium class letter). Citizen/challenge groups (107K自我
# 挑戰, 一般組, 雙塔520…) carry no sex and correctly stay None.
_GENDER_CODE = re.compile(r"[Rr]?([MWＭＷ])\s?\d")
_AGE_CODE = re.compile(r"[Rr]?[MWＭＷ]\s?(\d{1,2})")


def gender_from_category(category_raw):
    """Infer M/F from a category code/keyword, or None when unsexed or mixed."""
    if not category_raw:
        return None
    s = str(category_raw)
    has_m, has_w = "男" in s, "女" in s
    if "混" in s or (has_m and has_w):
        return None
    if has_w:
        return "F"
    if has_m:
        return "M"
    m = _GENDER_CODE.search(s)
    if m:
        return "M" if m.group(1) in ("M", "Ｍ") else "F"   # W/Ｗ -> female
    return None


def age_from_category(category_raw):
    """The age number embedded in a gender-age code (RM35 -> '35'), else None."""
    if not category_raw:
        return None
    m = _AGE_CODE.search(str(category_raw))
    return m.group(1) if m else None


def enrich(rec):
    """Add race_class + series + age_band; canonicalize the race_key for curated
    merged events; back-fill missing gender/age_band from the organizer's category
    code (M/W + age) when blank (mutates and returns it). Existing gender/age_group
    are never overridden."""
    canon = RACE_KEY_CANONICAL.get(rec.get("race_key"))
    if canon:
        rec["race_key"] = canon
        rec["race_name_canonical"] = canon
    rec["race_class"] = race_class(rec.get("result_label"), rec.get("category_raw"))
    rec["series"] = series_of(rec.get("race_name_raw") or rec.get("race_name_canonical"))
    # the long-distance certification series (北高360 / 雙塔520 / 四極620…) is by
    # definition 認證, even when the group label carries no 認證 keyword.
    if rec["series"] == "TBA 長途認證":
        rec["race_class"] = "認證"
    if rec.get("gender") not in ("M", "F"):
        g = gender_from_category(rec.get("category_raw"))
        if g:
            rec["gender"] = g
    rec["age_band"] = age_band(rec.get("age_group") or age_from_category(rec.get("category_raw")))
    return rec
