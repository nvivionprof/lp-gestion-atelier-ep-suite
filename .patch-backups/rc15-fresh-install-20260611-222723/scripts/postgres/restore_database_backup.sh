#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/db_common.sh"

ZIP_PATH="${1:-}"
REQUESTED_MODULE="${2:-auto}"
if [[ -z "$ZIP_PATH" || ! -f "$ZIP_PATH" ]]; then
  echo "ERREUR: archive ZIP de sauvegarde base introuvable: $ZIP_PATH" >&2
  exit 1
fi
RUN_ID="$(date +%Y%m%d-%H%M%S)"
STAGING="$SUITE_ROOT/backups/restore-db-staging/$RUN_ID"
mkdir -p "$STAGING"

python3 - "$ZIP_PATH" <<'PY_RESTORE_CHECK'
import pathlib, sys, zipfile
path = sys.argv[1]
with zipfile.ZipFile(path) as zf:
    names = zf.namelist()
    if not names:
        raise SystemExit('ZIP vide')
    for name in names:
        clean = name.replace('\\', '/')
        parts = pathlib.PurePosixPath(clean).parts
        if clean.startswith('/') or '..' in parts:
            raise SystemExit(f'Chemin interdit: {name}')
print('Archive ZIP vérifiée.')
PY_RESTORE_CHECK

unzip -q "$ZIP_PATH" -d "$STAGING"
if [[ ! -f "$STAGING/manifest.json" ]]; then
  echo "ERREUR: manifest.json absent. Restauration refusée." >&2
  exit 1
fi
if [[ -f "$STAGING/checksums.sha256" ]]; then
  (cd "$STAGING" && sha256sum -c checksums.sha256)
fi

ensure_postgres

restore_one(){
  local module="$1"
  local dump="$STAGING/databases/${module}.dump"
  local db service
  if [[ ! -f "$dump" ]]; then
    echo "Dump absent pour $module : $dump" >&2
    return 1
  fi
  db="$(module_db "$module")"
  service="$(module_service "$module")"
  safe_db_name "$db"
  echo "Restauration base $module -> $db"
  docker compose stop "$service" >/dev/null 2>&1 || true
  create_db_if_missing "$db"
  pg_exec psql -U "$POSTGRES_USER" -d "$db" <<SQL
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public AUTHORIZATION "$POSTGRES_USER";
GRANT ALL ON SCHEMA public TO "$POSTGRES_USER";
SQL
  cat "$dump" | pg_exec pg_restore -U "$POSTGRES_USER" -d "$db" --no-owner --no-privileges
  docker compose up -d "$service" >/dev/null 2>&1 || true
  if [[ -x "$SUITE_ROOT/scripts/migrate_all.sh" ]]; then
    "$SUITE_ROOT/scripts/migrate_all.sh" --module "$module" || true
  fi
}

if [[ "$REQUESTED_MODULE" != "auto" ]]; then
  MODULE="$(norm_module "$REQUESTED_MODULE")" || { echo "Module demandé invalide: $REQUESTED_MODULE" >&2; exit 1; }
  if [[ "$MODULE" = "all" ]]; then
    for module in "${MODULES[@]}"; do restore_one "$module"; done
  else
    restore_one "$MODULE"
  fi
else
  found=0
  for module in "${MODULES[@]}"; do
    if [[ -f "$STAGING/databases/${module}.dump" ]]; then
      found=1
      restore_one "$module"
    fi
  done
  if [[ "$found" = "0" ]]; then
    echo "ERREUR: aucun dump de module trouvé dans databases/*.dump" >&2
    exit 1
  fi
fi

docker compose up -d lp-gateway >/dev/null 2>&1 || true
echo "Restauration base terminée depuis $ZIP_PATH"
