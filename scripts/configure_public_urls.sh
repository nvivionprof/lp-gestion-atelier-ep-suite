#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env

env_get(){
  local key="$1"
  awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n 1 | sed -e 's/^"//' -e 's/"$//'
}

set_env_py(){
python3 - "$@" <<'CONFIG_PY'
import sys
from pathlib import Path
p=Path('.env')
text=p.read_text() if p.exists() else ''
values=dict(arg.split('=',1) for arg in sys.argv[1:])
lines=[]; seen=set()
for line in text.splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key=line.split('=',1)[0].strip()
        if key in values:
            lines.append(f'{key}={values[key]}'); seen.add(key)
        else:
            lines.append(line)
    else:
        lines.append(line)
for k,v in values.items():
    if k not in seen:
        lines.append(f'{k}={v}')
p.write_text('\n'.join(lines).rstrip()+'\n')
CONFIG_PY
}

append_port(){
  local scheme="$1" host="$2" port="$3"
  if [[ "$scheme" == "http" && "$port" == "80" ]]; then
    printf "%s://%s" "$scheme" "$host"
  elif [[ "$scheme" == "https" && "$port" == "443" ]]; then
    printf "%s://%s" "$scheme" "$host"
  else
    printf "%s://%s:%s" "$scheme" "$host" "$port"
  fi
}

DEFAULT_MODE="$(env_get LP_DEPLOY_MODE)"; DEFAULT_MODE="${DEFAULT_MODE:-reseau}"
if [[ "$DEFAULT_MODE" == "production" ]]; then DEFAULT_MODE="reseau"; fi

echo "Configuration des adresses publiques."
echo "Choix conseillé pour le lycée : mode reseau, adresse IP du serveur, port 9000."
read -rp "Mode de déploiement [local/reseau] (${DEFAULT_MODE}) : " MODE_IN
LP_DEPLOY_MODE="${MODE_IN:-$DEFAULT_MODE}"

DEFAULT_PORT="$(env_get GATEWAY_HTTP_PORT)"; DEFAULT_PORT="${DEFAULT_PORT:-9000}"
DEFAULT_HTTPS_PORT="$(env_get GATEWAY_HTTPS_PORT)"; DEFAULT_HTTPS_PORT="${DEFAULT_HTTPS_PORT:-9443}"

if [[ "$LP_DEPLOY_MODE" == "local" ]]; then
  PUBLIC_DOMAIN="localhost"
  GATEWAY_HTTP_PORT="${DEFAULT_PORT:-9000}"
  read -rp "Port externe du portail HTTP [${GATEWAY_HTTP_PORT}] : " PORT_IN
  GATEWAY_HTTP_PORT="${PORT_IN:-$GATEWAY_HTTP_PORT}"
else
  LP_DEPLOY_MODE="reseau"
  DEFAULT_DOMAIN="$(env_get PUBLIC_DOMAIN)"
  if [[ -z "$DEFAULT_DOMAIN" || "$DEFAULT_DOMAIN" == "localhost" || "$DEFAULT_DOMAIN" == "127.0.0.1" ]]; then
    DEFAULT_DOMAIN="$(hostname -I 2>/dev/null | awk '{print $1}')"
  fi
  DEFAULT_DOMAIN="${DEFAULT_DOMAIN:-192.168.101.19}"
  read -rp "Adresse IP ou nom DNS du serveur [${DEFAULT_DOMAIN}] : " DOMAIN_IN
  PUBLIC_DOMAIN="${DOMAIN_IN:-$DEFAULT_DOMAIN}"
  read -rp "Port externe du portail HTTP [${DEFAULT_PORT}] : " PORT_IN
  GATEWAY_HTTP_PORT="${PORT_IN:-$DEFAULT_PORT}"
fi

# Par défaut cette bêta reste en HTTP sur port 9000 afin de ne pas entrer en conflit avec 80/443.
PUBLIC_SCHEME="http"
ENABLE_HTTPS="0"
GATEWAY_HTTPS_PORT="${DEFAULT_HTTPS_PORT:-9443}"
LP_CORE_PORT="$GATEWAY_HTTP_PORT"
BASE="$(append_port "$PUBLIC_SCHEME" "$PUBLIC_DOMAIN" "$GATEWAY_HTTP_PORT")"
CSRF="${BASE},http://localhost:${GATEWAY_HTTP_PORT},http://127.0.0.1:${GATEWAY_HTTP_PORT}"
ALLOWED="${PUBLIC_DOMAIN},localhost,127.0.0.1,*"

set_env_py \
  "LP_DEPLOY_MODE=${LP_DEPLOY_MODE}" \
  "SERVER_IP=${PUBLIC_DOMAIN}" \
  "PUBLIC_DOMAIN=${PUBLIC_DOMAIN}" \
  "PUBLIC_SCHEME=${PUBLIC_SCHEME}" \
  "EXPOSURE_MODE=reverse_proxy" \
  "ENABLE_HTTPS=${ENABLE_HTTPS}" \
  "GATEWAY_HTTP_PORT=${GATEWAY_HTTP_PORT}" \
  "GATEWAY_HTTPS_PORT=${GATEWAY_HTTPS_PORT}" \
  "LP_CORE_PORT=${LP_CORE_PORT}" \
  "LP_CORE_PUBLIC_URL=${BASE}" \
  "TOOLMAG_PUBLIC_BASE_URL=${BASE}/toolmag/" \
  "SAFETY_PUBLIC_URL=${BASE}/safety/" \
  "PEDASHOP_PUBLIC_URL=${BASE}/pedashop/" \
  "CONSUMABLES_PUBLIC_URL=${BASE}/pedashop/" \
  "INVENTORY_PUBLIC_URL=${BASE}/system/" \
  "SYSTEM_MANAGER_PUBLIC_URL=${BASE}/system/" \
  "TPMANAGER_PUBLIC_URL=${BASE}/tpmanager/" \
  "PFMP_PUBLIC_URL=${BASE}/pfmp/" \
  "DJANGO_ALLOWED_HOSTS=${ALLOWED}" \
  "CSRF_TRUSTED_ORIGINS=${CSRF}" \
  "SESSION_COOKIE_SECURE=${ENABLE_HTTPS}" \
  "CSRF_COOKIE_SECURE=${ENABLE_HTTPS}"

echo "Configuration publique mise à jour :"
grep -E '^(LP_DEPLOY_MODE|PUBLIC_DOMAIN|PUBLIC_SCHEME|ENABLE_HTTPS|GATEWAY_HTTP_PORT|GATEWAY_HTTPS_PORT|LP_CORE_PUBLIC_URL|TOOLMAG_PUBLIC_BASE_URL|SAFETY_PUBLIC_URL|PEDASHOP_PUBLIC_URL|SYSTEM_MANAGER_PUBLIC_URL|TPMANAGER_PUBLIC_URL|PFMP_PUBLIC_URL)=' .env
