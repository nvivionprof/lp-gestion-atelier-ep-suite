#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

require_project_files
wait_postgres 180

for svc in "${LP_MODULE_SERVICES[@]}"; do
  log "Migrations Django : $svc"
  run_manage "$svc" migrate
 done
log "Migrations terminées."
