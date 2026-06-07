#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh
MODULE="$(norm_module "${1:-all}")" || { echo "Module inconnu: ${1:-}" >&2; exit 1; }
if [ "$MODULE" = "all" ]; then
  dc restart lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app lp-gateway
else
  service="$(module_service "$MODULE")"
  dc restart "$service"
fi
