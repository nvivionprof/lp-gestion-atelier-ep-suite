#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh
MODULE="$(norm_module "${1:-all}")" || { echo "Module inconnu: ${1:-}" >&2; exit 1; }
collect_one(){
  local module="$1" service
  service="$(module_service "$module")"
  dc up -d "$service" >/dev/null
  echo "Collectstatic : $service"
  dc exec -T "$service" python manage.py collectstatic --noinput
}
if [ "$MODULE" = "all" ]; then for m in "${MODULES[@]}"; do collect_one "$m"; done; else collect_one "$MODULE"; fi
