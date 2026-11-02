#!/usr/bin/env bash
# macOS/Linux twin of freshness_local.ps1 — local data-freshness radar.
# Must run from a Taiwan IP: the race calendars 403 the cloud routine's IP.
# Refreshes web/public/data/v1/coverage.json + _discover/missing_races.json and
# appends to _discover/freshness.log. Does NOT commit or push.
# Works without master.public.json (falls back to races.json for the diff).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY=python3
"$PY" scrapers/discover.py
"$PY" scrapers/freshness_log.py
