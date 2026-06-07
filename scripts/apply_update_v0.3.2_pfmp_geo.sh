#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-/home/user/docker/lp-gestion-atelier-ep-suite}"
PATCH_DIR="${PATCH_DIR:-$(pwd)}"
BACKUP_DIR="${BACKUP_DIR:-/home/user/backups-lp-suite}"
mkdir -p "$BACKUP_DIR"
cd "$PROJECT_DIR"
BACKUP_NAME="lp-suite-before-v0.3.2-pfmp-$(date +%Y%m%d-%H%M%S).tar.gz"
tar --exclude='./lp-core-db/data' \
    --exclude='./toolmag-db/data' \
    --exclude='./safety-db/data' \
    --exclude='./pedashop-db/data' \
    --exclude='./system-manager-db/data' \
    --exclude='./tpmanager-db/data' \
    --exclude='./pfmp-db/data' \
    --exclude='./backups' \
    --exclude='./ssl' \
    -czf "$BACKUP_DIR/$BACKUP_NAME" .
docker compose down
rsync -a "$PATCH_DIR"/ ./
docker compose up -d --build pfmp-app lp-gateway
echo "Mise à jour PFMP V0.3.2 appliquée. Sauvegarde : $BACKUP_DIR/$BACKUP_NAME"
echo "Tester : http://localhost:9000/pfmp/carte/"
