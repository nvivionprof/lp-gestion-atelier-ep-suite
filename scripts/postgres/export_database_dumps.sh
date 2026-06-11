#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/db_common.sh"

DEST="${1:-}"
MODULE="${2:-all}"
if [ -z "$DEST" ]; then
  echo "Usage: $0 <destination-dir> [module|all]" >&2
  exit 1
fi
MODULE="$(norm_module "$MODULE")" || { echo "Module inconnu: $MODULE" >&2; exit 1; }
mkdir -p "$DEST/databases"
ensure_postgres

export_one(){
  local module="$1"
  local db
  db="$(module_db "$module")"
  safe_db_name "$db"
  create_db_if_missing "$db"
  echo "Export PostgreSQL: $module -> $db"
  pg_exec pg_dump -U "$POSTGRES_USER" -d "$db" -Fc --no-owner --no-privileges > "$DEST/databases/${module}.dump"
  cat > "$DEST/databases/${module}.json" <<EOF
{"module":"$module","database":"$db","format":"pg_dump_custom","created_at":"$(date -Iseconds)"}
EOF
}

if [ "$MODULE" = "all" ]; then
  for module in "${MODULES[@]}"; do export_one "$module"; done
else
  export_one "$MODULE"
fi
