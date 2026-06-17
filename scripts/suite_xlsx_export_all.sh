#!/usr/bin/env bash
set -euo pipefail

EXPORT_DIR="${1:-./exports/xlsx-$(date +%F_%H%M)}"
mkdir -p "$EXPORT_DIR"

run_export() {
  local service="$1"
  local prefix="$2"

  if ! docker compose ps --services | grep -qx "$service"; then
    echo "[SKIP] Service absent : $service"
    return 0
  fi

  echo "[EXPORT] $service -> $EXPORT_DIR/${prefix}.xlsx"
  docker compose exec "$service" python manage.py suite_xlsx export --output "/tmp/${prefix}.xlsx"
  docker cp "$(docker compose ps -q "$service"):/tmp/${prefix}.xlsx" "$EXPORT_DIR/${prefix}.xlsx"
}

run_template() {
  local service="$1"
  local prefix="$2"

  if ! docker compose ps --services | grep -qx "$service"; then
    return 0
  fi

  echo "[MODELE] $service -> $EXPORT_DIR/${prefix}_modele.xlsx"
  docker compose exec "$service" python manage.py suite_xlsx template --output "/tmp/${prefix}_modele.xlsx"
  docker cp "$(docker compose ps -q "$service"):/tmp/${prefix}_modele.xlsx" "$EXPORT_DIR/${prefix}_modele.xlsx"
}

run_export lp-core-app lp_core
run_export toolmag-app toolmag
run_export safety-app safety
run_export pedashop-app pedashop
run_export system-manager-app system_manager
run_export tpmanager-app tpmanager
run_export pfmp-app pfmp

run_template lp-core-app lp_core
run_template toolmag-app toolmag
run_template safety-app safety
run_template pedashop-app pedashop
run_template system-manager-app system_manager
run_template tpmanager-app tpmanager
run_template pfmp-app pfmp

echo
echo "Exports XLSX terminés : $EXPORT_DIR"
ls -lh "$EXPORT_DIR"
