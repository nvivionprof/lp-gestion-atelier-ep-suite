#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
COMPOSE=(docker compose -f "$ROOT_DIR/docker-compose.yml" --env-file "$ROOT_DIR/.env")

echo "[LP Suite] Réparation routes après coupure WSL/Docker — aucun volume supprimé"
"${COMPOSE[@]}" up -d postgres || true
"${COMPOSE[@]}" up -d --build lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app lp-gateway

echo "[LP Suite] Migrations rapides"
for svc in lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
  echo "===== migrate $svc ====="
  "${COMPOSE[@]}" run --rm "$svc" python manage.py migrate || true
  echo "===== collectstatic $svc ====="
  "${COMPOSE[@]}" run --rm "$svc" python manage.py collectstatic --noinput || true
done

echo "[LP Suite] Redémarrage gateway"
"${COMPOSE[@]}" restart lp-gateway
"${COMPOSE[@]}" ps

echo "[LP Suite] Contrôle routes"
for url in \
  http://localhost:9000/ \
  http://localhost:9000/toolmag/ \
  http://localhost:9000/safety/ \
  http://localhost:9000/pedashop/ \
  http://localhost:9000/system/ \
  http://localhost:9000/tpmanager/ \
  http://localhost:9000/pfmp/
do
  echo
  echo "===== $url ====="
  curl -sSI "$url" | grep -Ei 'HTTP/|location:|x-lp-gateway-module' || true
done
