#!/usr/bin/env bash
# Installs (or reinstalls) the two macOS jobs. A run missed while the Mac sleeps
# runs on wake.
#   Mon 08:30  com.ttigger.tw-cycling-ingest     scrapers/auto_ingest.sh: re-crawl,
#              rebuild, check; if there are new results it opens a PR (never merges)
#   Thu 08:30  com.ttigger.tw-cycling-freshness  scrapers/freshness_local.sh: calendar
#              check only -> coverage.json (not committed; Monday's run rebuilds it)
#   bash scrapers/install_launchd.sh            install / update both
#   bash scrapers/install_launchd.sh --remove   uninstall both
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/Library/LaunchAgents" "$REPO/data/processed/_discover" "$REPO/data/processed/_auto"

esc() { sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }

install_job() {   # label weekday command
  local label=$1 weekday=$2 cmd=$3 plist="$HOME/Library/LaunchAgents/$1.plist"
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  if [ "${REMOVE:-}" = 1 ]; then rm -f "$plist"; echo "removed $label"; return; fi
  cat > "$plist" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>-c</string><string>$(printf '%s' "$cmd" | esc)</string></array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Weekday</key><integer>$weekday</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>30</integer></dict>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
</dict>
</plist>
PL
  plutil -lint "$plist" >/dev/null
  launchctl bootstrap "gui/$(id -u)" "$plist"
  echo "installed $label -> $plist"
}

[ "${1:-}" = "--remove" ] && REMOVE=1

FLOG="data/processed/_discover/launchd.log"
install_job com.ttigger.tw-cycling-freshness 4 "cd \"$REPO\" && { date; scrapers/freshness_local.sh; } >> $FLOG 2>&1 \
&& /usr/bin/osascript -e 'display notification \"賽事偵查完成,coverage.json 已更新(週一自動收錄會一起提交)\" with title \"tw-cycling-data\"' \
|| /usr/bin/osascript -e 'display notification \"賽事偵查失敗,請看 $FLOG\" with title \"tw-cycling-data\"'"

# auto_ingest notifies on its own (new PR / nothing new / failed)
install_job com.ttigger.tw-cycling-ingest 1 "cd \"$REPO\" && { date; scrapers/auto_ingest.sh; } >> data/processed/_auto/launchd.log 2>&1"
