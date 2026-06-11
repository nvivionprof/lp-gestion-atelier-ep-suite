#!/usr/bin/env bash
set -Eeuo pipefail
trap 'echo; echo "Installation interrompue." >&2; exit 130' INT TERM
cd "$(dirname "$0")"

MODE="auto"
FULL_REBUILD=0
CLEAN_BUILD=0
SKIP_SEED=0
SKIP_MIGRATIONS=0
YES=0
SKIP_CHECKSUM=0
FORCE_DEMO=""
usage(){
  cat <<'HELP'
Usage : ./install.sh [options]
Modes : --mode install | update | upgrade | auto
Options : --full-rebuild --clean-build --skip-seed --skip-migrations --demo --no-demo --skip-checksum -y|--yes
HELP
}
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="$2"; shift 2;;
    --mode=*) MODE="${1#*=}"; shift;;
    --full-rebuild) FULL_REBUILD=1; shift;;
    --clean-build) CLEAN_BUILD=1; FULL_REBUILD=1; shift;;
    --skip-seed) SKIP_SEED=1; shift;;
    --skip-migrations) SKIP_MIGRATIONS=1; shift;;
    --demo) FORCE_DEMO=1; shift;;
    --no-demo) FORCE_DEMO=0; shift;;
    --skip-checksum) SKIP_CHECKSUM=1; shift;;
    -y|--yes) YES=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Option inconnue : $1" >&2; usage >&2; exit 1;;
  esac
done
log(){ echo "[$(date +%H:%M:%S)] $*"; }
need(){ command -v "$1" >/dev/null 2>&1 || { echo "ERREUR : commande absente : $1" >&2; exit 1; }; }
need docker; need python3; need awk
if ! docker compose version >/dev/null 2>&1; then echo "ERREUR : Docker Compose v2 n'est pas disponible." >&2; exit 1; fi
[ -f .env ] || cp .env.example .env
dc(){ docker compose --env-file .env "$@"; }
env_get(){ awk -F= -v k="$1" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n 1; }
validate_env(){
  python3 - <<'PY'
from pathlib import Path
import re
bad=[]
for i,line in enumerate(Path('.env').read_text(encoding='utf-8').splitlines(),1):
    s=line.strip()
    if not s or s.startswith('#'): continue
    if '=' not in s:
        bad.append((i,line,"ligne sans '='")); continue
    k=s.split('=',1)[0]
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', k): bad.append((i,line,'clé invalide'))
if bad:
    for i,line,why in bad: print(f'.env invalide ligne {i}: {why}: {line!r}')
    raise SystemExit(1)
PY
}
if [ "$SKIP_CHECKSUM" = "0" ] && [ -f CHECKSUMS.sha256 ]; then
  CHECKSUM_ON="${CHECKSUM_VERIFY_ON_INSTALL:-1}"
  if [ -f .env ]; then CHECKSUM_ON="$(env_get CHECKSUM_VERIFY_ON_INSTALL || true)"; fi
  CHECKSUM_ON="${CHECKSUM_ON:-1}"
  if [ "$CHECKSUM_ON" = "1" ] && [ -x scripts/verify_checksums.sh ]; then
    log "Vérification intégrité archive : CHECKSUMS.sha256"
    scripts/verify_checksums.sh --quiet
  fi
fi
CURRENT_VERSION="unknown"
[ -f .suite-version ] && CURRENT_VERSION="$(cat .suite-version | head -1 | tr -d '\r\n')"
[ -f VERSION ] && NEW_VERSION="$(cat VERSION | head -1 | tr -d '\r\n')" || NEW_VERSION="unknown"
if [ "$MODE" = "auto" ]; then if [ ! -f .suite-version ]; then MODE="install"; else MODE="update"; fi; fi
case "$MODE" in install|update|upgrade) ;; *) echo "Mode invalide : $MODE" >&2; exit 1;; esac
if [ "$MODE" != "install" ] && [ -n "$FORCE_DEMO" ]; then echo "ERREUR : --demo/--no-demo réservés au mode install." >&2; exit 1; fi
log "Mode sélectionné : $MODE"
log "Version installée : $CURRENT_VERSION"
log "Version archive/code : $NEW_VERSION"
python3 scripts/check_version_policy.py "$MODE" "$CURRENT_VERSION"
CONFIGURE_ENV_ARGS=(--mode "$MODE")
if [ "$MODE" = "install" ] && [ -n "$FORCE_DEMO" ]; then [ "$FORCE_DEMO" = "1" ] && CONFIGURE_ENV_ARGS+=(--demo) || CONFIGURE_ENV_ARGS+=(--no-demo); fi
if [ "$MODE" = "install" ]; then
  ./scripts/configure_install_env.sh "${CONFIGURE_ENV_ARGS[@]}"
else
  if grep -q '^POSTGRES_PASSWORD=CHANGE_ME' .env || ! grep -q '^POSTGRES_PASSWORD=' .env; then
    log "Mot de passe PostgreSQL absent ou générique : configuration interactive requise."
    ./scripts/configure_install_env.sh "${CONFIGURE_ENV_ARGS[@]}"
  else
    ./scripts/set_env_value.sh LOAD_DEMO_DATA 0
  fi
fi
if [ -x ./scripts/configure_public_urls.sh ]; then
  if [ "$MODE" = "install" ]; then
    echo "Configuration des adresses publiques. Pour un test local : localhost."
    ./scripts/configure_public_urls.sh
  elif [ "$YES" = "0" ]; then
    read -rp "Conserver les URL/ports actuels du .env ? [O/n] : " keep_urls
    if [[ "${keep_urls:-O}" =~ ^[Nn]$ ]]; then ./scripts/configure_public_urls.sh; fi
  fi
fi
validate_env
mkdir -p postgres-db/data lp-core-db/data toolmag-db/data safety-db/data pedashop-db/data system-manager-db/data tpmanager-db/data pfmp-db/data \
  lp-core-db/data/staticfiles toolmag-db/data/staticfiles safety-db/data/staticfiles pedashop-db/data/staticfiles system-manager-db/data/staticfiles tpmanager-db/data/staticfiles pfmp-db/data/staticfiles \
  lp-core-db/data/updates/incoming lp-core-db/data/updates/logs backups/daily backups/manual backups/pre_upgrade backups/tmp imports logs updates/incoming updates/logs ssl
BACKUP_REQUIRED="$(env_get BACKUP_PRE_UPGRADE_REQUIRED)"; BACKUP_REQUIRED="${BACKUP_REQUIRED:-1}"
if [ "$MODE" != "install" ] && [ "$BACKUP_REQUIRED" = "1" ]; then
  log "Sauvegarde pré-${MODE} requise."
  scripts/full_backup.sh pre-upgrade
fi
log "Arrêt des conteneurs existants, volumes conservés."
dc down --remove-orphans || true
if [ "$CLEAN_BUILD" = "1" ]; then
  log "Nettoyage Docker sécurisé : cache BuildKit/images inutilisées, volumes conservés."
  docker builder prune -af || true
  docker system prune -f || true
fi
log "Démarrage PostgreSQL."
dc up -d postgres
log "Attente PostgreSQL."
PGUSER="$(env_get POSTGRES_USER)"; PGUSER="${PGUSER:-lp_suite_user}"
for i in $(seq 1 60); do
  if dc exec -T postgres pg_isready -U "$PGUSER" >/dev/null 2>&1; then break; fi
  sleep 2
  if [ "$i" = "60" ]; then echo "ERREUR : PostgreSQL ne répond pas." >&2; exit 1; fi
done
log "Vérification/création des bases PostgreSQL."
scripts/postgres/ensure_databases.sh all
BUILD_ARGS=(); [ "$FULL_REBUILD" = "1" ] && BUILD_ARGS+=(--no-cache)
BUILD_SERVICES=(lp-gateway lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app suite-admin-agent suite-backup-scheduler)
log "Construction des images."
dc build "${BUILD_ARGS[@]}" "${BUILD_SERVICES[@]}"
run_app(){ dc run --rm --no-deps "$@"; }
seed_app(){ if [ "$SKIP_SEED" = "1" ]; then log "Seed ignoré : $*"; else run_app "$@"; fi; }
run_manage(){ local service="$1"; shift; run_app "$service" python manage.py "$@"; }
if [ "$SKIP_MIGRATIONS" = "0" ]; then
  log "Migrations et initialisation LP Core."
  run_manage lp-core-app migrate --noinput
  run_manage lp-core-app collectstatic --noinput
  ADMIN_USER="$(env_get LP_CORE_ADMIN_USERNAME)"; ADMIN_USER="${ADMIN_USER:-admin}"
  ADMIN_PASS="$(env_get LP_CORE_ADMIN_PASSWORD)"
  seed_app lp-core-app python manage.py seed_core --admin-username "$ADMIN_USER" --admin-password "$ADMIN_PASS"
  if [ -n "$(env_get LP_CORE_IMPORT_XLSX)" ]; then
    IMPORT_XLSX="$(env_get LP_CORE_IMPORT_XLSX)"
    log "Import Excel LP Core : $IMPORT_XLSX"
    run_manage lp-core-app import_users_xlsx "$IMPORT_XLSX" || true
  fi
  for svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
    log "Migrations : $svc"
    run_manage "$svc" migrate --noinput
    run_manage "$svc" collectstatic --noinput || true
  done
  seed_app safety-app python manage.py seed_safety_manager || true
  seed_app pedashop-app python manage.py seed_pedashop || true
  seed_app system-manager-app python manage.py seed_system_manager || true
  seed_app tpmanager-app python manage.py seed_tp_manager || true
  seed_app tpmanager-app python manage.py seed_tpmanager_v2 || true
  seed_app tpmanager-app python manage.py seed_sequence_manager || true
  seed_app pfmp-app python manage.py seed_pfmp_manager || true
  if [ "$MODE" = "install" ]; then
    LOAD_DEMO="$(env_get LOAD_DEMO_DATA)"; LOAD_DEMO="${LOAD_DEMO:-0}"
    if [ "$LOAD_DEMO" = "1" ]; then
      log "Chargement automatique des bases de démonstration demandé à l'installation."
      [ -x scripts/load_demo_data.sh ] && scripts/load_demo_data.sh --from-install || true
    else
      log "Bases de démonstration non chargées pour cette installation."
    fi
  else
    log "Mode $MODE : bases de démonstration non chargées automatiquement."
  fi
else
  log "Migrations ignorées sur demande (--skip-migrations)."
fi
log "Démarrage final des services."
dc up -d lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app suite-admin-agent suite-backup-scheduler lp-gateway
log "Synchronisations LP Core après démarrage."
for svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
  dc exec -T "$svc" python manage.py sync_lp_core_users || true
done
dc exec -T tpmanager-app python manage.py sync_system_manager || true
[ -x ./scripts/verify_portal_routes.sh ] && ./scripts/verify_portal_routes.sh || true
printf '%s\n' "$NEW_VERSION" > .suite-version
log "Installation/mise à jour terminée."
echo "Portail : $(env_get LP_CORE_PUBLIC_URL)"
echo "Compte admin LP Core : $(env_get LP_CORE_ADMIN_USERNAME) / mot de passe choisi à l'installation"
echo "Version enregistrée : $NEW_VERSION"
