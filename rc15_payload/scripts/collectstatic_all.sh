#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

require_project_files
for svc in "${LP_MODULE_SERVICES[@]}"; do
  log "Collectstatic : $svc"
  run_manage "$svc" collectstatic --noinput || warn "collectstatic non bloquant pour $svc"
 done
log "Collectstatic terminé."
