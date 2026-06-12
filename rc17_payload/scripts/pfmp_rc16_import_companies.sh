#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-simulation}"
KEY="${2:-code_entreprise}"
FILE="/imports/pfmp_manager_base_entreprises_fusionnee.xlsx"
CONFIRM="${3:-}"
if [[ "$MODE" == "replace_all" || "$MODE" == "delete_all_then_import" ]]; then
  if [[ "$CONFIRM" != "CONFIRMER IMPORT DESTRUCTIF" ]]; then
    echo "Mode destructif refusé. Exemple :"
    echo "bash scripts/pfmp_rc16_import_companies.sh replace_all code_entreprise 'CONFIRMER IMPORT DESTRUCTIF'"
    exit 2
  fi
fi

docker compose --env-file .env exec -T pfmp-app python manage.py import_pfmp_companies_xlsx \
  --file "$FILE" \
  --mode "$MODE" \
  --key "$KEY" \
  --confirm "$CONFIRM"
