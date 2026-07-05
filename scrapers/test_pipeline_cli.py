# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.core import Step, build_plan, run_plan, load_state, clear_state  # noqa: E402
import pipeline.core as core  # noqa: E402


def names(plan):
    return [s.name for s in plan]


def test_order_invariants():
    n = names(build_plan())
    assert n.index("merge") < n.index("validate") < n.index("build:viz")
    assert n[-1] == "backup" and n[-2] == "docs-gen"
    assert n.index("build:manifest") == n.index("docs-gen") - 1  # manifest last builder


def test_skip_scrape_and_source_filter():
    assert not any(s.startswith("scrape:") for s in names(build_plan(skip_scrape=True)))
    only = [s for s in names(build_plan(sources=["tsu"])) if s.startswith("scrape:")]
    assert only == ["scrape:tsu"]


def test_backup_falls_back_to_no_upload_without_r2(monkeypatch):
    monkeypatch.delenv("R2_ACCOUNT_ID", raising=False)
    plan = build_plan(skip_scrape=True)
    assert "--no-upload" in plan[-1].argv
    monkeypatch.setenv("R2_ACCOUNT_ID", "acct")
    plan = build_plan(skip_scrape=True)
    assert "--no-upload" not in plan[-1].argv


def test_run_plan_stops_on_failure_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "STATE_FILE", tmp_path / "state.json")
    plan = [Step("a", ["a.py"]), Step("b", ["b.py"]), Step("c", ["c.py"])]
    ran = []

    def flaky(step):
        ran.append(step.name)
        return 1 if step.name == "b" and len(ran) == 2 else 0

    assert run_plan(plan, runner=flaky, log=lambda *_: None) == 1
    assert load_state() == ["a"]
    assert run_plan(plan, runner=flaky, resume=True, log=lambda *_: None) == 0
    assert ran == ["a", "b", "b", "c"]          # a not re-run on resume
    assert load_state() == []                    # state cleared on success


def test_dry_run_executes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "STATE_FILE", tmp_path / "state.json")
    boom = lambda step: (_ for _ in ()).throw(AssertionError("executed!"))
    assert run_plan(build_plan(skip_scrape=True), runner=boom,
                    dry_run=True, log=lambda *_: None) == 0
