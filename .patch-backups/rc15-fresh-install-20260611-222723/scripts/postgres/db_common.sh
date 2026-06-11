#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
SUITE_ROOT="$(pwd)"

env_get(){
  local key="$1" default="${2:-}"
  local value=""
  if [ -f .env ]; then
    value="$(awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n 1)"
  fi
  printf '%s' "${value:-$default}"
}

dc(){ docker compose --env-file .env "$@"; }

POSTGRES_SERVICE="$(env_get POSTGRES_SERVICE postgres)"
POSTGRES_USER="$(env_get POSTGRES_USER lp_suite_user)"
POSTGRES_DB="$(env_get POSTGRES_DB lp_core)"
POSTGRES_PASSWORD="$(env_get POSTGRES_PASSWORD '')"

MODULES=(lp-core toolmag safety pedashop system-manager tpmanager pfmp)

module_db(){
  case "$1" in
    lp-core|core|lp_core|lp-core-app) echo "$(env_get LP_CORE_DB_NAME lp_core)" ;;
    toolmag|toolmag-app) echo "$(env_get TOOLMAG_DB_NAME toolmag)" ;;
    safety|safety-app|safety-manager) echo "$(env_get SAFETY_DB_NAME safety)" ;;
    pedashop|pedashop-app) echo "$(env_get PEDASHOP_DB_NAME pedashop)" ;;
    system-manager|system|system-manager-app) echo "$(env_get SYSTEM_MANAGER_DB_NAME system_manager)" ;;
    tpmanager|tp|tp-manager|tpmanager-app) echo "$(env_get TPMANAGER_DB_NAME tpmanager)" ;;
    pfmp|pfmp-app|pfmp-manager) echo "$(env_get PFMP_DB_NAME pfmp)" ;;
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
  dc up -d "$POSTGRES_SERVICE" >/dev/null
  dc exec -T "$POSTGRES_SERVICE" pg_isready -U "$POSTGRES_USER" -d "${POSTGRES_DB:-lp_core}" >/dev/null
}

safe_db_name(){
  case "$1" in
    *[!a-zA-Z0-9_-]*|'') echo "Nom de base interdit: $1" >&2; return 1 ;;
    *) return 0 ;;
  esac
}

pg_exec(){
  dc exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_SERVICE" "$@"
}

create_db_if_missing(){
  local db="$1"
  safe_db_name "$db"
  pg_exec sh -lc "psql -U '$POSTGRES_USER' -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$db'\" | grep -q 1 || createdb -U '$POSTGRES_USER' '$db'"
}
