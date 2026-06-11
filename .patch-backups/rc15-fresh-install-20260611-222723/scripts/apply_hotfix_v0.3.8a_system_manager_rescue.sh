#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-/home/user/docker/lp-gestion-atelier-ep-suite}"
PATCH_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ ! -d "$TARGET" ]; then
  echo "ERREUR : dossier cible introuvable : $TARGET" >&2
  exit 1
fi
cd "$TARGET"
BACKUP="/home/backups-lp-suite/system-manager-before-v0.3.8a-$(date +%Y%m%d-%H%M%S).tar.gz"
mkdir -p /home/backups-lp-suite

echo "[1/7] Sauvegarde applicative avant V0.3.8a..."
tar --exclude='./system-manager-db/data' --exclude='./backups' --exclude='./ssl' -czf "$BACKUP" system-manager-app lp-core-app docker-compose.yml manifest.json VERSION VERSION.txt scripts docs || true

echo "[2/7] Copie contrôlée du hotfix V0.3.8a..."
rsync -a "$PATCH_DIR/" "$TARGET/"

echo "[3/7] Reconstruction des images nécessaires..."
docker compose build lp-core-app system-manager-app lp-gateway

echo "[4/7] Arrêt éventuel du conteneur System Manager en boucle..."
docker compose stop system-manager-app || true

echo "[5/7] Vérification Django System Manager dans un conteneur one-shot..."
docker compose run --rm --entrypoint python system-manager-app manage.py check --traceback

echo "[6/7] Migrations LP Core + System Manager en one-shot..."
docker compose run --rm --entrypoint python lp-core-app manage.py migrate
docker compose run --rm --entrypoint python system-manager-app manage.py migrate

echo "[7/7] Collectstatic + redémarrage ciblé..."
docker compose run --rm --entrypoint python lp-core-app manage.py collectstatic --noinput || true
docker compose run --rm --entrypoint python system-manager-app manage.py collectstatic --noinput || true
docker compose up -d lp-core-app system-manager-app lp-gateway

echo "Hotfix V0.3.8a terminé. Sauvegarde : $BACKUP"
echo "Tests :"
echo "  docker compose ps"
echo "  curl -I http://localhost:9000/system/"
echo "  curl -I http://localhost:9000/system/parametrage/"
echo "  curl -I http://localhost:9000/system/reservations/calendrier/"
