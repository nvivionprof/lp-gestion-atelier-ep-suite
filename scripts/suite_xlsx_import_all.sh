#!/usr/bin/env bash
set -euo pipefail

IMPORT_DIR="${1:-./exports/latest}"

if [ ! -d "$IMPORT_DIR" ]; then
  echo "Dossier introuvable : $IMPORT_DIR"
  exit 1
fi

run_import() {
  local service="$1"
  local prefix="$2"
  local file="$IMPORT_DIR/${prefix}.xlsx"

  if [ ! -f "$file" ]; then
    echo "[SKIP] Fichier absent : $file"
    return 0
  fi

  if ! docker compose ps --services | grep -qx "$service"; then
    echo "[SKIP] Service absent : $service"
    return 0
  fi

  echo "[IMPORT DRY-RUN] $service <- $file"
  docker cp "$file" "$(docker compose ps -q "$service"):/tmp/${prefix}.xlsx"
  docker compose exec "$service" python manage.py suite_xlsx import --input "/tmp/${prefix}.xlsx" --dry-run

  echo "[IMPORT REEL] $service <- $file"
  docker compose exec "$service" python manage.py suite_xlsx import --input "/tmp/${prefix}.xlsx"
}

run_import lp-core-app lp_core
run_import toolmag-app toolmag
run_import safety-app safety
run_import pedashop-app pedashop
run_import system-manager-app system_manager
run_import tpmanager-app tpmanager
run_import pfmp-app pfmp

echo
echo "Imports XLSX terminés."
