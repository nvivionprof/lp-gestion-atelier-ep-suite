#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SUITE_ROOT="$(pwd)"
MODE="${1:-manual}"
# La politique peut être générée par LP Core dans lp-core-db/data/backup-policy.env.
[ -f .env ] && set -a && . ./.env && set +a || true
[ -f lp-core-db/data/backup-policy.env ] && set -a && . ./lp-core-db/data/backup-policy.env && set +a || true
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
STAMP="$(date +%Y%m%d-%H%M%S)"
case "$MODE" in
  daily) BACKUP_DIR="$SUITE_ROOT/backups/daily" ;;
  pre-upgrade|pre_upgrade) BACKUP_DIR="$SUITE_ROOT/backups/pre_upgrade" ;;
  pre-restore|pre_restore) BACKUP_DIR="$SUITE_ROOT/backups/pre_restore" ;;
  *) BACKUP_DIR="$SUITE_ROOT/backups/manual" ;;
esac
mkdir -p "$BACKUP_DIR" "$SUITE_ROOT/backups/tmp"
TMP="$(mktemp -d "$SUITE_ROOT/backups/tmp/full-backup-$STAMP-XXXX")"
ARCHIVE="$BACKUP_DIR/lp-suite-full-$STAMP.zip"
copy_if_exists(){
  local src="$1"
  if [[ -e "$SUITE_ROOT/$src" ]]; then
    mkdir -p "$TMP/$(dirname "$src")"
    cp -a "$SUITE_ROOT/$src" "$TMP/$src"
  fi
}
copy_if_exists ".env"
copy_if_exists "docker-compose.yml"
copy_if_exists "README.md"
copy_if_exists "docs"
for d in lp-core-db toolmag-db safety-db pedashop-db system-manager-db tpmanager-db pfmp-db media uploads ssl imports logs; do
  copy_if_exists "$d"
done

# Exports logiques PostgreSQL : plus fiables que la copie brute du volume postgres-db à chaud.
if [[ -x "$SUITE_ROOT/scripts/postgres/export_database_dumps.sh" ]]; then
  "$SUITE_ROOT/scripts/postgres/export_database_dumps.sh" "$TMP" all || echo "Avertissement : export PostgreSQL impossible." >&2
fi

cat > "$TMP/manifest.json" <<BACKUP_MANIFEST_EOF
{
  "suite": "lp-gestion-atelier-ep-suite",
  "backup_type": "full",
  "created_at": "$(date -Iseconds)",
  "mode": "$MODE",
  "retention_days": $RETENTION_DAYS,
  "hostname": "$(hostname)",
  "suite_root": "$SUITE_ROOT",
  "contains": ["env", "postgresql_dumps", "media", "uploads", "ssl", "imports", "logs", "metadata"],
  "restore_note": "Installer une version neuve compatible, puis restaurer cette archive depuis LP Core > Sauvegardes."
}
BACKUP_MANIFEST_EOF
(
  cd "$TMP"
  find . -type f ! -name checksums.sha256 -print0 | sort -z | xargs -0 sha256sum > checksums.sha256
  zip -qr "$ARCHIVE" .
)
rm -rf "$TMP"
if [[ "$MODE" == "daily" ]]; then
  find "$BACKUP_DIR" -type f -name 'lp-suite-full-*.zip' -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
fi
echo "Sauvegarde complète créée : $ARCHIVE"
