#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"

# Installateur interactif LP Gestion Atelier EP Suite RC14.
# Mode : installation complète SSH, pas mise à jour web.

if [ -f scripts/lp_suite_common.sh ]; then
  source scripts/lp_suite_common.sh
else
  log(){ echo "[$(date +%H:%M:%S)] $*"; }
  fatal(){ echo "ERREUR : $*" >&2; exit 1; }
fi

ask(){
  local prompt="$1" default="${2:-}" reply
  if [ -n "$default" ]; then
    read -r -p "$prompt [$default] : " reply || true
    echo "${reply:-$default}"
  else
    read -r -p "$prompt : " reply || true
    echo "$reply"
  fi
}

ask_secret(){
  local prompt="$1" default="${2:-}" reply
  if [ -n "$default" ]; then
    read -r -s -p "$prompt [valeur par défaut masquée] : " reply || true
    echo >&2
    echo "${reply:-$default}"
  else
    read -r -s -p "$prompt : " reply || true
    echo >&2
    echo "$reply"
  fi
}

gen_secret(){ tr -dc 'A-Za-z0-9_@%+=-' </dev/urandom | head -c 32; echo; }

upsert_env_local(){
  local key="$1" value="$2" file=".env"
  touch "$file"
  if grep -qE "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

require_docker_compose
[ -f docker-compose.yml ] || fatal "docker-compose.yml introuvable."

log "LP Gestion Atelier EP Suite - installation assistée RC14"
echo "Type : installation complète SSH."
echo "Ce script configure .env, démarre Docker, migre les bases, crée les admins et peut charger la démo."
echo

if [ -f .env ]; then
  echo "Un fichier .env existe déjà."
  keep="$(ask "Le conserver et seulement compléter les valeurs manquantes ? oui/non" "oui")"
  if [[ ! "$keep" =~ ^[OoYy] ]]; then
    cp -a .env ".env.backup-install-$(date +%Y%m%d-%H%M%S)"
    rm -f .env
  fi
fi

if [ ! -f .env ]; then
  if [ -f .env.example ]; then cp .env.example .env; else touch .env; fi
fi

cat <<MENU
Mode d'accès :
  1) local      : http://localhost:9000
  2) réseau     : http://IP_SERVEUR:9000
  3) domaine    : http(s)://domaine:port ou reverse-proxy
MENU
mode_choice="$(ask "Choix" "2")"
case "$mode_choice" in
  1) DEPLOY_MODE="local"; HOST="localhost:9000"; SCHEME="http"; SERVER_IP="127.0.0.1"; ENABLE_HTTPS="0" ;;
  2) DEPLOY_MODE="network"; SERVER_IP="$(ask "Adresse IP du serveur" "$(hostname -I 2>/dev/null | awk '{print $1}')")"; HOST="${SERVER_IP}:9000"; SCHEME="http"; ENABLE_HTTPS="0" ;;
  3) DEPLOY_MODE="domain"; DOMAIN="$(ask "Domaine public" "stjo-lpsuite.duckdns.org")"; HTTPS="$(ask "HTTPS actif ? oui/non" "non")"; if [[ "$HTTPS" =~ ^[OoYy] ]]; then SCHEME="https"; ENABLE_HTTPS="1"; HOST="$DOMAIN"; else SCHEME="http"; ENABLE_HTTPS="0"; HOST="${DOMAIN}:9000"; fi; SERVER_IP="$(ask "IP locale du serveur" "$(hostname -I 2>/dev/null | awk '{print $1}')")" ;;
  *) fatal "Choix invalide" ;;
esac

ADMIN_USER="$(ask "Utilisateur admin LP Core / Django" "admin")"
ADMIN_PASS="$(ask_secret "Mot de passe admin" "admin")"
POSTGRES_USER="$(ask "Utilisateur PostgreSQL" "lp_suite_user")"
POSTGRES_PASSWORD="$(ask_secret "Mot de passe PostgreSQL" "$(gen_secret)")"
SECRET_KEY="$(ask_secret "Django SECRET_KEY" "$(gen_secret)")"
DEMO="$(ask "Charger la base de démonstration ? oui/non" "oui")"

upsert_env_local LP_DEPLOY_MODE "$DEPLOY_MODE"
upsert_env_local EXPOSURE_MODE "$DEPLOY_MODE"
upsert_env_local SERVER_IP "$SERVER_IP"
upsert_env_local PUBLIC_SCHEME "$SCHEME"
upsert_env_local PUBLIC_DOMAIN "$HOST"
upsert_env_local ENABLE_HTTPS "$ENABLE_HTTPS"
upsert_env_local GATEWAY_HTTP_PORT "9000"
upsert_env_local GATEWAY_HTTPS_PORT "9443"
upsert_env_local POSTGRES_USER "$POSTGRES_USER"
upsert_env_local POSTGRES_PASSWORD "$POSTGRES_PASSWORD"
upsert_env_local POSTGRES_MULTIPLE_DATABASES "lp_core,toolmag,safety,pedashop,system_manager,tpmanager,pfmp"
upsert_env_local SECRET_KEY "$SECRET_KEY"
upsert_env_local DJANGO_SECRET_KEY "$SECRET_KEY"
upsert_env_local LP_CORE_ADMIN_USERNAME "$ADMIN_USER"
upsert_env_local LP_CORE_ADMIN_PASSWORD "$ADMIN_PASS"
upsert_env_local DJANGO_SUPERUSER_USERNAME "$ADMIN_USER"
upsert_env_local DJANGO_SUPERUSER_PASSWORD "$ADMIN_PASS"
upsert_env_local SUITE_DEMO_DATA "$([[ "$DEMO" =~ ^[OoYy] ]] && echo 1 || echo 0)"

BASE_URL="${SCHEME}://${HOST}"
upsert_env_local LP_CORE_PUBLIC_URL "$BASE_URL"
upsert_env_local TOOLMAG_PUBLIC_BASE_URL "$BASE_URL/toolmag/"
upsert_env_local SAFETY_PUBLIC_URL "$BASE_URL/safety/"
upsert_env_local PEDASHOP_PUBLIC_URL "$BASE_URL/pedashop/"
upsert_env_local SYSTEM_MANAGER_PUBLIC_URL "$BASE_URL/system/"
upsert_env_local INVENTORY_PUBLIC_URL "$BASE_URL/system/"
upsert_env_local TPMANAGER_PUBLIC_URL "$BASE_URL/tpmanager/"
upsert_env_local PFMP_PUBLIC_URL "$BASE_URL/pfmp/"
upsert_env_local CSRF_TRUSTED_ORIGINS "$BASE_URL,http://localhost:9000,http://127.0.0.1:9000"

chmod +x scripts/*.sh scripts/postgres/*.sh 2>/dev/null || true
bash scripts/preflight_compat.sh || true

if [ -d postgres-db/data ] && [ "$(find postgres-db/data -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)" -gt 0 ]; then
  reset_db="$(ask "Des données PostgreSQL existent. Les supprimer pour une installation neuve ? oui/non" "non")"
  if [[ "$reset_db" =~ ^[OoYy] ]]; then
    docker compose --env-file .env down || true
    rm -rf postgres-db/data
    mkdir -p postgres-db/data
  fi
fi

log "Construction et démarrage des conteneurs"
docker compose --env-file .env up -d --build postgres
wait_postgres 120
docker compose --env-file .env up -d --build
sleep 20

bash scripts/migrate_all.sh
bash scripts/create_initial_admins.sh
if [[ "$DEMO" =~ ^[OoYy] ]]; then
  bash scripts/load_demo_data.sh --from-install
  bash scripts/sync_all_modules_from_core.sh || true
fi
bash scripts/collectstatic_all.sh

docker compose --env-file .env restart
sleep 30
check_http_routes

log "Installation terminée."
echo "URL principale : $BASE_URL"
echo "Compte initial : $ADMIN_USER / mot de passe choisi"
echo "Change le mot de passe après validation."
