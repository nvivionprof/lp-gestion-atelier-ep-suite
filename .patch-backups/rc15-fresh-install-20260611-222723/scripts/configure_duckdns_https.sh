#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  cat <<'EOF'
Usage:
  ./scripts/configure_duckdns_https.sh <domaine.duckdns.org> <email-letsencrypt> <duckdns-token> [port_https] [port_http]

Exemple standard public :
  ./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org nvivion.prof@gmail.com TOKEN_DUCKDNS 443 80

Exemple derrière box avec redirection externe 443 -> serveur:9443 :
  ./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org nvivion.prof@gmail.com TOKEN_DUCKDNS 9443 9000

Principe :
  - DNS-01 DuckDNS : pas besoin d'ouvrir le port 80 pour obtenir le certificat.
  - Nginx lp-gateway sert ensuite HTTPS sur GATEWAY_HTTPS_PORT.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 3 ]]; then
  usage
  exit 0
fi

DOMAIN="$1"
EMAIL="$2"
TOKEN="$3"
HTTPS_PORT="${4:-443}"
HTTP_PORT="${5:-80}"

DOMAIN="${DOMAIN#http://}"
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN%%/*}"
DOMAIN="${DOMAIN%%:*}"

if [[ "$DOMAIN" != *.duckdns.org ]]; then
  echo "ERREUR: ce script est prévu pour un domaine DuckDNS (*.duckdns.org). Domaine reçu: $DOMAIN" >&2
  exit 2
fi

if [[ ! -f .env ]]; then
  echo "ERREUR: .env introuvable. Lance d'abord l'installation." >&2
  exit 2
fi

cp .env ".env.backup-before-duckdns-https-$(date +%Y%m%d-%H%M%S)"

python3 - "$DOMAIN" "$EMAIL" "$TOKEN" "$HTTPS_PORT" "$HTTP_PORT" <<'PY'
from pathlib import Path
import sys

domain, email, token, https_port, http_port = sys.argv[1:6]
env = Path('.env')
lines = env.read_text(encoding='utf-8').splitlines()
values = {
    'LP_DEPLOY_MODE': 'public',
    'PUBLIC_DOMAIN': domain,
    'PUBLIC_SCHEME': 'https',
    'EXPOSURE_MODE': 'external',
    'EXTERNAL_PUBLIC_DOMAIN': domain,
    'ENABLE_HTTPS': '1',
    'GATEWAY_HTTP_PORT': http_port,
    'GATEWAY_HTTPS_PORT': https_port,
    'LP_CORE_PUBLIC_URL': f'https://{domain}',
    'TOOLMAG_PUBLIC_BASE_URL': f'https://{domain}/toolmag/',
    'TOOLMAG_PUBLIC_URL': f'https://{domain}/toolmag/',
    'SAFETY_PUBLIC_URL': f'https://{domain}/safety/',
    'PEDASHOP_PUBLIC_URL': f'https://{domain}/pedashop/',
    'CONSUMABLES_PUBLIC_URL': f'https://{domain}/pedashop/',
    'INVENTORY_PUBLIC_URL': f'https://{domain}/system/',
    'SYSTEM_MANAGER_PUBLIC_URL': f'https://{domain}/system/',
    'TPMANAGER_PUBLIC_URL': f'https://{domain}/tpmanager/',
    'PFMP_PUBLIC_URL': f'https://{domain}/pfmp/',
    'DJANGO_ALLOWED_HOSTS': f'localhost,127.0.0.1,{domain}',
    'CSRF_TRUSTED_ORIGINS': f'https://{domain},http://localhost:9000,http://127.0.0.1:9000',
    'SESSION_COOKIE_SECURE': '1',
    'CSRF_COOKIE_SECURE': '1',
    'SSL_DIR': './ssl',
    'SSL_CERT_FILE': '/ssl/fullchain.pem',
    'SSL_KEY_FILE': '/ssl/privkey.pem',
    'CERT_CHALLENGE_METHOD': 'dns_duckdns',
    'LETSENCRYPT_EMAIL': email,
    'DUCKDNS_TOKEN': token,
}

seen = set()
out = []
for line in lines:
    if not line or line.lstrip().startswith('#') or '=' not in line:
        out.append(line)
        continue
    key = line.split('=', 1)[0]
    if key in values:
        out.append(f'{key}={values[key]}')
        seen.add(key)
    else:
        out.append(line)
for key, value in values.items():
    if key not in seen:
        out.append(f'{key}={value}')
env.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')

cert_env = Path('lp-core-db/data/cert-manager.env')
cert_env.parent.mkdir(parents=True, exist_ok=True)
cert_env.write_text('\n'.join(f'{k}={v}' for k, v in values.items() if k in {
    'PUBLIC_DOMAIN','PUBLIC_SCHEME','ENABLE_HTTPS','GATEWAY_HTTP_PORT','GATEWAY_HTTPS_PORT',
    'SSL_DIR','SSL_CERT_FILE','SSL_KEY_FILE','CERT_CHALLENGE_METHOD','LETSENCRYPT_EMAIL','DUCKDNS_TOKEN',
    'LP_CORE_PUBLIC_URL','TOOLMAG_PUBLIC_BASE_URL','SAFETY_PUBLIC_URL','PEDASHOP_PUBLIC_URL',
    'SYSTEM_MANAGER_PUBLIC_URL','TPMANAGER_PUBLIC_URL','PFMP_PUBLIC_URL','DJANGO_ALLOWED_HOSTS','CSRF_TRUSTED_ORIGINS'
}) + '\n', encoding='utf-8')
PY

chmod +x scripts/cert_manager.sh

echo "[1/4] Génération / installation du certificat Let's Encrypt DuckDNS"
./scripts/cert_manager.sh issue

echo "[2/4] Recréation rapide des conteneurs applicatifs pour recharger .env"
docker compose --env-file .env up -d --build lp-gateway lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app

echo "[3/4] Statut certificat"
./scripts/cert_manager.sh status

echo "[4/4] Contrôle HTTPS"
curl -k -sSI "https://${DOMAIN}:${HTTPS_PORT}/" | head || true

echo "HTTPS DuckDNS configuré. URL principale : https://${DOMAIN}${HTTPS_PORT:+:${HTTPS_PORT}}/"
echo "Si le port public externe est 443 redirigé vers ce port interne, l'URL utilisateur est simplement : https://${DOMAIN}/"
