# Sourced by auto_ingest.sh / backup_now.sh. Exports backup secrets from the
# login keychain (they are never written to files or the repo). Store them with
#   security add-generic-password -a "$USER" -s <name> -w
# names: twcd-backup-passphrase, twcd-r2-account-id, twcd-r2-access-key-id,
#        twcd-r2-secret-access-key   (R2 ones are optional: local backup only)
_kc() { security find-generic-password -a "$USER" -s "$1" -w 2>/dev/null; }
_v=$(_kc twcd-backup-passphrase) && export TWCD_BACKUP_PASSPHRASE="$_v"
_v=$(_kc twcd-r2-account-id) && export R2_ACCOUNT_ID="$_v"
_v=$(_kc twcd-r2-access-key-id) && export R2_ACCESS_KEY_ID="$_v"
_v=$(_kc twcd-r2-secret-access-key) && export R2_SECRET_ACCESS_KEY="$_v"
unset _v
