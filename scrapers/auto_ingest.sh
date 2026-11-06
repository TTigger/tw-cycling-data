#!/bin/bash
# launchd entry for the weekly unattended ingest (see scrapers/auto_ingest.py).
# launchd starts with a bare PATH: add Homebrew (git, gh) and keep the Mac
# awake while it runs (a full crawl takes about 2 hours).
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "$(dirname "$0")/.." || exit 1
. scrapers/keychain_env.sh
exec /usr/bin/caffeinate -i .venv/bin/python scrapers/auto_ingest.py "$@"
