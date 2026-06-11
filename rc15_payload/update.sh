#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
source scripts/lp_suite_common.sh

BRANCH="${LP_SUITE_UPDATE_BRANCH:-rc}"
WITH_DEMO=0
NO_BACKUP=0
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --branch=*) BRANCH="${arg#*=}" ;;
    --with-demo) WITH_DEMO=1 ;;
    --no-backup) NO_BACKUP=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      cat <<HELP
Usage : bash update.sh [--branch=rc] [--with-demo] [--no-backup] [--dry-run]

Mise à jour rapide depuis Git :
  - vérifie la compatibilité
  - sauvegarde PostgreSQL + .env
  - git pull --ff-only
  - rebuild/restart
  - migrations, admins, collectstatic
  - démo optionnelle seulement avec --with-demo
HELP
      exit 0 ;;
    *) fatal "Option inconnue : $arg" ;;
  esac
done

require_docker_compose
require_project_files
bash scripts/preflight_compat.sh --strict

if [ ! -d .git ]; then
  fatal "update.sh nécessite un dépôt Git. Pour un ZIP, utilise : bash upgrade.sh --zip /chemin/fichier.zip"
fi

git fetch origin "$BRANCH"
LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse "origin/$BRANCH")"
log "Branche : $BRANCH"
log "Local  : $LOCAL_SHA"
log "Distant: $REMOTE_SHA"

if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
  log "Aucun commit distant à appliquer. On vérifie tout de même migrations/statics."
else
  if [ "$DRY_RUN" = "1" ]; then
    git --no-pager log --oneline "$LOCAL_SHA..$REMOTE_SHA" || true
    exit 0
  fi
  if [ "$NO_BACKUP" = "0" ]; then bash scripts/backup_all.sh; fi
  git pull --ff-only origin "$BRANCH"
fi

log "Reconstruction et démarrage"
dc build
dc up -d
wait_postgres 120
bash scripts/migrate_all.sh
bash scripts/create_initial_admins.sh
if [ "$WITH_DEMO" = "1" ]; then bash scripts/load_demo_data.sh; fi
bash scripts/collectstatic_all.sh
bash scripts/sync_all_modules_from_core.sh || true

dc restart
sleep 30
check_http_routes
log "Mise à jour terminée."
