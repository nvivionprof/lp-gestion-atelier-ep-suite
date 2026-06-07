#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

env_get(){
  local key="$1"
  [ -f .env ] || return 0
  awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n 1 | sed -e 's/^"//' -e 's/"$//'
}

LP_URL="$(env_get LP_CORE_PUBLIC_URL)"; LP_URL="${LP_URL:-http://localhost:9000}"
TM_URL="$(env_get TOOLMAG_PUBLIC_BASE_URL)"; TM_URL="${TM_URL:-http://localhost:9000/toolmag}"
SF_URL="$(env_get SAFETY_PUBLIC_URL)"; SF_URL="${SF_URL:-http://localhost:9000/safety}"
PD_URL="$(env_get PEDASHOP_PUBLIC_URL)"; PD_URL="${PD_URL:-$(env_get CONSUMABLES_PUBLIC_URL)}"; PD_URL="${PD_URL:-http://localhost:9000/pedashop}"
SM_URL="$(env_get SYSTEM_MANAGER_PUBLIC_URL)"; SM_URL="${SM_URL:-$(env_get INVENTORY_PUBLIC_URL)}"; SM_URL="${SM_URL:-http://localhost:9000/system}"
TP_URL="$(env_get TPMANAGER_PUBLIC_URL)"; TP_URL="${TP_URL:-http://localhost:9000/tpmanager}"
PFMP_URL="$(env_get PFMP_PUBLIC_URL)"; PFMP_URL="${PFMP_URL:-http://localhost:9000/pfmp}"

echo "État Docker :"
docker compose ps

echo "Test HTTP LP Core : $LP_URL"
curl -fsS -I "$LP_URL" >/dev/null && echo "OK LP Core" || echo "ATTENTION : LP Core ne répond pas sur $LP_URL"

echo "Test HTTP ToolMag : $TM_URL"
curl -fsS -I "$TM_URL" >/dev/null && echo "OK ToolMag" || echo "ATTENTION : ToolMag ne répond pas sur $TM_URL"

echo "Test HTTP Safety : $SF_URL"
curl -fsS -I "$SF_URL" >/dev/null && echo "OK Safety" || echo "ATTENTION : Safety ne répond pas sur $SF_URL"

echo "Test HTTP PedaShop : $PD_URL"
curl -fsS -I "$PD_URL" >/dev/null && echo "OK PedaShop" || echo "ATTENTION : PedaShop ne répond pas sur $PD_URL"


echo "Test HTTP System Manager : $SM_URL"
curl -fsS -I "$SM_URL" >/dev/null && echo "OK System Manager" || echo "ATTENTION : System Manager ne répond pas sur $SM_URL"


echo "Test HTTP TP Manager : $TP_URL"
curl -fsS -I "$TP_URL" >/dev/null && echo "OK TP Manager" || echo "ATTENTION : TP Manager ne répond pas sur $TP_URL"

echo "Test HTTP PFMP Manager : $PFMP_URL"
curl -fsS -I "$PFMP_URL" >/dev/null && echo "OK PFMP Manager" || echo "ATTENTION : PFMP Manager ne répond pas sur $PFMP_URL"

echo "Test agent de maintenance interne"
docker compose exec -T suite-admin-agent python - <<'PY' || echo "ATTENTION : suite-admin-agent ne répond pas."
import json, urllib.request, os
req = urllib.request.Request('http://127.0.0.1:8079/health', headers={'X-Agent-Token': os.getenv('LP_CORE_API_TOKEN','')})
print(urllib.request.urlopen(req, timeout=5).read().decode())
PY
