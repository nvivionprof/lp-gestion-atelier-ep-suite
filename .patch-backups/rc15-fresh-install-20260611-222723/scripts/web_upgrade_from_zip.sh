#!/usr/bin/env bash
set -euo pipefail

ZIP_PATH="${1:-}"
if [[ -z "$ZIP_PATH" || ! -f "$ZIP_PATH" ]]; then
  echo "ERREUR: ZIP de mise à jour introuvable: $ZIP_PATH" >&2
  exit 1
fi

cd "$(dirname "$0")/.."
SUITE_ROOT="$(pwd)"
STAGING_BASE="$SUITE_ROOT/updates/staging"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
STAGING="$STAGING_BASE/$RUN_ID"
mkdir -p "$STAGING" "$SUITE_ROOT/updates/logs"

safe_unzip_test() {
  python3 - "$ZIP_PATH" <<'PY'
import sys, zipfile, pathlib
zip_path = sys.argv[1]
with zipfile.ZipFile(zip_path) as zf:
    names = zf.namelist()
    if not names:
        raise SystemExit('ZIP vide')
    for name in names:
        clean = name.replace('\\', '/')
        parts = pathlib.PurePosixPath(clean).parts
        if clean.startswith('/') or '..' in parts:
            raise SystemExit(f'Chemin interdit dans le ZIP: {name}')
print('ZIP vérifié.')
PY
}

safe_unzip_test

echo "Chargement politique de sauvegarde..."
[ -f "$SUITE_ROOT/.env" ] && set -a && . "$SUITE_ROOT/.env" && set +a || true
[ -f "$SUITE_ROOT/lp-core-db/data/backup-policy.env" ] && set -a && . "$SUITE_ROOT/lp-core-db/data/backup-policy.env" && set +a || true
BACKUP_PRE_UPGRADE_REQUIRED="${BACKUP_PRE_UPGRADE_REQUIRED:-1}"
BACKUP_BLOCK_UPDATE_IF_BACKUP_FAILED="${BACKUP_BLOCK_UPDATE_IF_BACKUP_FAILED:-1}"
echo "Sauvegarde complète avant mise à jour..."
if [[ "$BACKUP_PRE_UPGRADE_REQUIRED" == "1" ]]; then
  if [[ -x "$SUITE_ROOT/scripts/full_backup.sh" ]]; then
    if ! "$SUITE_ROOT/scripts/full_backup.sh" pre-upgrade; then
      echo "ERREUR: sauvegarde pré-mise-à-jour échouée." >&2
      if [[ "$BACKUP_BLOCK_UPDATE_IF_BACKUP_FAILED" == "1" ]]; then
        echo "Mise à jour bloquée conformément à la politique LP Core." >&2
        exit 1
      fi
    fi
  else
    echo "ERREUR: full_backup.sh introuvable." >&2
    if [[ "$BACKUP_BLOCK_UPDATE_IF_BACKUP_FAILED" == "1" ]]; then
      exit 1
    fi
  fi
else
  echo "Sauvegarde pré-mise-à-jour non obligatoire selon la politique LP Core."
fi

echo "Extraction dans $STAGING"
unzip -q "$ZIP_PATH" -d "$STAGING"

# Détecte le dossier racine de la suite dans le ZIP.
SRC=""
if [[ -f "$STAGING/docker-compose.yml" ]]; then
  SRC="$STAGING"
else
  while IFS= read -r candidate; do
    if [[ -f "$candidate/docker-compose.yml" ]]; then
      SRC="$candidate"
      break
    fi
  done < <(find "$STAGING" -mindepth 1 -maxdepth 3 -type d | sort)
fi
if [[ -z "$SRC" ]]; then
  echo "ERREUR: docker-compose.yml introuvable dans le ZIP." >&2
  exit 1
fi

echo "Source détectée: $SRC"

echo "Synchronisation des fichiers applicatifs..."
rsync -a --delete \
  --exclude='.env' \
  --exclude='ssl/' \
  --exclude='backups/' \
  --exclude='logs/' \
  --exclude='updates/' \
  --exclude='lp-core-db/' \
  --exclude='toolmag-db/' \
  --exclude='safety-db/' \
  --exclude='pedashop-db/' \
  --exclude='system-manager-db/' \
  --exclude='tpmanager-db/' \
  --exclude='.git/' \
  "$SRC/" "$SUITE_ROOT/"

mkdir -p lp-core-db/data toolmag-db/data safety-db/data pedashop-db/data system-manager-db/data tpmanager-db/data ssl backups imports logs updates/incoming updates/staging updates/logs
chmod +x install.sh start.sh stop.sh upgrade.sh scripts/*.sh 2>/dev/null || true

echo "Application des paramètres publics si disponibles..."
if [[ -x "$SUITE_ROOT/scripts/apply_public_settings.sh" && -f "$SUITE_ROOT/lp-core-db/data/cert-manager.env" ]]; then
  "$SUITE_ROOT/scripts/apply_public_settings.sh" || true
fi

echo "Reconstruction et redémarrage Docker Compose..."
docker compose up -d --build

echo "Migrations après mise à jour..."
if [[ -x "$SUITE_ROOT/scripts/migrate_all.sh" ]]; then
  "$SUITE_ROOT/scripts/migrate_all.sh" || true
fi

echo "Contrôle santé après mise à jour..."
if [[ -x "$SUITE_ROOT/scripts/check_health.sh" ]]; then
  "$SUITE_ROOT/scripts/check_health.sh" || true
fi

echo "Mise à jour terminée depuis $ZIP_PATH"
