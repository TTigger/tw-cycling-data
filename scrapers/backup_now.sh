#!/bin/bash
# One encrypted backup right now (master.json + raw caches), then a restore
# drill on the archive it made. Secrets come from the keychain (keychain_env.sh).
#   bash scrapers/backup_now.sh
set -euo pipefail
cd "$(dirname "$0")/.."
. scrapers/keychain_env.sh
if [ -z "${TWCD_BACKUP_PASSPHRASE:-}" ]; then
  echo "沒有找到備份密碼。先執行:security add-generic-password -a \"\$USER\" -s twcd-backup-passphrase -w"
  exit 1
fi
UPLOAD=--no-upload; [ -n "${R2_ACCOUNT_ID:-}" ] && UPLOAD=
.venv/bin/python scrapers/backup.py --keep 2 --include data/raw_archive --include data/raw --include data/pdf $UPLOAD
latest=$(ls -t data/backups/master-*.zip | head -1)
.venv/bin/python scrapers/backup.py --verify "$latest" | head -3
