#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

FROM_INSTALL=0
if [ "${1:-}" = "--from-install" ]; then FROM_INSTALL=1; fi

log "Chargement des données de démonstration LP Suite."
log "Les commandes sont tolérantes : une seed absente ne bloque pas l'ensemble."

if [ -f imports/base_demo_lp_core.xlsx ]; then
  CORE_DEMO_PRESENT="$(run_manage lp-core-app shell -c "from core.models import CoreUser; print(CoreUser.objects.filter(username='PROF-0001').exists())" 2>/dev/null | tail -n 1 || true)"
  if [ "$CORE_DEMO_PRESENT" = "True" ]; then
    log "LP Core : utilisateurs démo déjà présents, import XLSX ignoré."
  else
    log "LP Core : import imports/base_demo_lp_core.xlsx"
    run_manage lp-core-app import_users_xlsx /imports/base_demo_lp_core.xlsx || warn "Import XLSX LP Core ignoré/échoué"
  fi
fi

log "LP Core : seed_core"
ADMIN_USER="$(env_get LP_CORE_ADMIN_USERNAME)"; ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="$(env_get LP_CORE_ADMIN_PASSWORD)"; ADMIN_PASS="${ADMIN_PASS:-admin}"
run_manage lp-core-app seed_core --admin-username "$ADMIN_USER" --admin-password "$ADMIN_PASS" || warn "seed_core en erreur/non disponible"

log "ToolMag : référentiels et démo"
run_manage toolmag-app seed_referentials || warn "seed_referentials en erreur/non disponible"
run_manage toolmag-app seed_demo || warn "seed_demo en erreur/non disponible"

log "Safety Manager : démo / référentiels"
run_manage safety-app seed_safety_manager || warn "seed_safety_manager en erreur/non disponible"

log "PedaShop : démo / référentiels"
run_manage pedashop-app seed_pedashop || warn "seed_pedashop en erreur/non disponible"

log "System Manager : démo / référentiels"
run_manage system-manager-app seed_system_manager || warn "seed_system_manager en erreur/non disponible"

log "TP Manager : démo / référentiels"
run_manage tpmanager-app seed_tp_manager || warn "seed_tp_manager en erreur/non disponible"
run_manage tpmanager-app seed_tpmanager_v2 || warn "seed_tpmanager_v2 en erreur/non disponible"
run_manage tpmanager-app seed_sequence_manager || warn "seed_sequence_manager en erreur/non disponible"
run_manage tpmanager-app seed_evaluation_demo || warn "seed_evaluation_demo en erreur/non disponible"

log "PFMP Manager : démo / référentiels"
run_manage pfmp-app seed_pfmp_manager || warn "seed_pfmp_manager en erreur/non disponible"

if [ "$FROM_INSTALL" = "1" ]; then
  log "Synchronisation post-démo différée par install.sh."
else
  bash scripts/sync_all_modules_from_core.sh || true
fi
log "Chargement démo terminé."
