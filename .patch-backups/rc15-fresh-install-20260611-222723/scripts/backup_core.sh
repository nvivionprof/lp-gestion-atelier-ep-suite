#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)
tar -czf "backups/lp-core-backup-$stamp.tar.gz" lp-core-db/data imports .env 2>/dev/null || true
echo "Sauvegarde LP Core créée."
