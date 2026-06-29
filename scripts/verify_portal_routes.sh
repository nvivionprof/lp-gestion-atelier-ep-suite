#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:9000}"

ROUTES=(
  "/"
  "/toolmag/"
  "/pfmp/"
  "/safety/"
  "/pedashop/"
  "/system/"
  "/tpmanager/"
  "/lpdisplaymanager/"
  "/admin-xlsx/"
  "/toolmag/xlsx/"
)

echo "Vérification des routes sur : ${BASE_URL}"

for route in "${ROUTES[@]}"; do
  url="${BASE_URL}${route}"
  code="$(curl -k -s -o /dev/null -w "%{http_code}" "$url" || true)"

  case "$code" in
    200|301|302|303|403)
      echo "[OK]   $code $route"
      ;;
    *)
      echo "[WARN] $code $route"
      ;;
  esac
done
