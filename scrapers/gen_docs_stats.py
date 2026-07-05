"""Regenerate machine-derived doc blocks from build artifacts.

Keeps SOURCES.md's dataset stats and mcp-server/README.md's tool list in
sync with reality (manifest.json / master_summary.json / server.py), so the
numbers can never drift again. Narrative prose stays hand-written; only the
content between ``<!-- gen:NAME:begin -->`` / ``<!-- gen:NAME:end -->``
markers is owned by this script.

Usage:
    python scrapers/gen_docs_stats.py          # rewrite blocks in place
    python scrapers/gen_docs_stats.py --check  # exit 1 if any block is stale (CI)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "web" / "public" / "data" / "v1" / "manifest.json"
SUMMARY = ROOT / "data" / "processed" / "master_summary.json"
SERVER = ROOT / "mcp-server" / "tw_cycling_data_mcp" / "server.py"
SOURCES_MD = ROOT / "SOURCES.md"
MCP_README = ROOT / "mcp-server" / "README.md"

# Short display names for by_platform keys, ordered by count at render time.
PLATFORM_SHORT = {
    "bravelog.tw": "bravelog",
    "irunner.biji.co": "irunner",
    "tsu.com.tw": "tsu",
    "taiwanbike.org": "taiwanbike",
    "twbike.org": "twbike",
    "cyclist.org.tw": "cyclist",
    "criterium.tw": "criterium",
    "cycling.org.tw": "cycling",
}


def replace_block(text: str, name: str, body: str) -> str:
    """Replace the content between gen markers for *name*; raise if missing."""
    begin, end = f"<!-- gen:{name}:begin -->", f"<!-- gen:{name}:end -->"
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"marker pair for '{name}' not found")
    return pattern.sub(begin + "\n" + body.strip() + "\n" + end, text)


def render_sources_stats() -> str:
    # Everything from master_summary.json — this block describes the master
    # dataset (incl. DNF/DNS rows), not the public manifest counts.
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    by_platform = summary["by_platform"]
    years = [int(y) for y in summary["by_year"]]
    parts = "・".join(
        f"{PLATFORM_SHORT.get(k, k)} {v:,}"
        for k, v in sorted(by_platform.items(), key=lambda kv: -kv[1])
    )
    return (
        f"主資料集 master:**{summary['total_records']:,} 筆 / "
        f"{min(years)}–{max(years)} / "
        f"{summary['distinct_races']} 場 / "
        f"{len(by_platform)} 來源**(海外賽另計)。\n\n"
        f"> 各來源現況筆數(master 內,跨源去重後):{parts}。\n"
        f"> (本區塊由 `scrapers/gen_docs_stats.py` 生成,勿手改。)"
    )


def mcp_tool_signatures(source: str) -> list[str]:
    """Extract `name(arg, optional?)` for each @mcp.tool() def in server.py."""
    sigs = []
    for m in re.finditer(r"@mcp\.tool\(\)\s*\ndef (\w+)\((.*?)\)\s*->", source, re.DOTALL):
        name, raw = m.group(1), m.group(2)
        params = []
        for p in raw.split(","):
            p = p.strip()
            if not p:
                continue
            pname = p.split(":")[0].split("=")[0].strip()
            params.append(pname + ("?" if "=" in p else ""))
        sigs.append(f"{name}({', '.join(params)})")
    return sigs


def render_mcp_tools() -> str:
    sigs = mcp_tool_signatures(SERVER.read_text(encoding="utf-8"))
    listed = "、".join(f"`{s}`" for s in sigs)
    return (
        f"{len(sigs)} 個工具:{listed}。\n"
        f"(本區塊由 `scrapers/gen_docs_stats.py` 生成,勿手改。)"
    )


def main() -> int:
    check = "--check" in sys.argv[1:]
    stale = []
    for path, name, body in (
        (SOURCES_MD, "stats", render_sources_stats()),
        (MCP_README, "tools", render_mcp_tools()),
    ):
        old = path.read_text(encoding="utf-8")
        new = replace_block(old, name, body)
        if new != old:
            if check:
                stale.append(str(path.relative_to(ROOT)))
            else:
                path.write_text(new, encoding="utf-8")
                print(f"updated {path.relative_to(ROOT)}")
    if stale:
        print("stale generated blocks (run: python scrapers/gen_docs_stats.py):")
        for p in stale:
            print(f"  {p}")
        return 1
    if check:
        print("generated doc blocks are up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
