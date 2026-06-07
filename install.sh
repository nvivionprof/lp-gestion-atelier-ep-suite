#!/usr/bin/env bash
set -Eeuo pipefail
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
  cat <<'EOF'
Usage : ./install.sh [options]

Modes :
  --mode install    Installation neuve PostgreSQL. Demande le mot de passe DB et le compte admin.
  --mode update     Mise à jour depuis Git/archive compatible. Sauvegarde pré-update puis migrations.
  --mode upgrade    Changement de version/socle. Vérifie la version minimale, sauvegarde puis migrations.
  --mode auto       Déduit install/update selon la présence de .suite-version. Défaut.

Options :
  --full-rebuild       Reconstruit les images Docker sans cache.
  --clean-build        Nettoie le cache Docker/BuildKit avant build, sans supprimer les volumes.
  --skip-seed          N'exécute pas les seeds après migrations.
  --skip-migrations    Ne lance pas les migrations Django. À réserver au diagnostic.
  --demo               En mode install uniquement : charge les bases de démonstration après migrations.
  --no-demo            En mode install uniquement : ne charge pas les bases de démonstration.
  --skip-checksum      Ne vérifie pas CHECKSUMS.sha256 avant installation. À réserver au diagnostic.
  -y, --yes            Réponses automatiques aux confirmations non critiques.
  -h, --help           Affiche cette aide.

Variables non interactives utiles :
  LP_INSTALL_DB_PASSWORD, LP_INSTALL_ADMIN_USERNAME, LP_INSTALL_ADMIN_PASSWORD, LP_INSTALL_LOAD_DEMO
EOF
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
need docker
need python3
if ! docker compose version >/dev/null 2>&1; then echo "ERREUR : Docker Compose v2 n'est pas disponible." >&2; exit 1; fi

# Vérification rapide de l'intégrité des fichiers extraits.
if [ "$SKIP_CHECKSUM" = "0" ] && [ -f CHECKSUMS.sha256 ]; then
  CHECKSUM_ON="${CHECKSUM_VERIFY_ON_INSTALL:-1}"
  if [ -f .env ]; then CHECKSUM_ON="$(awk -F= '$1=="CHECKSUM_VERIFY_ON_INSTALL"{print $2}' .env | tail -n1 || true)"; fi
  CHECKSUM_ON="${CHECKSUM_ON:-1}"
  if [ "$CHECKSUM_ON" = "1" ] && [ -x scripts/verify_checksums.sh ]; then
    log "Vérification intégrité archive : CHECKSUMS.sha256"
    scripts/verify_checksums.sh --quiet
  fi
fi

[ -f .env ] || cp .env.example .env
CURRENT_VERSION="unknown"
[ -f .suite-version ] && CURRENT_VERSION="$(cat .suite-version | head -1 | tr -d '\r\n')"
[ -f VERSION ] && NEW_VERSION="$(cat VERSION | head -1 | tr -d '\r\n')" || NEW_VERSION="unknown"

if [ "$MODE" = "auto" ]; then
  if [ ! -f .suite-version ]; then MODE="install"; else MODE="update"; fi
fi
case "$MODE" in install|update|upgrade) ;; *) echo "Mode invalide : $MODE" >&2; exit 1;; esac

# Règle projet : les bases de démonstration sont proposées et chargées uniquement
# lors d'une installation neuve. Elles ne sont jamais chargées automatiquement
# en update/upgrade pour éviter de polluer ou modifier des données existantes.
if [ "$MODE" != "install" ] && [ -n "$FORCE_DEMO" ]; then
  echo "ERREUR : --demo et --no-demo sont réservés au mode install." >&2
  echo "En update/upgrade, les bases de démonstration ne sont pas chargées." >&2
  exit 1
fi

log "Mode sélectionné : $MODE"
log "Version installée : $CURRENT_VERSION"
log "Version archive/code : $NEW_VERSION"
python3 scripts/check_version_policy.py "$MODE" "$CURRENT_VERSION"

# Choix DB/admin et mise à jour .env.
# En mode install, la question des bases de démonstration est posée au début
# de l'installation, avant build/migrations, puis appliquée automatiquement
# après les migrations si la réponse est oui.
CONFIGURE_ENV_ARGS=(--mode "$MODE")
if [ "$MODE" = "install" ] && [ -n "$FORCE_DEMO" ]; then
  if [ "$FORCE_DEMO" = "1" ]; then CONFIGURE_ENV_ARGS+=(--demo); else CONFIGURE_ENV_ARGS+=(--no-demo); fi
fi

if [ "$MODE" = "install" ]; then
  ./scripts/configure_install_env.sh "${CONFIGURE_ENV_ARGS[@]}"
else
  if grep -q '^POSTGRES_PASSWORD=CHANGE_ME' .env || ! grep -q '^POSTGRES_PASSWORD=' .env; then
    log "Mot de passe PostgreSQL absent ou générique : configuration interactive requise."
    ./scripts/configure_install_env.sh "${CONFIGURE_ENV_ARGS[@]}"
  else
    # Garantie anti-démo en update/upgrade : même si .env contient LOAD_DEMO_DATA=1,
    # l'installateur ne chargera pas les bases démo hors installation neuve.
    if [ -x ./scripts/set_env_value.sh ]; then
      ./scripts/set_env_value.sh LOAD_DEMO_DATA 0
    else
      if grep -q '^LOAD_DEMO_DATA=' .env; then sed -i "s#^LOAD_DEMO_DATA=.*#LOAD_DEMO_DATA=0#" .env; else printf 'LOAD_DEMO_DATA=0\n' >> .env; fi
    fi
  fi
fi

# Configuration des URL publiques, conservable si déjà configurée.
if [ -x ./scripts/configure_public_urls.sh ]; then
  if [ "$MODE" = "install" ]; then
    echo "Configuration des adresses publiques. Pour un test local : localhost."
    ./scripts/configure_public_urls.sh
  elif [ "$YES" = "0" ]; then
    read -rp "Conserver les URL/ports actuels du .env ? [O/n] : " keep_urls
    if [[ "${keep_urls:-O}" =~ ^[Nn]$ ]]; then ./scripts/configure_public_urls.sh; fi
  fi
fi

mkdir -p postgres-db/data lp-core-db/data toolmag-db/data safety-db/data pedashop-db/data system-manager-db/data tpmanager-db/data pfmp-db/data \
  lp-core-db/data/staticfiles toolmag-db/data/staticfiles safety-db/data/staticfiles pedashop-db/data/staticfiles system-manager-db/data/staticfiles tpmanager-db/data/staticfiles pfmp-db/data/staticfiles \
  lp-core-db/data/updates/incoming lp-core-db/data/updates/logs backups/daily backups/manual backups/pre_upgrade backups/tmp imports logs updates/incoming updates/logs ssl

# Sauvegarde obligatoire en update/upgrade sauf désactivation explicite dans .env.
BACKUP_REQUIRED="$(awk -F= '$1=="BACKUP_PRE_UPGRADE_REQUIRED"{print $2}' .env | tail -n1)"
BACKUP_REQUIRED="${BACKUP_REQUIRED:-1}"
if [ "$MODE" != "install" ] && [ "$BACKUP_REQUIRED" = "1" ]; then
  log "Sauvegarde pré-${MODE} requise."
  if [ -x scripts/full_backup.sh ]; then
    scripts/full_backup.sh pre-upgrade
  elif [ -x scripts/backup_before_upgrade.sh ]; then
    scripts/backup_before_upgrade.sh
  else
    echo "ERREUR : aucun script de sauvegarde disponible." >&2
    exit 1
  fi
fi

log "Arrêt des conteneurs existants, volumes conservés."
docker compose down --remove-orphans || true

if [ "$CLEAN_BUILD" = "1" ]; then
  log "Nettoyage Docker sécurisé : cache BuildKit/images inutilisées, volumes conservés."
  docker builder prune -af || true
  docker system prune -f || true
fi

log "Démarrage PostgreSQL."
docker compose up -d postgres
log "Attente PostgreSQL."
for i in $(seq 1 60); do
  if docker compose exec -T postgres pg_isready -U "$(awk -F= '$1=="POSTGRES_USER"{print $2}' .env | tail -n1)" >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if [ "$i" = "60" ]; then echo "ERREUR : PostgreSQL ne répond pas." >&2; exit 1; fi
done

BUILD_ARGS=()
[ "$FULL_REBUILD" = "1" ] && BUILD_ARGS+=(--no-cache)
BUILD_SERVICES=(lp-gateway lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app suite-admin-agent suite-backup-scheduler)
log "Construction des images."
docker compose build "${BUILD_ARGS[@]}" "${BUILD_SERVICES[@]}"

run_app(){ docker compose run --rm "$@"; }
seed_app(){ if [ "$SKIP_SEED" = "1" ]; then log "Seed ignoré : $*"; else run_app "$@"; fi; }
run_manage(){ local service="$1"; shift; run_app "$service" python manage.py "$@"; }

if [ "$SKIP_MIGRATIONS" = "0" ]; then
  log "Migrations et initialisation LP Core."
  run_manage lp-core-app migrate --noinput
  run_manage lp-core-app collectstatic --noinput
  ADMIN_USER="$(awk -F= '$1=="LP_CORE_ADMIN_USERNAME"{print $2}' .env | tail -n1)"
  ADMIN_PASS="$(awk -F= '$1=="LP_CORE_ADMIN_PASSWORD"{print $2}' .env | tail -n1)"
  seed_app lp-core-app python manage.py seed_core --admin-username "${ADMIN_USER:-admin}" --admin-password "$ADMIN_PASS"

  if [ -n "$(awk -F= '$1=="LP_CORE_IMPORT_XLSX"{print $2}' .env | tail -n1)" ]; then
    IMPORT_XLSX="$(awk -F= '$1=="LP_CORE_IMPORT_XLSX"{print $2}' .env | tail -n1)"
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
    LOAD_DEMO="$(awk -F= '$1=="LOAD_DEMO_DATA"{print $2}' .env | tail -n1)"
    LOAD_DEMO="${LOAD_DEMO:-0}"
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
docker compose up -d lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app suite-admin-agent suite-backup-scheduler lp-gateway

log "Synchronisations LP Core après démarrage."
docker compose exec -T toolmag-app python manage.py sync_lp_core_users || true
docker compose exec -T safety-app python manage.py sync_lp_core_users || true
docker compose exec -T pedashop-app python manage.py sync_lp_core_users || true
docker compose exec -T system-manager-app python manage.py sync_lp_core_users || true
docker compose exec -T tpmanager-app python manage.py sync_lp_core_users || true
docker compose exec -T pfmp-app python manage.py sync_lp_core_users || true
docker compose exec -T tpmanager-app python manage.py sync_system_manager || true

[ -x ./scripts/verify_portal_routes.sh ] && ./scripts/verify_portal_routes.sh || true
printf '%s\n' "$NEW_VERSION" > .suite-version

log "Installation/mise à jour terminée."
echo "Portail : $(awk -F= '$1=="LP_CORE_PUBLIC_URL"{print $2}' .env | tail -n1)"
echo "Compte admin LP Core : $(awk -F= '$1=="LP_CORE_ADMIN_USERNAME"{print $2}' .env | tail -n1) / mot de passe choisi à l'installation"
echo "Version enregistrée : $NEW_VERSION"
