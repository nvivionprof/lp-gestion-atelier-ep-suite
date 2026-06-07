#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

MODULE="all"
RUN_SEEDS=1
RUN_STATIC=1

usage(){
  cat <<'EOF'
Usage : ./scripts/migrate_all.sh [--module <module>] [--skip-seed] [--skip-static]
Modules : all, lp-core, toolmag, safety, pedashop, system-manager, tpmanager, pfmp
EOF
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
service_exists(){ docker compose config --services 2>/dev/null | grep -qx "$1"; }
service_running(){ [ -n "$(docker compose ps -q "$1" 2>/dev/null || true)" ]; }
exec_manage(){
  local service="$1"; shift
  if service_exists "$service" && service_running "$service"; then
    docker compose exec -T "$service" python manage.py "$@"
  else
    log "Service absent ou non démarré, étape ignorée : $service $*"
  fi
}
run_migrate(){
  local service="$1"
  if service_exists "$service"; then
    if ! service_running "$service"; then
      log "Démarrage du service pour migrations : $service"
      docker compose up -d "$service"
    fi
    log "Migrations Django : $service"
    exec_manage "$service" migrate --noinput
    if [ "$RUN_STATIC" = "1" ]; then
      exec_manage "$service" collectstatic --noinput || true
    fi
  else
    log "Service non défini dans docker-compose : $service"
  fi
}

norm_module(){
  case "$1" in
    core|lp_core|lp-core|lp-core-app) echo lp-core;;
    toolmag|toolmag-app) echo toolmag;;
    safety|safety-manager|safety-app) echo safety;;
    pedashop|peda-shop|pedashop-app) echo pedashop;;
    system|system-manager|system-manager-app) echo system-manager;;
    tp|tpmanager|tp-manager|tpmanager-app) echo tpmanager;;
    pfmp|pfmp-manager|pfmp-app) echo pfmp;;
    all|*) echo "$1";;
  esac
}
MODULE="$(norm_module "$MODULE")"

run_module(){
  local module="$1"
  case "$module" in
    lp-core)
      run_migrate lp-core-app
      ;;
    toolmag)
      run_migrate toolmag-app
      log "Synchronisation LP Core → ToolMag"
      exec_manage toolmag-app sync_lp_core_users || true
      ;;
    safety)
      run_migrate safety-app
      if [ "$RUN_SEEDS" = "1" ]; then
        log "Synchronisation LP Core → Safety"
        exec_manage safety-app sync_lp_core_users || true
        exec_manage safety-app seed_safety_manager || true
      fi
      ;;
    pedashop)
      run_migrate pedashop-app
      if [ "$RUN_SEEDS" = "1" ]; then
        log "Synchronisation LP Core → PedaShop"
        exec_manage pedashop-app sync_lp_core_users || true
        exec_manage pedashop-app seed_pedashop || true
        exec_manage pedashop-app pedashop_recalculate_stock_alerts || true
        exec_manage pedashop-app pedashop_check_integrity || true
      fi
      ;;
    system-manager)
      run_migrate system-manager-app
      if [ "$RUN_SEEDS" = "1" ]; then
        log "Synchronisation LP Core → System Manager"
        exec_manage system-manager-app sync_lp_core_users || true
        exec_manage system-manager-app seed_system_manager || true
      fi
      ;;
    tpmanager)
      run_migrate tpmanager-app
      if [ "$RUN_SEEDS" = "1" ]; then
        log "Synchronisation LP Core / System Manager → TP Manager"
        exec_manage tpmanager-app sync_lp_core_users || true
        exec_manage tpmanager-app sync_system_manager || true
        exec_manage tpmanager-app seed_tp_manager || true
        exec_manage tpmanager-app seed_tpmanager_v2 || true
        exec_manage tpmanager-app seed_sequence_manager || true
      fi
      ;;
    pfmp)
      run_migrate pfmp-app
      if [ "$RUN_SEEDS" = "1" ]; then
        log "Synchronisation LP Core → PFMP Manager"
        exec_manage pfmp-app sync_lp_core_users || true
        exec_manage pfmp-app seed_pfmp_manager || true
      fi
      ;;
    *) echo "Module inconnu : $module" >&2; exit 1;;
  esac
}

if [ "$MODULE" = "all" ]; then
  run_module lp-core
  run_module toolmag
  run_module safety
  run_module pedashop
  run_module system-manager
  run_module tpmanager
  run_module pfmp
else
  run_module "$MODULE"
fi

log "Migrations terminées. Module : $MODULE"
