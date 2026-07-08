#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/db_common.sh"

MODULE="$(norm_module "${1:-all}")" || { echo "Module inconnu: ${1:-}" >&2; exit 1; }
MODE="${2:-manual}"
STAMP="$(date +%Y%m%d-%H%M%S)"
case "$MODE" in
  daily) BACKUP_DIR="$SUITE_ROOT/backups/databases/daily" ;;
  pre-upgrade|pre_upgrade) BACKUP_DIR="$SUITE_ROOT/backups/databases/pre_upgrade" ;;
  pre-restore|pre_restore) BACKUP_DIR="$SUITE_ROOT/backups/databases/pre_restore" ;;
  *) BACKUP_DIR="$SUITE_ROOT/backups/databases/manual" ;;
esac
mkdir -p "$BACKUP_DIR" "$SUITE_ROOT/backups/tmp"
TMP="$(mktemp -d "$SUITE_ROOT/backups/tmp/db-backup-$STAMP-XXXX")"
ARCHIVE="$BACKUP_DIR/lp-suite-db-${MODULE}-${STAMP}.zip"

"$SCRIPT_DIR/export_database_dumps.sh" "$TMP" "$MODULE"

cat > "$TMP/manifest.json" <<EOF
{
  "suite": "lp-gestion-atelier-ep-suite",
  "backup_type": "database_${MODULE}",
  "package_type": "database_backup",
  "module": "$MODULE",
  "created_at": "$(date -Iseconds)",
  "mode": "$MODE",
  "source_version": "$(cat "$SUITE_ROOT/VERSION" 2>/dev/null | tr -d '\n' || true)",
  "restore_note": "Restaurer depuis LP Core > Sauvegardes ou via scripts/postgres/restore_database_backup.sh."
}
EOF
(
  cd "$TMP"
  find . -type f ! -name checksums.sha256 -print0 | sort -z | xargs -0 sha256sum > checksums.sha256
  zip -qr "$ARCHIVE" .
)
rm -rf "$TMP"
echo "Sauvegarde base créée : $ARCHIVE"
if [[ -x "$SUITE_ROOT/scripts/cloud_backup_sync.sh" ]]; then
  "$SUITE_ROOT/scripts/cloud_backup_sync.sh" push "$ARCHIVE" || echo "Avertissement : upload cloud impossible." >&2
fi
