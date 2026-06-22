# Local data-freshness radar for tw-cycling-data.
#
# Why local: the claude.ai cloud routine runs discover.py from a datacenter IP
# that all three race calendars (raceon / biji / ensage) return HTTP 403 for, so
# a real calendar diff only works from this (Taiwan) IP. This script is meant to
# run as a Windows Scheduled Task (Mon/Thu) with "run task as soon as possible
# after a missed start" enabled, so a machine that was powered off catches up on
# its next wake — fine for a twice-weekly radar.
#
# It refreshes web/public/data/coverage.json + _discover/missing_races.json and
# appends a dated line (plus any newly-appeared races) to _discover/freshness.log.
# It does NOT git commit or push — review missing_races.json and commit when you
# act on a new gap. To self-heal the live /coverage page automatically instead,
# uncomment the git block at the bottom.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'

$repo = Split-Path -Parent $PSScriptRoot   # scrapers\ -> repo root
Set-Location $repo

python scrapers\discover.py
python scrapers\freshness_log.py

# --- optional: auto-publish the refreshed coverage so /coverage never goes stale ---
# git add web/public/data/coverage.json
# git diff --cached --quiet; if (-not $?) { git commit -m "chore(data): weekly local freshness refresh"; git push origin master }
