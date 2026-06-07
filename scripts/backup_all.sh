#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -x scripts/full_backup.sh ]]; then
  exec scripts/full_backup.sh manual
fi
mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)
archive="backups/lp-suite-backup-$stamp.tar.gz"
tar -czf "$archive" lp-core-db/data toolmag-db/data safety-db/data pedashop-db/data system-manager-db/data tpmanager-db/data imports .env 2>/dev/null || true
echo "Sauvegarde créée : $archive"
