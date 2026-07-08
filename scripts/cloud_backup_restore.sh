#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SUITE_ROOT="$(pwd)"

CLOUD_PATH="${1:-}"
BACKUP_KIND="${2:-auto}"
MODULE="${3:-auto}"

if [[ -z "$CLOUD_PATH" || "$CLOUD_PATH" == /* || "$CLOUD_PATH" == *".."* || "$CLOUD_PATH" != *.zip ]]; then
  echo "ERREUR : chemin cloud invalide : $CLOUD_PATH" >&2
  exit 1
fi

if [[ -f "$SUITE_ROOT/lp-core-db/data/backup-policy.env" ]]; then
  set -a
  . "$SUITE_ROOT/lp-core-db/data/backup-policy.env"
  set +a
fi

if [[ "${BACKUP_CLOUD_ENABLED:-0}" != "1" || "${BACKUP_CLOUD_RESTORE_ENABLED:-1}" != "1" ]]; then
  echo "ERREUR : restauration cloud désactivée." >&2
  exit 1
fi

REMOTE="${BACKUP_CLOUD_RCLONE_REMOTE:-gdrive}"
REMOTE_PATH="${BACKUP_CLOUD_REMOTE_PATH:-LP-Gestion-Atelier-Suite/backups}"
REMOTE_PATH="${REMOTE_PATH#/}"
REMOTE_PATH="${REMOTE_PATH%/}"
SOURCE="${REMOTE}:${REMOTE_PATH}/${CLOUD_PATH}"

mkdir -p "$SUITE_ROOT/backups/cloud-restore"
DEST="$SUITE_ROOT/backups/cloud-restore/$(basename "$CLOUD_PATH")"

echo "Téléchargement cloud : $SOURCE -> $DEST"
rclone copyto "$SOURCE" "$DEST"

if [[ "$BACKUP_KIND" == "database" || "$CLOUD_PATH" == databases/* || "$(basename "$CLOUD_PATH")" == lp-suite-db-* ]]; then
  echo "Restauration base PostgreSQL depuis sauvegarde cloud."
  "$SUITE_ROOT/scripts/postgres/restore_database_backup.sh" "$DEST" "$MODULE"
else
  echo "Restauration complète depuis sauvegarde cloud."
  "$SUITE_ROOT/scripts/restore_full_backup.sh" "$DEST"
fi
