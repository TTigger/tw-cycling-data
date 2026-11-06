# -*- coding: utf-8 -*-
"""Weekly unattended ingest: re-crawl every source, rebuild, check, open a PR.

Runs on the Mac that holds the raw data (launchd, see scrapers/auto_ingest.sh).
It never merges: new results go up as a PR for a person to merge.

  1. needs a clean master checkout (skips otherwise, so it never touches work in progress)
  2. discover (calendars) + look for new iRunner / e-better events
  3. crawl each source; a source whose output shrinks or fails keeps its previous file
  4. rebuild (the pipeline also checks for real names)
  5. gates: no race-year lost or shrunk, no athlete URL lost, pytest passes
  6. nothing new -> restore the checkout and stop; otherwise branch, commit, push, PR

  python scrapers/auto_ingest.py                      # full run
  python scrapers/auto_ingest.py --sources sport-result --no-push   # try it out
Report: data/processed/_auto/report.md   Log: data/processed/_auto/run.log
"""
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import merge  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PY = os.path.join(ROOT, ".venv", "bin", "python")
AUTO = os.path.join(ROOT, "data", "processed", "_auto")
PREV = os.path.join(AUTO, "prev")
PROCESSED = os.path.join(ROOT, "data", "processed")
SOURCES = ["tsu", "cyclist", "league", "cycling", "bravelog", "irunner", "criterium",
           "focusline", "taiwanbike", "sporter96", "sport-result", "ebetter", "atsport"]
SOURCE_TIMEOUT = 3 * 3600
EMAIL = "102512862+TTigger@users.noreply.github.com"
IRUNNER_AHEAD = 150
COVERAGE = "web/public/data/v1/coverage.json"
EBETTER_AHEAD = 300


def log(msg):
    line = f"[{dt.datetime.now():%F %T}] {msg}"
    print(line, flush=True)
    with open(os.path.join(AUTO, "run.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd, timeout=None, check=False, capture=False):
    r = subprocess.run(cmd, cwd=ROOT, timeout=timeout, text=True,
                       capture_output=capture)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> exit {r.returncode}\n{(r.stderr or '')[-2000:]}")
    return r


def git(*args, capture=True):
    return run(["git", *args], capture=capture).stdout.strip() if capture else run(["git", *args])


def notify(msg):
    subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "tw-cycling-data"'])


# ---- source output guard -------------------------------------------------
def source_files():
    """Every file in data/processed a crawler writes (merge inputs + .public twins)."""
    out = []
    for f in os.listdir(PROCESSED):
        if f.startswith(merge.SOURCE_PREFIXES + ("tsu_",)) and f.endswith(".json") \
                and not f.endswith("_summary.json"):
            out.append(f)
    return sorted(out)


def rows_in(path):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return -1
    if isinstance(d, dict):
        d = d.get("records", [])
    return len(d) if isinstance(d, list) else -1


def snapshot():
    os.makedirs(PREV, exist_ok=True)
    counts = {}
    for f in source_files():
        shutil.copy2(os.path.join(PROCESSED, f), os.path.join(PREV, f))
        counts[f] = rows_in(os.path.join(PROCESSED, f))
    return counts


def shrunk(counts, now):
    """Files whose row count dropped (or that no longer parse: -1). (tested)"""
    return [f for f, n in counts.items() if now.get(f, -1) < n]


def guard(counts, failed_source):
    """Put back the previous file of any source output that shrank or broke.
    Returns what was restored, for the PR body."""
    now = {f: rows_in(os.path.join(PROCESSED, f)) for f in counts}
    restored = []
    for f in shrunk(counts, now):
        shutil.copy2(os.path.join(PREV, f), os.path.join(PROCESSED, f))
        restored.append(f"{f}({counts[f]} → {now[f]},沿用上一版)")
    if failed_source:
        log(f"  {failed_source} failed" + ("" if restored else " but no output shrank"))
    return restored


# ---- discovery helpers ---------------------------------------------------
def refresh_irunner():
    """Re-scan iRunner track ids up to a bit past the newest known event, so new
    events get crawled. The event list is gitignored: back it up first."""
    path = os.path.join(ROOT, "data", "raw", "irunner_events.json")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        prev = json.load(f)
    top = max(e["track_id"] for e in prev)
    lo = int(os.environ.get("IRUNNER_LO", "1200"))
    log(f"irunner: rescan track ids {lo}–{top + IRUNNER_AHEAD}")
    r = run([PY, "scrapers/irunner_crawl.py", "discover", str(lo), str(top + IRUNNER_AHEAD)],
            timeout=3600, capture=True)
    try:
        with open(path, encoding="utf-8") as f:
            now = json.load(f)
    except (OSError, ValueError):
        now = []
    if r.returncode != 0 or len(now) < len(prev):
        log("  irunner discover failed or found fewer events; keeping the previous list")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(prev, f, ensure_ascii=False, indent=2)
        return
    # discover rewrites the list without dates/extra fields; keep what we had
    old = {e["track_id"]: e for e in prev}
    merged = [old.get(e["track_id"], e) for e in now]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    log(f"  irunner events: {len(prev)} → {len(merged)}")


def scan_ebetter():
    """New e-better cycling events (names need a person: listed in the PR, not crawled)."""
    path = os.path.join(ROOT, "data", "raw", "ebetter_events.json")
    with open(path, encoding="utf-8") as f:
        top = max(int(e["sn"]) for e in json.load(f))
    r = run([PY, "scrapers/ebetter_crawl.py", "--scan", str(top + 1), str(top + EBETTER_AHEAD)],
            timeout=3600, capture=True)
    return [ln.strip() for ln in (r.stdout or "").splitlines()
            if ln.strip() and "(in worklist)" not in ln]


# ---- gates ---------------------------------------------------------------
def gate(cmp):
    """Problems that stop a PR. `cmp` is compare_rebuild --json output. (tested)"""
    bad = []
    if cmp["missing"]:
        bad.append(f"{len(cmp['missing'])} race-years disappeared")
    shrank = [c for c in cmp["changed"] if c.get("new", 0) < c.get("old", 0)]
    if shrank:
        bad.append(f"{len(shrank)} race-years lost rows")
    if cmp["athletes"]["lost"]:
        bad.append(f"{cmp['athletes']['lost']} athlete URLs would break")
    return bad


def has_news(cmp):
    return bool(cmp["added"]) or any(c.get("new", 0) > c.get("old", 0) for c in cmp["changed"])


def restore_checkout():
    git("checkout", "--", ".")
    git("clean", "-fdq", "--", "web/public/data")


def pr_body(cmp, restored, ebetter_new, today):
    lines = [f"每週自動收錄({today})。**請檢查後合併**;自動流程不會自己合併。", "",
             f"- 完賽筆數:{cmp['rows']['old']:,} → {cmp['rows']['new']:,}",
             f"- 新增賽事年度:{len(cmp['added'])};筆數增加:"
             f"{sum(1 for c in cmp['changed'] if c.get('new', 0) > c.get('old', 0))}",
             f"- 選手:{cmp['athletes']['old']:,} → {cmp['athletes']['new']:,}(失效網址 0)", ""]
    if cmp["added"]:
        lines.append("## 新增")
        lines += [f"- {a.get('race')} {a.get('year')}:{a.get('rows')} 筆" for a in cmp["added"][:40]]
        lines.append("")
    grew = [c for c in cmp["changed"] if c.get("new", 0) > c.get("old", 0)]
    if grew:
        lines.append("## 筆數增加")
        lines += [f"- {c.get('race')} {c.get('year')}:{c.get('old')} → {c.get('new')}" for c in grew[:40]]
        lines.append("")
    edited = [c for c in cmp["changed"] if c.get("new", 0) == c.get("old", 0)]
    if edited:
        lines.append("## 筆數相同但內容有變(來源更正或遮罩調整,請抽查)")
        lines += [f"- {c.get('race')} {c.get('year')}:{c.get('rows_not_reproduced')} 筆不同" for c in edited[:40]]
        lines.append("")
    if restored:
        lines.append("## 這次沒更新的來源(抓取失敗或筆數變少,沿用上一版)")
        lines += [f"- {r}" for r in restored]
        lines.append("")
    if ebetter_new:
        lines.append("## 伊貝特新賽事(需人工加進 data/raw/ebetter_events.json)")
        lines += [f"- {e}" for e in ebetter_new[:30]]
        lines.append("")
    lines += ["檢查:既有賽事年度沒有減少、選手網址沒有失效、沒有真實姓名、pytest 通過。", "",
              "🤖 Generated with [Claude Code](https://claude.com/claude-code)"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", nargs="*", default=SOURCES)
    ap.add_argument("--no-push", action="store_true", help="stop before branch/commit/PR")
    ap.add_argument("--skip-discovery", action="store_true")
    ap.add_argument("--compare-ref", default="master", help=argparse.SUPPRESS)  # testing only
    ap.add_argument("--here", action="store_true",
                    help="try it on the current (clean) branch instead of master")
    a = ap.parse_args()
    os.makedirs(AUTO, exist_ok=True)
    today = dt.date.today().isoformat()

    # the Thursday discover-only job leaves coverage.json modified; it is rebuilt here anyway
    dirty = [ln for ln in git("status", "--porcelain").splitlines() if not ln.endswith(COVERAGE)]
    on_master = git("rev-parse", "--abbrev-ref", "HEAD") == "master"
    if dirty or (not on_master and not a.here):
        log("skip: checkout is not a clean master (work in progress?)")
        notify("自動收錄略過:工作目錄不是乾淨的 master")
        return 0
    git("checkout", "--", COVERAGE)
    if on_master:
        git("pull", "-q", "--ff-only")

    restored, ebetter_new = [], []
    try:
        if not a.skip_discovery:
            run([PY, "scrapers/discover.py"], timeout=3600, capture=True)
            refresh_irunner()
            ebetter_new = scan_ebetter()
        counts = snapshot()
        for s in a.sources:
            log(f"crawl {s}")
            try:
                r = run(["bash", "scrapers/rebuild_all.sh", "crawl", s], timeout=SOURCE_TIMEOUT,
                        capture=True)
                failed = s if r.returncode != 0 else None
            except subprocess.TimeoutExpired:
                failed = s
                log(f"  {s} timed out")
            restored += guard(counts, failed)
        log("build")
        b = run(["bash", "scrapers/rebuild_all.sh", "build"], timeout=3 * 3600, capture=True)
        if b.returncode != 0:
            raise RuntimeError("build failed (real-name check or a builder):\n" + (b.stdout or "")[-3000:])
        cmp_path = os.path.join(AUTO, "compare.json")
        run([PY, "scrapers/compare_rebuild.py", "--ref", a.compare_ref, "--json", cmp_path],
            timeout=1800, check=True, capture=True)
        with open(cmp_path, encoding="utf-8") as f:
            cmp = json.load(f)
        problems = gate(cmp)
        if problems:
            raise RuntimeError("gates failed: " + "; ".join(problems))
        if not has_news(cmp):
            log("no new results")
            restore_checkout()
            notify("自動收錄:這週沒有新成績" + (f"(伊貝特有 {len(ebetter_new)} 場新賽事待加)" if ebetter_new else ""))
            return 0
        t = run([PY, "-m", "pytest", "scrapers", "-q"], timeout=1800, capture=True)
        if t.returncode != 0:
            raise RuntimeError("pytest failed:\n" + (t.stdout or "")[-2000:])
        body = pr_body(cmp, restored, ebetter_new, today)
        with open(os.path.join(AUTO, "report.md"), "w", encoding="utf-8") as f:
            f.write(body)
        if a.no_push:
            log("--no-push: report written, checkout left as built")
            return 0
        branch = f"auto/ingest-{today}"
        git("checkout", "-q", "-B", branch)
        git("add", "-A")
        env = dict(os.environ, GIT_AUTHOR_EMAIL=EMAIL, GIT_COMMITTER_EMAIL=EMAIL)
        msg = (f"data: 每週自動收錄 {today}(+{cmp['rows']['new'] - cmp['rows']['old']:,} 筆)\n\n"
               "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n")
        subprocess.run(["git", "commit", "-q", "-F", "-"], input=msg, text=True, cwd=ROOT, env=env, check=True)
        git("push", "-q", "-f", "-u", "origin", branch)
        url = run(["gh", "pr", "create", "--base", "master", "--head", branch,
                   "--title", f"每週自動收錄 {today}(+{cmp['rows']['new'] - cmp['rows']['old']:,} 筆)",
                   "--body", body], capture=True).stdout.strip()
        git("checkout", "-q", "master")
        log(f"PR {url}")
        notify("自動收錄:有新成績,PR 已開好,請檢查後合併")
        return 0
    except Exception as e:  # noqa: BLE001 - report every failure, leave a clean checkout
        log(f"FAILED: {e}")
        with open(os.path.join(AUTO, "report.md"), "w", encoding="utf-8") as f:
            f.write(f"# 自動收錄失敗 {today}\n\n```\n{e}\n```\n")
        if git("rev-parse", "--abbrev-ref", "HEAD").startswith("auto/"):
            git("checkout", "-q", "-f", "master")
        restore_checkout()
        notify("自動收錄失敗,請看 data/processed/_auto/report.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
