# -*- coding: utf-8 -*-
"""Classify a race into a discipline type for the climber-vs-rouleur radar.
Shared by build_athletes (per-athlete trait profile). Order matters: climb wins
over the rest; criterium/TT are detected by name or category; else road."""
import re

CLIMB = re.compile(r"武嶺|KOM|登山王|塔塔加|大禹嶺|爬坡", re.I)
CRIT = re.compile(r"繞圈|criterium|crit", re.I)
TT = re.compile(r"計時|個人計時|ITT|時間賽", re.I)

LABELS = {"climb": "爬坡", "crit": "繞圈", "tt": "計時", "road": "公路"}


def classify(race_name, category=None):
    """Return one of 'climb' | 'crit' | 'tt' | 'road'."""
    name = race_name or ""
    if CLIMB.search(name):
        return "climb"
    blob = name + " " + (category or "")
    if CRIT.search(blob):
        return "crit"
    if TT.search(blob):
        return "tt"
    return "road"
