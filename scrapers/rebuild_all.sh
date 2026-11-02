#!/usr/bin/env bash
# Rebuild master.json FROM SCRATCH by re-crawling every source (2009–today).
#
# Why this exists: master.json (real names) and data/raw are gitignored, so they
# live on exactly one machine. `python -m pipeline refresh` assumes those caches
# already exist (it runs irunner in test mode, bravelog_calendar for one year,
# cyclist for 2024+ only). This script encodes the full-history arguments so any
# fresh clone can regenerate the canonical dataset.
#
# Usage:
#   scrapers/rebuild_all.sh crawl <source>   # one source (see SOURCES below)
#   scrapers/rebuild_all.sh crawl all        # every source, sequentially
#   scrapers/rebuild_all.sh build            # merge → validate → builders → manifest
# Sources hit different sites, so `crawl <source>` jobs can run in parallel.
# Logs: data/raw/_rebuild/<source>.log   Every crawler caches, so re-runs resume.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY=python3
export PYTHONIOENCODING=utf-8
LOG=data/raw/_rebuild
mkdir -p "$LOG"
YEAR_NOW=$(date +%Y)
SOURCES="tsu cyclist league cycling bravelog irunner criterium focusline taiwanbike sporter96"

# iRunner cycling events live in this track-id window (2023+ ≈ 1200–1650 as of
# 2026-11); widen IRUNNER_HI as new events are published.
IRUNNER_LO=${IRUNNER_LO:-1200}
IRUNNER_HI=${IRUNNER_HI:-1700}

crawl_one() {
  case "$1" in
    tsu)        $PY scrapers/tsu_crawl.py --years 2009-$YEAR_NOW ;;
    cyclist)    $PY scrapers/cyclist_crawl.py --years 2014-$YEAR_NOW --out cyclist_2014_$YEAR_NOW.json ;;
    league)     $PY scrapers/cyclist_league.py ;;
    cycling)    $PY scrapers/cycling_crawl.py && $PY scrapers/cycling_oldroad.py ;;
    bravelog)
      # Union the committed worklist with a fresh calendar pull, so contests the
      # search endpoint no longer returns are still crawled.
      W=data/raw/bravelog_cycling_contests.json
      cp "$W" "$LOG/bravelog_worklist.prev.json"
      $PY scrapers/bravelog_calendar.py $(seq 2020 $YEAR_NOW) || true
      $PY - "$LOG/bravelog_worklist.prev.json" "$W" <<'EOF'
import json, sys
prev, cur = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
seen = {c["uid"] for c in cur}
merged = cur + [c for c in prev if c["uid"] not in seen]
merged.sort(key=lambda c: c.get("start_date") or "")
json.dump(merged, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"bravelog worklist: {len(cur)} fresh + {len(merged)-len(cur)} kept from previous = {len(merged)}")
EOF
      $PY scrapers/bravelog_crawl.py ;;
    irunner)
      [ -f data/raw/irunner_events.json ] || $PY scrapers/irunner_crawl.py discover $IRUNNER_LO $IRUNNER_HI
      ids=$($PY -c "import json;print(' '.join(str(e['track_id']) for e in json.load(open('data/raw/irunner_events.json',encoding='utf-8'))))")
      $PY scrapers/irunner_crawl.py fetch $ids && $PY scrapers/irunner_crawl.py dates && $PY scrapers/irunner_crawl.py build ;;
    criterium)  $PY scrapers/criterium_crawl.py ;;
    focusline)  $PY scrapers/focusline_crawl.py ;;
    taiwanbike) $PY scrapers/taiwanbike_crawl.py ;;
    sporter96)  $PY scrapers/sporter96_pdf.py ;;   # PDFs listed in data/raw/sporter96_pdfs.json
    *) echo "unknown source: $1 (one of: $SOURCES)"; return 2 ;;
  esac
}

case "${1:-}" in
  crawl)
    targets="${2:-all}"; [ "$targets" = all ] && targets=$SOURCES
    rc=0
    for s in $targets; do
      echo "[$(date '+%F %T')] crawl $s → $LOG/$s.log"
      if crawl_one "$s" >"$LOG/$s.log" 2>&1; then echo "  ok $s"; else echo "  FAILED $s (see log)"; rc=1; fi
    done
    exit $rc ;;
  build)
    $PY -m pipeline refresh --skip-scrape --clean-race ${BUILD_FLAGS:---no-backup} ;;
  *) sed -n '2,16p' "$0"; exit 2 ;;
esac
