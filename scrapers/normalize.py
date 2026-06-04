# -*- coding: utf-8 -*-
"""
Cross-source normalization tables (recon-flagged Phase-1 task):
  - race_class():  the awarded-group bucket (競賽/市民/挑戰/青少年/團體/電輔車/認證)
  - series_of():   group races into series for analysis (96聯賽 / 登山大滿貫 / 臺灣自行車聯賽 …)
  - enrich():      add race_class + series to a unified record (in place)

These are CURATED keyword tables built from the real 2024-26 race/category values.
IMPORTANT (recon): distinct races must NOT be merged — the three "武嶺" races
(TIS崇越盃 / 96聯賽 / NeverStop) are different events; series labels group them
for browsing but each keeps its own race_key. KOM登山王之路 ≠ KOM太平洋經典賽 ≠ KOM登山王挑戰.
"""
import re


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
    if "市民" in lab or "巿民" in lab:
        return "市民"
    if "認證" in lab or "完賽" in lab:
        return "認證"
    if re.match(r"^[MWＭＷ]\d", cat) or cat == "MASTER" or "分齡" in lab:
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
]
_SERIES = [(re.compile(p, re.I), label) for p, label in _SERIES]


def series_of(race_name):
    name = race_name or ""
    for rx, label in _SERIES:
        if rx.search(name):
            return label
    return None


def enrich(rec):
    """Add race_class + series to a unified record (mutates and returns it)."""
    rec["race_class"] = race_class(rec.get("result_label"), rec.get("category_raw"))
    rec["series"] = series_of(rec.get("race_name_raw") or rec.get("race_name_canonical"))
    return rec
