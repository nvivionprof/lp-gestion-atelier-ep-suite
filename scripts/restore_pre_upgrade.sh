#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
BACKUP_ZIP="${1:-}"
if [[ -z "$BACKUP_ZIP" ]]; then
  BACKUP_ZIP="$(find backups/pre_upgrade -type f -name 'lp-suite-full-*.zip' 2>/dev/null | sort | tail -n 1 || true)"
fi
if [[ -z "$BACKUP_ZIP" || ! -f "$BACKUP_ZIP" ]]; then
  echo "Aucune sauvegarde pré-mise-à-jour ZIP trouvée." >&2
  echo "Usage : $0 backups/pre_upgrade/lp-suite-full-YYYYMMDD-HHMMSS.zip" >&2
  exit 1
fi

echo "Retour arrière vers : $BACKUP_ZIP"
read -rp "Tape RESTAURER pour confirmer : " CONFIRM
if [[ "$CONFIRM" != "RESTAURER" ]]; then
  echo "Restauration annulée."
  exit 0
fi

exec "$PROJECT_DIR/scripts/restore_full_backup.sh" "$BACKUP_ZIP"
