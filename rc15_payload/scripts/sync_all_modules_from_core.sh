#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

for svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
  log "Synchronisation LP Core -> $svc"
  run_manage "$svc" sync_lp_core_users || warn "sync_lp_core_users indisponible ou en erreur pour $svc"
 done
