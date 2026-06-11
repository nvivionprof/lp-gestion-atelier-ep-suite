#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-/home/user/docker/lp-gestion-atelier-ep-suite}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -d "$TARGET" ]; then echo "Dossier cible introuvable: $TARGET" >&2; exit 1; fi
cd "$TARGET"
echo "[1/6] Sauvegarde applicative avant V0.3.7..."
mkdir -p /home/backups-lp-suite
BACKUP="/home/backups-lp-suite/lp-suite-before-v0.3.7-$(date +%Y%m%d-%H%M%S).tar.gz"
tar --exclude='./lp-core-db/data' --exclude='./toolmag-db/data' --exclude='./safety-db/data' --exclude='./pedashop-db/data' --exclude='./system-manager-db/data' --exclude='./tpmanager-db/data' --exclude='./pfmp-db/data' --exclude='./backups' --exclude='./ssl' -czf "$BACKUP" . || true
echo "[2/6] Copie du patch V0.3.7..."
rsync -a "$PATCH_DIR/" "$TARGET/"
echo "[3/6] Reconstruction System Manager (LibreOffice pour prévisualisation Office) + passerelle..."
docker compose up -d --build system-manager-app lp-gateway
echo "[4/6] Migrations System Manager..."
docker compose exec system-manager-app python manage.py migrate
echo "[5/6] Collectstatic System Manager..."
docker compose exec system-manager-app python manage.py collectstatic --noinput || true
echo "[6/6] Redémarrage ciblé..."
docker compose restart system-manager-app lp-gateway
echo "Mise à jour V0.3.7 terminée. Sauvegarde: $BACKUP"
