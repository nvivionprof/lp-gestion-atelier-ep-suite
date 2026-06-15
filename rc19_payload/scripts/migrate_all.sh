#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

require_project_files
wait_postgres 180

# Réparation préventive des cas connus où les objets SQL existent mais django_migrations
# n'a pas été mis à jour à cause d'une interruption/erreur de migration.
if [ -x scripts/repair_migration_state.sh ]; then
  bash scripts/repair_migration_state.sh all || true
fi

run_migrate_with_repair(){
  local svc="$1"
  log "Migrations Django : $svc"
  if run_manage "$svc" migrate; then
    return 0
  fi

  warn "Migration en erreur pour $svc. Tentative de réparation automatique puis nouvel essai."
  if [ -x scripts/repair_migration_state.sh ]; then
    bash scripts/repair_migration_state.sh "$svc" || true
  fi

  run_manage "$svc" migrate
}

for svc in "${LP_MODULE_SERVICES[@]}"; do
  run_migrate_with_repair "$svc"
done

log "Migrations terminées."
