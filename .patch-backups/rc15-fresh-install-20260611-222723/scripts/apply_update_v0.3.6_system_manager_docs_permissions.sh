#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR="${1:-/home/user/docker/lp-gestion-atelier-ep-suite}"
SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="/home/backups-lp-suite"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [ ! -d "$TARGET_DIR" ]; then
  echo "ERREUR: dossier cible introuvable: $TARGET_DIR" >&2
  exit 1
fi
for required in system-manager-app/system_manager/models.py system-manager-app/system_manager/views.py system-manager-app/system_manager/forms.py system-manager-app/system_manager/migrations/0004_v036_document_versions_temp_permissions.py; do
  if [ ! -e "$SOURCE_DIR/$required" ]; then
    echo "ERREUR: archive/patch incomplet, élément manquant: $required" >&2
    exit 1
  fi
done

mkdir -p "$BACKUP_DIR"
cd "$TARGET_DIR"

echo "[1/6] Sauvegarde applicative avant V0.3.6..."
tar --exclude='./lp-core-db/data' \
    --exclude='./toolmag-db/data' \
    --exclude='./safety-db/data' \
    --exclude='./pedashop-db/data' \
    --exclude='./system-manager-db/data' \
    --exclude='./tpmanager-db/data' \
    --exclude='./pfmp-db/data' \
    --exclude='./backups' \
    --exclude='./ssl' \
    -czf "$BACKUP_DIR/lp-suite-before-v0.3.6-$STAMP.tar.gz" .

echo "[2/6] Copie contrôlée V0.3.6..."
rsync -a "$SOURCE_DIR/" "$TARGET_DIR/" \
  --exclude '.env' \
  --exclude 'lp-core-db/data/' \
  --exclude 'toolmag-db/data/' \
  --exclude 'safety-db/data/' \
  --exclude 'pedashop-db/data/' \
  --exclude 'system-manager-db/data/' \
  --exclude 'tpmanager-db/data/' \
  --exclude 'pfmp-db/data/' \
  --exclude 'backups/' \
  --exclude 'ssl/'

echo "[3/6] Reconstruction ciblée System Manager + passerelle..."
docker compose build system-manager-app lp-gateway
docker compose up -d --no-deps system-manager-app lp-gateway

echo "[4/6] Migration System Manager..."
docker compose exec -T system-manager-app python manage.py migrate --noinput

echo "[5/6] Collectstatic System Manager..."
docker compose exec -T system-manager-app python manage.py collectstatic --noinput || true

echo "[6/6] Redémarrage ciblé..."
docker compose restart system-manager-app lp-gateway

echo "Mise à jour V0.3.6 terminée. Tests :"
echo "  http://localhost:9000/system/"
echo "  http://localhost:9000/system/parametrage/"
echo "  http://localhost:9000/system/parametrage/droits-temporaires/"
