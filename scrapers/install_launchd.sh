#!/usr/bin/env bash
# Installs (or reinstalls) the macOS weekly freshness radar: Mon + Thu 08:30
# local time, runs scrapers/freshness_local.sh (calendar check -> coverage.json),
# then shows a notification. It does NOT commit or push; review and commit the
# updated coverage.json yourself. A run missed while the Mac sleeps runs on wake.
#   bash scrapers/install_launchd.sh            install / update
#   bash scrapers/install_launchd.sh --remove   uninstall
set -euo pipefail
LABEL=com.ttigger.tw-cycling-freshness
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="data/processed/_discover/launchd.log"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ "${1:-}" = "--remove" ]; then rm -f "$PLIST"; echo "removed $LABEL"; exit 0; fi

mkdir -p "$HOME/Library/LaunchAgents" "$REPO/data/processed/_discover"
CMD="cd \"$REPO\" && { date; scrapers/freshness_local.sh; } >> $LOG 2>&1 \
&& /usr/bin/osascript -e 'display notification \"賽事偵查完成,coverage.json 已更新(尚未提交)\" with title \"tw-cycling-data\"' \
|| /usr/bin/osascript -e 'display notification \"賽事偵查失敗,請看 $LOG\" with title \"tw-cycling-data\"'"

esc() { sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>-c</string><string>$(printf '%s' "$CMD" | esc)</string></array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>30</integer></dict>
    <dict><key>Weekday</key><integer>4</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>30</integer></dict>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
</dict>
</plist>
PL
plutil -lint "$PLIST" >/dev/null
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "installed $LABEL (Mon/Thu 08:30) -> $PLIST"
echo "log: $REPO/$LOG"
