#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-/home/user/docker/lp-gestion-atelier-ep-suite}"
PATCH_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ ! -d "$TARGET" ]; then
  echo "ERREUR : dossier cible introuvable : $TARGET" >&2
  exit 1
fi
cd "$TARGET"
BACKUP="/home/backups-lp-suite/system-manager-before-v0.3.8-$(date +%Y%m%d-%H%M%S).tar.gz"
mkdir -p /home/backups-lp-suite
echo "[1/6] Sauvegarde applicative avant V0.3.8..."
tar --exclude='./system-manager-db/data' --exclude='./backups' --exclude='./ssl' -czf "$BACKUP" system-manager-app lp-core-app docker-compose.yml manifest.json VERSION VERSION.txt scripts docs || true
echo "[2/6] Copie contrôlée du patch V0.3.8..."
rsync -a "$PATCH_DIR/" "$TARGET/"
echo "[3/6] Reconstruction LP Core + System Manager + passerelle..."
docker compose up -d --build lp-core-app system-manager-app lp-gateway
echo "[4/6] Migrations LP Core + System Manager..."
docker compose exec lp-core-app python manage.py migrate
docker compose exec system-manager-app python manage.py migrate
echo "[5/6] Collectstatic LP Core + System Manager..."
docker compose exec lp-core-app python manage.py collectstatic --noinput || true
docker compose exec system-manager-app python manage.py collectstatic --noinput || true
echo "[6/6] Redémarrage ciblé..."
docker compose restart lp-core-app system-manager-app lp-gateway
echo "Mise à jour V0.3.8 terminée. Sauvegarde : $BACKUP"
echo "Tests conseillés :"
echo "  curl -I http://localhost:9000/system/"
echo "  curl -I http://localhost:9000/system/reservations/calendrier/"
echo "  curl -I http://localhost:9000/system/parametrage/"
