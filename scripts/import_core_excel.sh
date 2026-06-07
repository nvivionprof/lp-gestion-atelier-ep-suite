#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ $# -lt 1 ]; then
  echo "Usage : ./scripts/import_core_excel.sh imports/mon_fichier.xlsx" >&2
  exit 1
fi
INPUT="$1"
BASENAME="$(basename "$INPUT")"
if [[ "$INPUT" != /imports/* ]]; then
  mkdir -p imports
  cp "$INPUT" "imports/$BASENAME"
  CONTAINER_PATH="/imports/$BASENAME"
else
  CONTAINER_PATH="$INPUT"
fi
docker compose exec -T lp-core-app python manage.py import_users_xlsx "$CONTAINER_PATH"
docker compose exec -T toolmag-app python manage.py sync_lp_core_users || true
echo "Import terminé et synchronisation ToolMag demandée."
