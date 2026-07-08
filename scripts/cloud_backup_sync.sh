#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SUITE_ROOT="$(pwd)"
ACTION="${1:-sync}"
FILE_PATH="${2:-}"

load_policy(){
  if [[ -f "$SUITE_ROOT/lp-core-db/data/backup-policy.env" ]]; then
    set -a
    . "$SUITE_ROOT/lp-core-db/data/backup-policy.env"
    set +a
  fi
}
load_policy

need(){ command -v "$1" >/dev/null 2>&1 || { echo "ERREUR : commande absente : $1" >&2; exit 1; }; }
need rclone

if [[ "${BACKUP_CLOUD_ENABLED:-0}" != "1" ]]; then
  echo "Cloud désactivé dans backup-policy.env."
  exit 0
fi

REMOTE="${BACKUP_CLOUD_RCLONE_REMOTE:-gdrive}"
REMOTE_PATH="${BACKUP_CLOUD_REMOTE_PATH:-LP-Gestion-Atelier-Suite/backups}"
REMOTE_PATH="${REMOTE_PATH#/}"
REMOTE_PATH="${REMOTE_PATH%/}"
TARGET="${REMOTE}:${REMOTE_PATH}"

test_cloud(){
  echo "Test cloud : $TARGET"
  rclone mkdir "$TARGET"
  TMPFILE="$(mktemp)"
  echo "lp-suite-cloud-test $(date -Iseconds)" > "$TMPFILE"
  rclone copyto "$TMPFILE" "$TARGET/.lp-suite-cloud-test.txt"
  rclone deletefile "$TARGET/.lp-suite-cloud-test.txt" || true
  rm -f "$TMPFILE"
  echo "Test cloud OK."
}

push_file(){
  local file="$1"
  if [[ -z "$file" || ! -f "$file" ]]; then
    echo "ERREUR : fichier à envoyer introuvable : $file" >&2
    exit 1
  fi
  local abs rel dest
  abs="$(readlink -f "$file")"
  case "$abs" in
    "$SUITE_ROOT"/backups/*) rel="${abs#"$SUITE_ROOT"/backups/}" ;;
    *) echo "ERREUR : fichier hors dossier backups : $abs" >&2; exit 1 ;;
  esac
  dest="$TARGET/$(dirname "$rel")"
  echo "Envoi cloud : $abs -> $dest"
  rclone mkdir "$dest"
  rclone copy "$abs" "$dest"
  echo "Envoi cloud terminé."
}

sync_all(){
  echo "Synchronisation cloud vers $TARGET"
  rclone mkdir "$TARGET"

  if [[ "${BACKUP_CLOUD_SYNC_FULL:-1}" = "1" ]]; then
    for d in daily manual pre_upgrade pre_restore; do
      [[ -d "$SUITE_ROOT/backups/$d" ]] && rclone copy "$SUITE_ROOT/backups/$d" "$TARGET/$d" --include "*.zip"
    done
  fi

  if [[ "${BACKUP_CLOUD_SYNC_DATABASE:-1}" = "1" ]]; then
    [[ -d "$SUITE_ROOT/backups/databases" ]] && rclone copy "$SUITE_ROOT/backups/databases" "$TARGET/databases" --include "*.zip"
  fi

  echo "Synchronisation cloud terminée."
}

case "$ACTION" in
  test) test_cloud ;;
  push) push_file "$FILE_PATH" ;;
  sync) sync_all ;;
  *) echo "Usage: $0 test|sync|push [fichier.zip]" >&2; exit 1 ;;
esac
