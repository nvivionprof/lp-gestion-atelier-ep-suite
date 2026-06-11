#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)
tar -czf "backups/toolmag-backup-$stamp.tar.gz" toolmag-db/data .env 2>/dev/null || true
echo "Sauvegarde ToolMag créée."
