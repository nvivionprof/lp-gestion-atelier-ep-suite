#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/db_common.sh"

MODULE="${1:-all}"
MODULE="$(norm_module "$MODULE")" || { echo "Module inconnu: $MODULE" >&2; exit 1; }
ensure_postgres

if [ "$MODULE" = "all" ]; then
  for module in "${MODULES[@]}"; do
    db="$(module_db "$module")"
    echo "Vérification base PostgreSQL: $module -> $db"
    create_db_if_missing "$db"
  done
else
  db="$(module_db "$MODULE")"
  echo "Vérification base PostgreSQL: $MODULE -> $db"
  create_db_if_missing "$db"
fi
