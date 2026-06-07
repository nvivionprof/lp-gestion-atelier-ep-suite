#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
SUITE_ROOT="$(pwd)"
[ -f .env ] && set -a && . ./.env && set +a || true

POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-lp_suite_user}"
POSTGRES_DB="${POSTGRES_DB:-lp_core}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

MODULES=(lp-core toolmag safety pedashop system-manager tpmanager pfmp)

module_db(){
  case "$1" in
    lp-core|core|lp_core|lp-core-app) echo "${LP_CORE_DB_NAME:-lp_core}" ;;
    toolmag|toolmag-app) echo "${TOOLMAG_DB_NAME:-toolmag}" ;;
    safety|safety-app|safety-manager) echo "${SAFETY_DB_NAME:-safety}" ;;
    pedashop|pedashop-app) echo "${PEDASHOP_DB_NAME:-pedashop}" ;;
    system-manager|system|system-manager-app) echo "${SYSTEM_MANAGER_DB_NAME:-system_manager}" ;;
    tpmanager|tp|tp-manager|tpmanager-app) echo "${TPMANAGER_DB_NAME:-tpmanager}" ;;
    pfmp|pfmp-app|pfmp-manager) echo "${PFMP_DB_NAME:-pfmp}" ;;
    *) return 1 ;;
  esac
}

norm_module(){
  case "$1" in
    all|total|toutes|tous) echo all ;;
    lp-core|core|lp_core|lp-core-app) echo lp-core ;;
    toolmag|toolmag-app) echo toolmag ;;
    safety|safety-app|safety-manager) echo safety ;;
    pedashop|pedashop-app) echo pedashop ;;
    system-manager|system|system-manager-app) echo system-manager ;;
    tpmanager|tp|tp-manager|tpmanager-app) echo tpmanager ;;
    pfmp|pfmp-app|pfmp-manager) echo pfmp ;;
    *) return 1 ;;
  esac
}

module_service(){
  case "$1" in
    lp-core) echo lp-core-app ;;
    toolmag) echo toolmag-app ;;
    safety) echo safety-app ;;
    pedashop) echo pedashop-app ;;
    system-manager) echo system-manager-app ;;
    tpmanager) echo tpmanager-app ;;
    pfmp) echo pfmp-app ;;
    *) return 1 ;;
  esac
}

ensure_postgres(){
  docker compose up -d "$POSTGRES_SERVICE" >/dev/null
  docker compose exec -T "$POSTGRES_SERVICE" pg_isready -U "$POSTGRES_USER" -d "${POSTGRES_DB:-lp_core}" >/dev/null
}

safe_db_name(){
  case "$1" in
    *[!a-zA-Z0-9_-]*|'') echo "Nom de base interdit: $1" >&2; return 1 ;;
    *) return 0 ;;
  esac
}

pg_exec(){
  docker compose exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_SERVICE" "$@"
}

create_db_if_missing(){
  local db="$1"
  safe_db_name "$db"
  pg_exec sh -lc "psql -U '$POSTGRES_USER' -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$db'\" | grep -q 1 || createdb -U '$POSTGRES_USER' '$db'"
}
