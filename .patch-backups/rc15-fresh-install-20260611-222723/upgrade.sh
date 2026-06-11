#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
source scripts/lp_suite_common.sh

ZIP_FILE=""
BRANCH=""
WITH_DEMO=0
NO_BACKUP=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --zip=*) ZIP_FILE="${arg#*=}" ;;
    --branch=*) BRANCH="${arg#*=}" ;;
    --with-demo) WITH_DEMO=1 ;;
    --no-backup) NO_BACKUP=1 ;;
    --force) FORCE=1 ;;
    -h|--help)
      cat <<HELP
Usage :
  bash upgrade.sh --branch=rc [--with-demo] [--no-backup]
  bash upgrade.sh --zip=/home/patch.zip [--with-demo] [--no-backup] [--force]

Upgrade classique :
  - vérification compatibilité
  - sauvegarde PostgreSQL + .env
  - application ZIP ou Git
  - rebuild/restart
  - migrations, admins, collectstatic
  - démo optionnelle avec --with-demo
HELP
      exit 0 ;;
    *) fatal "Option inconnue : $arg" ;;
  esac
done

require_docker_compose
require_project_files
bash scripts/preflight_compat.sh --strict || { [ "$FORCE" = "1" ] || exit 1; }

if [ "$NO_BACKUP" = "0" ]; then bash scripts/backup_all.sh; fi

if [ -n "$BRANCH" ]; then
  [ -d .git ] || fatal "Upgrade par branche demandé mais ce dossier n'est pas un dépôt Git."
  git fetch origin "$BRANCH"
  git pull --ff-only origin "$BRANCH"
elif [ -n "$ZIP_FILE" ]; then
  [ -f "$ZIP_FILE" ] || fatal "ZIP introuvable : $ZIP_FILE"
  TMP="$(mktemp -d)"
  unzip -q "$ZIP_FILE" -d "$TMP"
  APPLY="$(find "$TMP" -maxdepth 2 -type f -name 'apply_*.sh' | head -n1 || true)"
  if [ -n "$APPLY" ]; then
    chmod +x "$APPLY"
    "$APPLY" "$PROJECT_ROOT"
  else
    PAYLOAD="$(find "$TMP" -maxdepth 2 -type d \( -name '*payload*' -o -name 'rc*_payload' \) | head -n1 || true)"
    if [ -n "$PAYLOAD" ]; then
      cp -a "$PAYLOAD"/. "$PROJECT_ROOT"/
    else
      fatal "ZIP non reconnu : aucun apply_*.sh ni payload."
    fi
  fi
  rm -rf "$TMP"
else
  fatal "Précise --branch=rc ou --zip=/chemin/patch.zip"
fi

bash scripts/preflight_compat.sh --strict || { [ "$FORCE" = "1" ] || exit 1; }

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
log "Upgrade terminé."
