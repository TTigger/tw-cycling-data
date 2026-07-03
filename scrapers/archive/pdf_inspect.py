# -*- coding: utf-8 -*-
"""Inspect raw text + word layout of a downloaded PDF to design a parser."""
import os
import sys
import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(__file__), "..", "data", "pdf", "2026050917190897897.pdf")

with pdfplumber.open(path) as pdf:
    print(f"FILE {os.path.basename(path)}  pages={len(pdf.pages)}")
    page = pdf.pages[0]
    print("\n--- extract_text() ---")
    txt = page.extract_text() or ""
    for i, line in enumerate(txt.splitlines()):
        if i > 40:
            print("   ...(truncated)")
            break
        print(f"{i:>3}| {line}")

    print("\n--- extract_tables(lattice/lines) ---")
    for strat in (
        {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
        {"vertical_strategy": "text", "horizontal_strategy": "text"},
    ):
        ts = page.extract_tables(table_settings=strat)
        nrows = sum(len(t) for t in ts)
        print(f"  strat={strat} -> {len(ts)} tables, {nrows} total rows")
        if ts and ts[0]:
            for row in ts[0][:6]:
                print("     | " + " | ".join((c or "").replace("\n", " ").strip() for c in row))
