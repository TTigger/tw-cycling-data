# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import auto_ingest as A  # noqa: E402


def cmp(**kw):
    base = {"missing": [], "added": [], "changed": [], "same": 10,
            "athletes": {"old": 5, "new": 5, "kept": 5, "lost": 0, "new_ids": 0},
            "rows": {"old": 100, "new": 100}}
    base.update(kw)
    return base


def test_shrunk_or_broken_outputs_are_flagged():
    before = {"a.json": 10, "b.json": 5, "c.json": 3}
    assert A.shrunk(before, {"a.json": 12, "b.json": 4, "c.json": -1}) == ["b.json", "c.json"]


def test_gate_blocks_lost_or_shrunk_race_years_and_lost_athletes():
    assert A.gate(cmp()) == []
    assert A.gate(cmp(missing=[{"race": "x", "year": 2020, "rows": 3}]))
    assert A.gate(cmp(changed=[{"race": "x", "year": 2020, "old": 10, "new": 9}]))
    assert A.gate(cmp(athletes={"old": 5, "new": 5, "kept": 4, "lost": 1, "new_ids": 1}))
    # a race-year that only grew is fine
    assert A.gate(cmp(changed=[{"race": "x", "year": 2026, "old": 10, "new": 30}])) == []


def test_news_means_added_or_grown():
    assert not A.has_news(cmp())
    assert not A.has_news(cmp(changed=[{"race": "x", "year": 2026, "old": 10, "new": 10,
                                        "rows_not_reproduced": 2}]))
    assert A.has_news(cmp(added=[{"race": "y", "year": 2026, "rows": 50}]))
    assert A.has_news(cmp(changed=[{"race": "x", "year": 2026, "old": 10, "new": 30}]))


def test_pr_body_lists_news_kept_sources_and_new_events():
    body = A.pr_body(cmp(added=[{"race": "某某挑戰", "year": 2026, "rows": 50}],
                         rows={"old": 100, "new": 150}),
                     ["cyclist_x.json(10 → 0,沿用上一版)"], ["  7001  某某自行車賽"], "2026-11-09")
    assert "100 → 150" in body and "某某挑戰 2026:50 筆" in body
    assert "沿用上一版" in body and "7001" in body and "請檢查後合併" in body


def test_guard_puts_back_a_shrunk_source(tmp_path, monkeypatch):
    import json
    proc, prev = tmp_path / "processed", tmp_path / "prev"
    proc.mkdir()
    monkeypatch.setattr(A, "PROCESSED", str(proc))
    monkeypatch.setattr(A, "PREV", str(prev))
    monkeypatch.setattr(A, "log", lambda m: None)
    (proc / "cyclist_x.json").write_text(json.dumps([1, 2, 3]))
    (proc / "ebetter_y.json").write_text(json.dumps([1]))
    counts = A.snapshot()
    (proc / "cyclist_x.json").write_text("[]")            # crawl came back empty
    (proc / "ebetter_y.json").write_text(json.dumps([1, 2]))  # grew: keep
    restored = A.guard(counts, "cyclist")
    assert json.loads((proc / "cyclist_x.json").read_text()) == [1, 2, 3]
    assert json.loads((proc / "ebetter_y.json").read_text()) == [1, 2]
    assert len(restored) == 1 and "cyclist_x.json" in restored[0]
