#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose up -d lp-gateway lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app suite-admin-agent

env_get(){
  local key="$1"
  [ -f .env ] || return 0
  awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n 1 | sed -e 's/^"//' -e 's/"$//'
}

echo "LP Core        : $(env_get LP_CORE_PUBLIC_URL)"
echo "ToolMag        : $(env_get TOOLMAG_PUBLIC_BASE_URL)"
echo "Safety         : $(env_get SAFETY_PUBLIC_URL)"
echo "PedaShop       : $(env_get PEDASHOP_PUBLIC_URL)"
echo "System Manager : $(env_get SYSTEM_MANAGER_PUBLIC_URL)"
echo "TP Manager     : $(env_get TPMANAGER_PUBLIC_URL)"
