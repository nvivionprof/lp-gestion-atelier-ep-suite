#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh
MODULE="$(norm_module "${1:-all}")" || { echo "Module inconnu: ${1:-}" >&2; exit 1; }
sync_one(){
  local module="$1" service
  [ "$module" = "lp-core" ] && return 0
  service="$(module_service "$module")"
  dc up -d "$service" >/dev/null
  echo "Synchronisation LP Core -> $service"
  dc exec -T "$service" python manage.py sync_lp_core_users
}
if [ "$MODULE" = "all" ]; then for m in toolmag safety pedashop system-manager tpmanager pfmp; do sync_one "$m"; done; else sync_one "$MODULE"; fi
