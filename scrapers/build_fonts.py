# -*- coding: utf-8 -*-
"""Self-host + subset the web fonts (perf: kills the ~25 parallel Google-Fonts
CJK unicode-range subset requests on content-heavy pages).

Collects every character the DEPLOYED site can render (committed
web/public/data/*.json — race/athlete/team names etc. — plus the UI source),
then subsets each font to exactly those glyphs and writes woff2 to
web/public/fonts/. The CJK fonts get the CJK glyphs; the Latin fonts get the
Latin/digit/punctuation glyphs. Re-run after ingesting new data (new names may
add glyphs), like the other build_* steps.

Source TTFs live in data/_fonts_src/ (gitignored, fetched once); the woff2
outputs are committed as deploy artifacts.
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
SRC = os.path.join(ROOT, "data", "_fonts_src")
OUT = os.path.join(ROOT, "web", "public", "fonts")

# always include printable ASCII + the punctuation/symbols the UI uses
BASE = "".join(chr(c) for c in range(0x20, 0x7F)) \
    + "…—–·○‧／、，。！？：；「」『』（）【】〈〉《》〔〕％°’‘“”　＋－×÷≈√⚔⛰★🥇🥈🥉🏆🏟️🔁🌐📅❤️🌧️🧬🎚️👯🆚🃏"


def is_cjk(cp):
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0xF900 <= cp <= 0xFAFF
            or 0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFFEF
            or 0x3100 <= cp <= 0x312F or 0x2E80 <= cp <= 0x2EFF)


def collect_chars():
    chars = set(BASE)
    pats = [os.path.join(ROOT, "web", "public", "data", "**", "*.json")]
    for ext in ("*.astro", "*.tsx", "*.ts"):
        pats.append(os.path.join(ROOT, "web", "src", "**", ext))
    for pat in pats:
        for p in glob.glob(pat, recursive=True):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    chars.update(line)
    for ws in "\n\r\t":
        chars.discard(ws)
    return chars


def main():
    os.makedirs(OUT, exist_ok=True)
    allc = collect_chars()
    cjk = set(BASE) | {c for c in allc if is_cjk(ord(c))}
    latin = {c for c in allc if not is_cjk(ord(c)) and ord(c) >= 0x20}
    cjk_txt = os.path.join(SRC, "_cjk.txt")
    lat_txt = os.path.join(SRC, "_latin.txt")
    open(cjk_txt, "w", encoding="utf-8").write("".join(sorted(cjk)))
    open(lat_txt, "w", encoding="utf-8").write("".join(sorted(latin)))
    print(f"chars: total={len(allc)} cjk={len(cjk)} latin={len(latin)}")

    jobs = [
        ("NotoSansTC.ttf", "noto-sans-tc.woff2", cjk_txt),
        ("NotoSerifTC.ttf", "noto-serif-tc.woff2", cjk_txt),
        ("Fraunces.ttf", "fraunces.woff2", lat_txt),
        ("HankenGrotesk.ttf", "hanken-grotesk.woff2", lat_txt),
        ("SplineSansMono.ttf", "spline-sans-mono.woff2", lat_txt),
    ]
    for src, out, txt in jobs:
        srcp = os.path.join(SRC, src)
        if not os.path.exists(srcp):
            print(f"  ! missing source {src} — skip"); continue
        cmd = [sys.executable, "-m", "fontTools.subset", srcp,
               f"--text-file={txt}", "--flavor=woff2",
               f"--output-file={os.path.join(OUT, out)}",
               "--layout-features=*", "--name-IDs=*", "--no-hinting"]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        print(f"  {out}: {os.path.getsize(os.path.join(OUT, out)) // 1024} KB")


if __name__ == "__main__":
    main()
