#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR="${1:-/home/user/docker/lp-gestion-atelier-ep-suite}"
SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="/home/user/backups-lp-suite"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [ ! -d "$TARGET_DIR" ]; then
  echo "ERREUR: dossier cible introuvable: $TARGET_DIR" >&2
  exit 1
fi
mkdir -p "$BACKUP_DIR"
cd "$TARGET_DIR"

echo "[1/5] Sauvegarde des fichiers applicatifs avant V0.3.3..."
tar --exclude='./lp-core-db/data' \
    --exclude='./toolmag-db/data' \
    --exclude='./safety-db/data' \
    --exclude='./pedashop-db/data' \
    --exclude='./system-manager-db/data' \
    --exclude='./tpmanager-db/data' \
    --exclude='./pfmp-db/data' \
    --exclude='./backups' \
    --exclude='./ssl' \
    -czf "$BACKUP_DIR/lp-suite-before-v0.3.3-system-manager-$STAMP.tar.gz" .

echo "[2/5] Copie du patch V0.3.3..."
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

echo "[3/5] Reconstruction LP Core + System Manager + passerelle..."
docker compose up -d --build lp-core-app system-manager-app lp-gateway

echo "[4/5] Migrations bases LP Core et System Manager..."
docker compose exec -T lp-core-app python manage.py migrate --noinput
docker compose exec -T system-manager-app python manage.py migrate --noinput

echo "[5/5] Collectstatic et redémarrage ciblé..."
docker compose exec -T lp-core-app python manage.py collectstatic --noinput || true
docker compose exec -T system-manager-app python manage.py collectstatic --noinput || true
docker compose restart lp-core-app system-manager-app lp-gateway

echo "Mise à jour V0.3.3 terminée. Tester : http://localhost:9000/system/ et http://localhost:9000/blocs-atelier/"
