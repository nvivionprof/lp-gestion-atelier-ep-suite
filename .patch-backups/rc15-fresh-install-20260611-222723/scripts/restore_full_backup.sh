#!/usr/bin/env bash
set -euo pipefail
ZIP_PATH="${1:-}"
if [[ -z "$ZIP_PATH" || ! -f "$ZIP_PATH" ]]; then
  echo "ERREUR: archive de sauvegarde introuvable: $ZIP_PATH" >&2
  exit 1
fi
cd "$(dirname "$0")/.."
SUITE_ROOT="$(pwd)"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
RESTORE_BASE="$SUITE_ROOT/backups/restore-staging"
STAGING="$RESTORE_BASE/$RUN_ID"
mkdir -p "$STAGING" "$SUITE_ROOT/backups/pre-restore"
python3 - "$ZIP_PATH" <<'RESTORE_PY_CHECK'
import sys, zipfile, pathlib
zip_path = sys.argv[1]
with zipfile.ZipFile(zip_path) as zf:
    names = zf.namelist()
    if not names:
        raise SystemExit('ZIP vide')
    for name in names:
        clean = name.replace('\\','/')
        parts = pathlib.PurePosixPath(clean).parts
        if clean.startswith('/') or '..' in parts:
            raise SystemExit(f'Chemin interdit dans la sauvegarde: {name}')
print('Sauvegarde ZIP vérifiée.')
RESTORE_PY_CHECK
unzip -q "$ZIP_PATH" -d "$STAGING"
SRC="$STAGING"
if [[ ! -f "$SRC/manifest.json" ]]; then
  CANDIDATE="$(find "$STAGING" -mindepth 1 -maxdepth 2 -name manifest.json -print -quit | xargs -r dirname)"
  if [[ -n "$CANDIDATE" && -f "$CANDIDATE/manifest.json" ]]; then
    SRC="$CANDIDATE"
  fi
fi
if [[ ! -f "$SRC/manifest.json" ]]; then
  echo "ERREUR: manifest.json absent. Restauration refusée." >&2
  exit 1
fi
if [[ -f "$SRC/checksums.sha256" ]]; then
  echo "Vérification SHA-256..."
  (cd "$SRC" && sha256sum -c checksums.sha256) || { echo "ERREUR: contrôle SHA-256 en échec." >&2; exit 1; }
fi
echo "Sauvegarde de sécurité avant restauration..."
if [[ -x "$SUITE_ROOT/scripts/full_backup.sh" ]]; then
  "$SUITE_ROOT/scripts/full_backup.sh" "pre-restore" || true
fi

if [[ -d "$SRC/databases" && -x "$SUITE_ROOT/scripts/postgres/restore_database_backup.sh" ]]; then
  echo "Restauration des dumps PostgreSQL contenus dans la sauvegarde complète..."
  "$SUITE_ROOT/scripts/postgres/restore_database_backup.sh" "$ZIP_PATH" all || { echo "ERREUR: restauration PostgreSQL en échec." >&2; exit 1; }
fi

echo "Arrêt des conteneurs applicatifs, sans arrêter suite-admin-agent..."
docker container stop lp-gateway lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app suite-backup-scheduler 2>/dev/null || true
restore_path(){
  local name="$1"
  if [[ -e "$SRC/$name" ]]; then
    echo "Restauration: $name"
    rm -rf "$SUITE_ROOT/$name"
    mkdir -p "$(dirname "$SUITE_ROOT/$name")"
    cp -a "$SRC/$name" "$SUITE_ROOT/$name"
  else
    echo "Info: $name absent de la sauvegarde."
  fi
}
restore_path ".env"
for d in lp-core-db toolmag-db safety-db pedashop-db system-manager-db tpmanager-db media uploads ssl imports logs; do
  restore_path "$d"
done
mkdir -p lp-core-db/data toolmag-db/data safety-db/data pedashop-db/data system-manager-db/data tpmanager-db/data ssl backups imports logs updates/incoming updates/logs
chmod +x install.sh start.sh stop.sh upgrade.sh scripts/*.sh 2>/dev/null || true
echo "Redémarrage de la suite..."
docker compose up -d --build
echo "Migrations après restauration..."
if [[ -x "$SUITE_ROOT/scripts/migrate_all.sh" ]]; then
  "$SUITE_ROOT/scripts/migrate_all.sh" || true
fi
echo "Contrôle santé après restauration..."
if [[ -x "$SUITE_ROOT/scripts/check_health.sh" ]]; then
  "$SUITE_ROOT/scripts/check_health.sh" || true
fi
echo "Restauration complète terminée depuis $ZIP_PATH"
