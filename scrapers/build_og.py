# -*- coding: utf-8 -*-
"""Build the branded social-share image (Feature 🔍 SSG + OG 分享圖).

Writes web/public/og.png — a single 1200x630 OpenGraph card used as the default
share image across the site. Per-page <title>/<meta description> carry the
entity-specific text; this image gives every share a consistent, on-brand look
without committing one raster per race/athlete.

Run once (and whenever branding/stats change); the PNG is committed.
PDPA: no personal data — brand + aggregate counts only.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common  # noqa: E402

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
DATA = common.PUBLIC_DATA_DIR
OUT = os.path.join(HERE, "..", "web", "public", "og.png")

# brand palette = dark theme tokens (tokens.css)
BG = (24, 23, 26)          # --color-bg  #18171A
SURFACE = (33, 31, 36)     # --color-surface
INK = (236, 233, 227)      # --color-ink  #ECE9E3
MUTED = (156, 150, 140)    # --color-muted #9C968C
ACCENT = (232, 145, 111)   # --color-accent #E8916F

W, H = 1200, 630

# Windows-bundled CJK variable fonts (this is a build machine).
SERIF = "C:/Windows/Fonts/NotoSerifTC-VF.ttf"
SANS = "C:/Windows/Fonts/NotoSansTC-VF.ttf"


def _font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def _stats():
    with open(os.path.join(DATA, "races.json"), encoding="utf-8") as f:
        races = json.load(f)
    with open(os.path.join(DATA, "athletes.json"), encoding="utf-8") as f:
        athletes = json.load(f)
    distinct = len({r["rk"] for r in races})
    years = [r["y"] for r in races if r.get("y")]
    return distinct, len(athletes), min(years), max(years)


def main():
    distinct, n_ath, y0, y1 = _stats()
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # subtle top accent bar
    d.rectangle([0, 0, W, 10], fill=ACCENT)

    pad = 80
    title_f = _font(SERIF, 92, 700)
    sub_f = _font(SANS, 40, 500)
    stat_f = _font(SANS, 34, 600)
    foot_f = _font(SANS, 28, 400)

    # title (two lines)
    d.text((pad, 150), "台灣公路車", font=title_f, fill=INK)
    d.text((pad, 150 + 112), "賽事成績儀表板", font=title_f, fill=ACCENT)

    # tagline
    d.text((pad, 430), "成績排行 · 進步軌跡 · 賽事 DNA · 車隊戰力", font=sub_f, fill=MUTED)

    # stat chips
    chips = [f"{n_ath:,} 位選手", f"{distinct} 場賽事", f"{y0}–{y1}"]
    x = pad
    for c in chips:
        bbox = d.textbbox((0, 0), c, font=stat_f)
        tw = bbox[2] - bbox[0]
        cw = tw + 48
        d.rounded_rectangle([x, 510, x + cw, 510 + 56], radius=28, fill=SURFACE)
        d.text((x + 24, 510 + 8), c, font=stat_f, fill=INK)
        x += cw + 18

    # footer source
    d.text((pad, H - 56), "cyclist.org.tw · bravelog.tw · cycling.org.tw 公開成績(去識別化)",
           font=foot_f, fill=MUTED)

    img.save(OUT, "PNG", optimize=True)
    print(f"og.png {W}x{H} -> {os.path.relpath(OUT)}  ({os.path.getsize(OUT)//1024} KB)")


if __name__ == "__main__":
    main()
