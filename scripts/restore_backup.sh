#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ARCHIVE="${1:-}"
if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
  echo "Usage : $0 backups/archive.tar.gz" >&2
  exit 1
fi
docker compose down
stamp=$(date +%Y%m%d-%H%M%S)
mkdir -p "pre-restore-$stamp"
cp -a lp-core-db toolmag-db safety-db pedashop-db system-manager-db tpmanager-db "pre-restore-$stamp/" 2>/dev/null || true
tar -xzf "$ARCHIVE"
docker compose up -d lp-gateway lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app
echo "Restauration terminée. Sauvegarde avant restauration : pre-restore-$stamp/"
