#!/usr/bin/env bash
set -euo pipefail

echo "=== Réparation / vérification routes LP Suite ==="

if [ -f scripts/configure_public_urls.sh ]; then
  echo "[INFO] Application configuration URLs publiques"
  bash scripts/configure_public_urls.sh || true
fi

if [ -f scripts/verify_portal_routes.sh ]; then
  echo "[INFO] Vérification routes locales"
  bash scripts/verify_portal_routes.sh http://localhost:9000 || true
fi

echo "=== Fin réparation routes ==="
