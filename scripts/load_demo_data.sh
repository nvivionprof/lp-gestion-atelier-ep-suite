#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

FROM_INSTALL=0
if [ "${1:-}" = "--from-install" ]; then FROM_INSTALL=1; fi

log(){ echo "[$(date +%H:%M:%S)] $*"; }
run_manage(){ local service="$1"; shift; docker compose run --rm "$service" python manage.py "$@"; }

if ! docker compose version >/dev/null 2>&1; then
  echo "ERREUR : Docker Compose v2 n'est pas disponible." >&2
  exit 1
fi

log "Chargement des données de démonstration LP Suite."
log "Usage normal : appelé automatiquement uniquement par ./install.sh --mode install si la démo a été acceptée."
log "Usage manuel possible après coup, sous responsabilité administrateur."
log "Les commandes sont tolérantes : un module absent ou une seed absente ne bloque pas l'ensemble."

if [ -f imports/base_demo_lp_core.xlsx ]; then
  log "LP Core : import imports/base_demo_lp_core.xlsx"
  run_manage lp-core-app import_users_xlsx /imports/base_demo_lp_core.xlsx || true
fi

log "LP Core : seed_core de consolidation"
ADMIN_USER="$(awk -F= '$1=="LP_CORE_ADMIN_USERNAME"{print $2}' .env | tail -n1)"
ADMIN_PASS="$(awk -F= '$1=="LP_CORE_ADMIN_PASSWORD"{print $2}' .env | tail -n1)"
if [ -n "${ADMIN_PASS:-}" ]; then
  docker compose run --rm lp-core-app python manage.py seed_core --admin-username "${ADMIN_USER:-admin}" --admin-password "$ADMIN_PASS" || true
else
  run_manage lp-core-app seed_core || true
fi

log "ToolMag : référentiels et démo"
run_manage toolmag-app seed_referentials || true
run_manage toolmag-app seed_demo || true

log "Safety Manager : démo / référentiels"
run_manage safety-app seed_safety_manager || true

log "PedaShop : démo / référentiels"
run_manage pedashop-app seed_pedashop || true

log "System Manager : démo / référentiels"
run_manage system-manager-app seed_system_manager || true

log "TP Manager : démo / référentiels"
run_manage tpmanager-app seed_tp_manager || true
run_manage tpmanager-app seed_tpmanager_v2 || true
run_manage tpmanager-app seed_sequence_manager || true
run_manage tpmanager-app seed_evaluation_demo || true

log "PFMP Manager : démo / référentiels"
run_manage pfmp-app seed_pfmp_manager || true

log "Synchronisation post-démo vers LP Core"
docker compose exec -T toolmag-app python manage.py sync_lp_core_users || true
docker compose exec -T safety-app python manage.py sync_lp_core_users || true
docker compose exec -T pedashop-app python manage.py sync_lp_core_users || true
docker compose exec -T system-manager-app python manage.py sync_lp_core_users || true
docker compose exec -T tpmanager-app python manage.py sync_lp_core_users || true
docker compose exec -T pfmp-app python manage.py sync_lp_core_users || true

log "Chargement démo terminé."
