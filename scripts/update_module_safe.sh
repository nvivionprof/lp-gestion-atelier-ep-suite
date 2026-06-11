#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

FULL_REBUILD=0
SKIP_SEED=0
MODULE=""
ZIP=""

usage(){
  cat <<'EOF'
Usage : ./upgrade_module.sh [options] <module> <archive_zip_suite_ou_module>
Options :
  --full-rebuild    Reconstruit l'image du module sans cache.
  --skip-seed       N'exécute pas les seeds du module après migration.
Modules :
  lp-core | toolmag | safety | pedashop | system-manager | tpmanager | suite-admin-agent
Exemples :
  ./upgrade_module.sh tpmanager lp-gestion-atelier-ep-suite-v2.8.3.zip
  ./upgrade_module.sh --full-rebuild pedashop nouvelle_suite.zip
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --full-rebuild) FULL_REBUILD=1; shift;;
    --skip-seed) SKIP_SEED=1; shift;;
    -h|--help) usage; exit 0;;
    *)
      if [ -z "$MODULE" ]; then MODULE="$1"; elif [ -z "$ZIP" ]; then ZIP="$1"; else echo "Argument en trop : $1" >&2; usage >&2; exit 1; fi
      shift;;
  esac
done

if [ -z "$MODULE" ] || [ -z "$ZIP" ]; then usage >&2; exit 1; fi
if [ ! -f "$ZIP" ]; then echo "Archive introuvable : $ZIP" >&2; exit 1; fi
if ! command -v unzip >/dev/null 2>&1; then echo "unzip est nécessaire : sudo apt install unzip" >&2; exit 1; fi
if ! command -v rsync >/dev/null 2>&1; then echo "rsync est nécessaire : sudo apt install rsync" >&2; exit 1; fi

norm_module(){
  case "$1" in
    core|lp_core|lp-core|lp-core-app) echo "lp-core|lp-core-app|lp-core-app";;
    toolmag|toolmag-app) echo "toolmag|toolmag-app|toolmag-app";;
    safety|safety-manager|safety-app) echo "safety|safety-app|safety-app";;
    pedashop|peda-shop|pedashop-app) echo "pedashop|pedashop-app|pedashop-app";;
    system|system-manager|system-manager-app) echo "system-manager|system-manager-app|system-manager-app";;
    tp|tpmanager|tp-manager|tpmanager-app) echo "tpmanager|tpmanager-app|tpmanager-app";;
    suite-admin|suite-admin-agent) echo "suite-admin-agent|suite-admin-agent|suite-admin-agent";;
    *) return 1;;
  esac
}
IFS='|' read -r MODULE_KEY DIR SERVICE < <(norm_module "$MODULE") || { echo "Module non géré : $MODULE" >&2; usage >&2; exit 1; }

LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/upgrade_module_${MODULE_KEY}_$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1
log(){ echo "[$(date +%H:%M:%S)] $*"; }

log "=== Mise à jour module optimisée ==="
log "Module : $MODULE_KEY"
log "Service : $SERVICE"
log "Archive : $ZIP"
log "Log : $LOG_FILE"
[ "$FULL_REBUILD" = "1" ] && log "Build : sans cache" || log "Build : cache conservé"
[ "$SKIP_SEED" = "1" ] && log "Seeds : désactivés" || log "Seeds : activés"

./scripts/backup_before_upgrade.sh

STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "versions/$MODULE_KEY-$STAMP"
[ -d "$DIR" ] && cp -a "$DIR" "versions/$MODULE_KEY-$STAMP/"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
unzip -q "$ZIP" -d "$TMP"
SRC_ROOT="$TMP/lp-gestion-atelier-ep-suite"
[ -d "$SRC_ROOT" ] || SRC_ROOT="$TMP"

if [ -d "$SRC_ROOT/$DIR" ]; then
  SRC_MODULE="$SRC_ROOT/$DIR"
elif [ -f "$SRC_ROOT/manage.py" ] || [ -f "$SRC_ROOT/Dockerfile" ]; then
  SRC_MODULE="$SRC_ROOT"
else
  echo "Impossible de trouver le dossier du module '$DIR' dans l'archive." >&2
  exit 1
fi

log "Copie du module $DIR sans toucher aux bases de données..."
mkdir -p "$DIR"
rsync -a --delete \
  --exclude '.env' \
  --exclude 'db.sqlite3' \
  --exclude 'media/' \
  --exclude 'staticfiles/' \
  "$SRC_MODULE/" "$DIR/"

# Certains changements de module nécessitent éventuellement des fichiers de scripts/documentation partagés.
# On copie uniquement les fichiers sûrs s'ils existent dans l'archive complète.
if [ -d "$SRC_ROOT/scripts" ]; then
  rsync -a "$SRC_ROOT/scripts/" scripts/ \
    --include 'migrate_all.sh' \
    --include 'backup_before_upgrade.sh' \
    --include 'update_module_safe.sh' \
    --exclude '*' || true
fi
[ -f "$SRC_ROOT/upgrade_module.sh" ] && cp -a "$SRC_ROOT/upgrade_module.sh" upgrade_module.sh
chmod +x upgrade_module.sh scripts/*.sh 2>/dev/null || true

BUILD_ARGS=()
if [ "$FULL_REBUILD" = "1" ]; then BUILD_ARGS+=(--no-cache); fi

log "Construction image : $SERVICE"
docker compose build "${BUILD_ARGS[@]}" "$SERVICE"
log "Redémarrage service : $SERVICE"
docker compose up -d "$SERVICE"

if [ "$MODULE_KEY" != "suite-admin-agent" ]; then
  MIGRATE_ARGS=(--module "$MODULE_KEY")
  [ "$SKIP_SEED" = "1" ] && MIGRATE_ARGS+=(--skip-seed)
  log "Migrations module : $MODULE_KEY"
  ./scripts/migrate_all.sh "${MIGRATE_ARGS[@]}"
fi

log "Contrôle santé ciblé..."
./scripts/check_health.sh || true
log "Mise à jour module terminée. Ancienne version : versions/$MODULE_KEY-$STAMP/"
