#!/usr/bin/env bash
# Fonctions communes LP Gestion Atelier EP Suite.
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

LP_MODULE_SERVICES=(
  lp-core-app
  toolmag-app
  safety-app
  pedashop-app
  system-manager-app
  tpmanager-app
  pfmp-app
)

LP_ALL_CONTAINERS=(
  lp-suite-postgres
  lp-core-app
  toolmag-app
  safety-app
  pedashop-app
  system-manager-app
  tpmanager-app
  pfmp-app
  lp-gateway
  suite-admin-agent
  suite-backup-scheduler
)

LP_DATA_DIRS=(
  postgres-db/data
  lp-core-db/data
  toolmag-db/data
  safety-db/data
  pedashop-db/data
  system-manager-db/data
  tpmanager-db/data
  pfmp-db/data
)

log(){ echo "[$(date +%H:%M:%S)] $*"; }
warn(){ echo "[$(date +%H:%M:%S)] AVERTISSEMENT : $*" >&2; }
fatal(){ echo "[$(date +%H:%M:%S)] ERREUR : $*" >&2; exit 1; }

dc(){ docker compose --env-file .env "$@"; }

env_get(){
  local key="$1"
  [ -f .env ] || return 0
  awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n1
}

upsert_env(){
  local key="$1" value="$2" file="${3:-.env}"
  touch "$file"
  if grep -qE "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

require_project_files(){
  [ -f docker-compose.yml ] || fatal "docker-compose.yml introuvable. Lance la commande depuis la racine du projet."
  [ -f .env ] || fatal ".env introuvable. Lance d'abord install.sh ou crée .env depuis .env.example."
}

require_docker_compose(){
  docker compose version >/dev/null 2>&1 || fatal "Docker Compose v2 n'est pas disponible."
}

current_version(){
  if [ -f VERSION ]; then tr -d '\r\n' < VERSION; else echo "UNKNOWN"; fi
}

check_disk_space(){
  local min_mb="${1:-1024}"
  local avail
  avail="$(df -Pm . | awk 'NR==2{print $4}')"
  if [ "${avail:-0}" -lt "$min_mb" ]; then
    fatal "Espace disque insuffisant : ${avail} Mo disponibles, ${min_mb} Mo requis."
  fi
}

check_compose_services(){
  local cfg
  cfg="$(dc config --services 2>/dev/null || true)"
  [ -n "$cfg" ] || fatal "docker compose config ne renvoie aucun service. Vérifie .env et docker-compose.yml."
  for svc in postgres lp-gateway "${LP_MODULE_SERVICES[@]}"; do
    if ! grep -qx "$svc" <<<"$cfg"; then
      warn "Service absent du compose : $svc"
    fi
  done
}

wait_postgres(){
  local timeout="${1:-90}" elapsed=0
  log "Attente PostgreSQL healthy / accessible..."
  until dc exec -T postgres sh -lc 'pg_isready -U "$POSTGRES_USER" -d postgres >/dev/null 2>&1'; do
    sleep 3
    elapsed=$((elapsed+3))
    if [ "$elapsed" -ge "$timeout" ]; then
      dc ps postgres || true
      dc logs --tail=80 postgres || true
      fatal "PostgreSQL non disponible après ${timeout}s."
    fi
  done
}

check_http_routes(){
  log "Contrôle HTTP rapide local serveur"
  for url in \
    http://localhost:9000/ \
    http://localhost:9000/toolmag/ \
    http://localhost:9000/safety/ \
    http://localhost:9000/pedashop/ \
    http://localhost:9000/system/ \
    http://localhost:9000/tpmanager/ \
    http://localhost:9000/pfmp/
  do
    echo "===== $url ====="
    curl -sSI "$url" | head -n 8 || true
  done
}

run_manage(){
  local service="$1"; shift
  if dc ps --services --filter status=running | grep -qx "$service"; then
    dc exec -T "$service" python manage.py "$@"
  else
    dc run --rm --no-deps "$service" python manage.py "$@"
  fi
}

run_manage_env(){
  local service="$1"; shift
  local -a env_args=()
  while [ "$#" -gt 0 ] && [[ "$1" == *=* ]]; do
    env_args+=("-e" "$1")
    shift
  done
  if dc ps --services --filter status=running | grep -qx "$service"; then
    dc exec -T "${env_args[@]}" "$service" python manage.py "$@"
  else
    dc run --rm --no-deps "${env_args[@]}" "$service" python manage.py "$@"
  fi
}

stop_known_lp_containers(){
  log "Suppression des conteneurs LP Suite connus, si présents"
  for c in "${LP_ALL_CONTAINERS[@]}"; do
    docker rm -f "$c" >/dev/null 2>&1 || true
  done
}

fresh_wipe_local_data(){
  log "Suppression des données locales LP Suite de cette installation"
  for d in "${LP_DATA_DIRS[@]}"; do
    rm -rf "$d"
    mkdir -p "$d"
  done
}

fresh_reset_installation(){
  require_project_files
  log "Arrêt Docker Compose avec suppression des volumes/orphelins"
  dc down -v --remove-orphans || true
  stop_known_lp_containers
  fresh_wipe_local_data
}
