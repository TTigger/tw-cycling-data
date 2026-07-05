# -*- coding: utf-8 -*-
"""Single-entry pipeline runner (roadmap 0-8 / D4).

Encodes the order-sensitive refresh sequence that previously lived in the
README as a copy-paste command list: scrape -> merge -> validate -> builders
(manifest LAST) -> docs-gen -> backup. Steps run as subprocesses of the
existing scripts — no scraper/builder logic is duplicated here.

State: data/.pipeline_state.json records completed steps of the current run;
--resume continues after the last completed step, so a MemoryError in
build_viz (a known Windows gotcha) doesn't force a full re-run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRAPERS = ROOT / "scrapers"
STATE_FILE = ROOT / "data" / ".pipeline_state.json"
RACE_DIR = ROOT / "web" / "public" / "data" / "v1" / "race"


@dataclass
class Step:
    name: str
    argv: list[str]                      # script + args, relative to scrapers/
    group: str = "build"                 # scrape | merge | validate | build | publish
    optional: bool = False               # skipped unless explicitly enabled
    note: str = ""
    env: dict = field(default_factory=dict)


def scrape_steps(year: int) -> list[Step]:
    s = lambda name, *argv: Step(name, list(argv), group="scrape")
    return [
        s("scrape:cyclist", "cyclist_crawl.py"),
        s("scrape:bravelog-calendar", "bravelog_calendar.py", str(year)),
        s("scrape:bravelog", "bravelog_crawl.py"),
        s("scrape:tsu", "tsu_crawl.py"),
        s("scrape:cycling", "cycling_crawl.py"),
        s("scrape:league", "cyclist_league.py"),
        s("scrape:irunner", "irunner_crawl.py"),
        s("scrape:criterium", "criterium_crawl.py"),
        s("scrape:focusline", "focusline_crawl.py"),
        s("scrape:taiwanbike", "taiwanbike_crawl.py"),
    ]


# Builder order: viz/athletes first (heaviest, most-depended-on outputs),
# manifest.json strictly LAST — it snapshots stats of everything else.
BUILDERS = [
    "build_viz.py", "build_athletes.py", "build_teams.py", "build_series.py",
    "build_race_dna.py", "build_difficulty.py", "build_insights.py",
    "build_benchmarks.py", "build_home_ridgeline.py",
]


def build_plan(skip_scrape=False, sources=None, clean_race=False,
               with_og=False, with_backup=True, year=None) -> list[Step]:
    year = year or time.localtime().tm_year
    plan: list[Step] = []
    if not skip_scrape:
        for st in scrape_steps(year):
            if sources and st.name.split(":", 1)[1] not in sources:
                continue
            plan.append(st)
    plan.append(Step("merge", ["merge.py"], group="merge"))
    plan.append(Step("validate", ["validate.py", "master.json"], group="validate"))
    if clean_race:
        plan.append(Step("clean-race-dir", [], group="build",
                         note="rm orphan per-race files (race_key changes)"))
    for b in BUILDERS:
        plan.append(Step("build:" + b.replace("build_", "").replace(".py", ""),
                         [b], group="build"))
    if with_og:
        plan.append(Step("build:og", ["build_og.py"], group="build"))
    plan.append(Step("build:manifest", ["build_manifest.py"], group="build",
                     note="must run last of the builders"))
    plan.append(Step("docs-gen", ["gen_docs_stats.py"], group="publish"))
    if with_backup:
        argv = ["backup.py", "--include", "data/raw_archive"]
        if not os.environ.get("R2_ACCOUNT_ID"):
            argv.append("--no-upload")   # R2 not configured yet — local zip only
        plan.append(Step("backup", argv, group="publish"))
    return plan


def default_runner(step: Step) -> int:
    if step.name == "clean-race-dir":
        if RACE_DIR.exists():
            for f in RACE_DIR.iterdir():
                f.unlink()
        return 0
    cmd = [sys.executable, str(SCRAPERS / step.argv[0]), *step.argv[1:]]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", **step.env}
    return subprocess.call(cmd, cwd=str(ROOT), env=env)


def load_state() -> list[str]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("completed", [])
    return []


def save_state(completed: list[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"completed": completed}, indent=1),
                          encoding="utf-8")


def clear_state() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def run_plan(plan: list[Step], runner=default_runner, resume=False,
             dry_run=False, log=print) -> int:
    completed = load_state() if resume else []
    if resume and completed:
        log(f"resuming — {len(completed)} step(s) already done: {', '.join(completed)}")
    for step in plan:
        label = f"[{step.group}] {step.name}"
        if step.name in completed:
            log(f"skip {label} (done)")
            continue
        if dry_run:
            log(f"plan {label}  ->  {' '.join(step.argv) or '(internal)'}")
            continue
        log(f"run  {label}")
        rc = runner(step)
        if rc != 0:
            save_state(completed)
            log(f"FAILED {label} (exit {rc}) — fix, then: python -m pipeline refresh --resume")
            return rc
        completed.append(step.name)
        save_state(completed)
    if not dry_run:
        clear_state()
        log(f"refresh complete — {len(plan)} step(s)")
    return 0
