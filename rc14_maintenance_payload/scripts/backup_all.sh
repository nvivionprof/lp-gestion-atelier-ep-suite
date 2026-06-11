#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

require_project_files
mkdir -p backups/manual
stamp="$(date +%Y%m%d-%H%M%S)"
out="backups/manual/lp-suite-backup-${stamp}.sql"

dc exec -T postgres sh -lc 'pg_dumpall -U "$POSTGRES_USER"' > "$out"
cp -a .env "backups/manual/.env-${stamp}.bak" 2>/dev/null || true
cp -a docker-compose.yml "backups/manual/docker-compose-${stamp}.yml.bak" 2>/dev/null || true
cp -a VERSION "backups/manual/VERSION-${stamp}.bak" 2>/dev/null || true

log "Sauvegarde créée : $out"
ls -lh "$out"
