#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
[[ -f "${ROOT_DIR}/docker-compose.yml" ]] || ROOT_DIR="${SCRIPT_DIR}"
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh

MODULE="all"
RUN_SEEDS=1
RUN_STATIC=1
usage(){
  cat <<'HELP'
Usage : ./scripts/migrate_all.sh [--module <module>] [--skip-seed] [--skip-static]
Modules : all, lp-core, toolmag, safety, pedashop, system-manager, tpmanager, pfmp
HELP
}
while [ $# -gt 0 ]; do
  case "$1" in
    --module) MODULE="${2:-}"; shift 2;;
    --skip-seed) RUN_SEEDS=0; shift;;
    --skip-static) RUN_STATIC=0; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Option inconnue : $1" >&2; usage >&2; exit 1;;
  esac
done
log(){ echo "[$(date +%H:%M:%S)] $*"; }
service_exists(){ dc config --services 2>/dev/null | grep -qx "$1"; }
service_running(){ [ -n "$(dc ps -q "$1" 2>/dev/null || true)" ]; }
exec_manage(){
  local service="$1"; shift
  if service_exists "$service" && service_running "$service"; then
    dc exec -T "$service" python manage.py "$@"
  else
    log "Service absent ou non démarré, étape ignorée : $service $*"
  fi
}
run_migrate(){
  local service="$1" module="$2"
  create_db_if_missing "$(module_db "$module")"
  if service_exists "$service"; then
    if ! service_running "$service"; then
      log "Démarrage du service pour migrations : $service"
      dc up -d "$service"
    fi
    log "Migrations Django : $service"
    exec_manage "$service" migrate --noinput
    if [ "$RUN_STATIC" = "1" ]; then exec_manage "$service" collectstatic --noinput || true; fi
  else
    log "Service non défini dans docker-compose : $service"
  fi
}
MODULE="$(norm_module "$MODULE")"
run_module(){
  local module="$1" service
  service="$(module_service "$module")"
  run_migrate "$service" "$module"
  if [ "$RUN_SEEDS" = "1" ]; then
    case "$module" in
      lp-core) ;;
      toolmag) exec_manage toolmag-app sync_lp_core_users || true ;;
      safety) exec_manage safety-app sync_lp_core_users || true; exec_manage safety-app seed_safety_manager || true ;;
      pedashop) exec_manage pedashop-app sync_lp_core_users || true; exec_manage pedashop-app seed_pedashop || true; exec_manage pedashop-app pedashop_recalculate_stock_alerts || true; exec_manage pedashop-app pedashop_check_integrity || true ;;
      system-manager) exec_manage system-manager-app sync_lp_core_users || true; exec_manage system-manager-app seed_system_manager || true ;;
      tpmanager) exec_manage tpmanager-app sync_lp_core_users || true; exec_manage tpmanager-app sync_system_manager || true; exec_manage tpmanager-app seed_tp_manager || true; exec_manage tpmanager-app seed_tpmanager_v2 || true; exec_manage tpmanager-app seed_sequence_manager || true ;;
      pfmp) exec_manage pfmp-app sync_lp_core_users || true; exec_manage pfmp-app seed_pfmp_manager || true ;;
    esac
  fi
}
ensure_postgres
if [ "$MODULE" = "all" ]; then
  for m in "${MODULES[@]}"; do run_module "$m"; done
else
  run_module "$MODULE"
fi
log "Migrations terminées. Module : $MODULE"
