#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"

# Installateur interactif LP Gestion Atelier EP Suite RC15.
# Type : installation complète SSH, pas mise à jour web.
# Objectif RC15 : mode fresh install fiable avec suppression des instances précédentes
# et migrations exécutées avant le démarrage des applications.

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

upsert_env_local(){ upsert_env "$1" "$2" ".env"; }

require_docker_compose
[ -f docker-compose.yml ] || fatal "docker-compose.yml introuvable."

log "LP Gestion Atelier EP Suite - installation assistée RC15"
echo "Type : installation complète SSH."
echo "RC15 corrige l'installation neuve : suppression optionnelle des instances précédentes, BDD vierge, migrations avant démarrage des apps."
echo

echo "Mode d'installation :"
echo "  1) fresh    : supprimer les conteneurs/données LP Suite de ce dossier puis installer à neuf"
echo "  2) conserve : conserver les données existantes et compléter l'installation"
install_mode="$(ask "Choix" "1")"
FRESH_INSTALL=0
case "$install_mode" in
  1|fresh|FRESH|Fresh) FRESH_INSTALL=1 ;;
  2|conserve|CONSERVE|Conserve) FRESH_INSTALL=0 ;;
  *) fatal "Choix invalide" ;;
esac

if [ -f .env ]; then
  echo "Un fichier .env existe déjà."
  if [ "$FRESH_INSTALL" = "1" ]; then
    keep="non"
    echo "Mode fresh : l'ancien .env sera sauvegardé puis recréé."
  else
    keep="$(ask "Le conserver et seulement compléter les valeurs manquantes ? oui/non" "oui")"
  fi
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

chmod +x install.sh update.sh upgrade.sh scripts/*.sh scripts/postgres/*.sh 2>/dev/null || true
bash scripts/preflight_compat.sh || true

if [ "$FRESH_INSTALL" = "1" ]; then
  echo
  echo "ATTENTION : mode fresh install."
  echo "Les conteneurs LP Suite, volumes Compose et données locales de cette installation seront supprimés."
  confirm="$(ask "Confirmer la suppression préalable ? oui/non" "oui")"
  if [[ "$confirm" =~ ^[OoYy] ]]; then
    fresh_reset_installation
  else
    fatal "Installation fresh annulée."
  fi
elif [ -d postgres-db/data ] && [ "$(find postgres-db/data -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)" -gt 0 ]; then
  reset_db="$(ask "Des données PostgreSQL existent. Les supprimer pour une installation neuve ? oui/non" "non")"
  if [[ "$reset_db" =~ ^[OoYy] ]]; then
    fresh_reset_installation
  fi
fi

log "Construction des images Docker"
docker compose --env-file .env build

log "Démarrage PostgreSQL uniquement"
docker compose --env-file .env up -d postgres
wait_postgres 180

log "Migrations avant démarrage des applications"
bash scripts/migrate_all.sh

log "Création des comptes initiaux avant démarrage des applications"
bash scripts/create_initial_admins.sh

if [[ "$DEMO" =~ ^[OoYy] ]]; then
  log "Chargement de la base de démonstration avant démarrage final"
  bash scripts/load_demo_data.sh --from-install
fi

log "Collecte des fichiers statiques"
bash scripts/collectstatic_all.sh

log "Démarrage final de la suite"
docker compose --env-file .env up -d --no-build
sleep 30

if [[ "$DEMO" =~ ^[OoYy] ]]; then
  log "Synchronisation post-démo vers les modules"
  bash scripts/sync_all_modules_from_core.sh || true
fi

check_http_routes

log "Installation terminée."
echo "URL principale : $BASE_URL"
echo "Compte initial : $ADMIN_USER / mot de passe choisi"
echo "Change le mot de passe après validation."
echo "Note : le contrôle localhost est interne au serveur. En mode réseau, l'accès utilisateur reste : $BASE_URL"
