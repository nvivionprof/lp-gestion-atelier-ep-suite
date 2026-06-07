#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

CERT_ENV="lp-core-db/data/cert-manager.env"
if [[ ! -f "$CERT_ENV" ]]; then
  echo "ERREUR: $CERT_ENV introuvable."
  echo "Va d'abord dans LP Core > URLs / HTTPS, enregistre les paramètres, puis relance ce script."
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$CERT_ENV"
set +a

if [[ ! -f .env ]]; then
  cp .env.example .env
fi
cp .env ".env.backup-before-public-settings-$(date +%Y%m%d-%H%M%S)"

set_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" .env; then
    sed -i "s#^${key}=.*#${key}=${value}#" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

# Variables d'exposition
for key in \
  LP_DEPLOY_MODE PUBLIC_DOMAIN PUBLIC_SCHEME EXPOSURE_MODE LOCAL_PUBLIC_HOST NETWORK_PUBLIC_HOST EXTERNAL_PUBLIC_DOMAIN ENABLE_HTTPS GATEWAY_HTTP_PORT GATEWAY_HTTPS_PORT SSL_CERT_FILE SSL_KEY_FILE \
  CERT_CHALLENGE_METHOD LETSENCRYPT_EMAIL DUCKDNS_TOKEN \
  LP_CORE_PORT TOOLMAG_PORT SAFETY_PORT PEDASHOP_PORT CONSUMABLES_PORT INVENTORY_PORT SYSTEM_MANAGER_PORT TPMANAGER_PORT PFMP_PORT \
  LP_CORE_PUBLIC_URL TOOLMAG_PUBLIC_URL TOOLMAG_PUBLIC_BASE_URL SAFETY_PUBLIC_URL PEDASHOP_PUBLIC_URL CONSUMABLES_PUBLIC_URL INVENTORY_PUBLIC_URL SYSTEM_MANAGER_PUBLIC_URL TPMANAGER_PUBLIC_URL PFMP_PUBLIC_URL \
  DJANGO_ALLOWED_HOSTS CSRF_TRUSTED_ORIGINS; do
  value="${!key-}"
  if [[ -n "$value" ]]; then
    set_env "$key" "$value"
  fi
done

# Compatibilité avec les réglages Django déjà présents.
set_env "SESSION_COOKIE_SECURE" "${ENABLE_HTTPS:-0}"
set_env "CSRF_COOKIE_SECURE" "${ENABLE_HTTPS:-0}"

# En mode HTTPS/reverse proxy, les navigateurs doivent faire confiance au domaine public.
if [[ -n "${PUBLIC_DOMAIN:-}" ]]; then
  domain="${PUBLIC_DOMAIN#http://}"
  domain="${domain#https://}"
  domain="${domain%%/*}"
  domain="${domain%%:*}"
  if [[ -n "$domain" ]]; then
    set_env "DJANGO_ALLOWED_HOSTS" "${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1,*},${domain}"
    if [[ "${PUBLIC_SCHEME:-http}" = "https" ]]; then
      set_env "CSRF_TRUSTED_ORIGINS" "${CSRF_TRUSTED_ORIGINS:-http://localhost:9000,http://127.0.0.1:9000},https://${domain},http://${domain}"
    fi
  fi
fi

echo "Paramètres publics appliqués dans .env."
echo "URLs publiques :"
grep -E '^(LP_CORE_PUBLIC_URL|TOOLMAG_PUBLIC|SAFETY_PUBLIC_URL|PEDASHOP_PUBLIC_URL|SYSTEM_MANAGER_PUBLIC_URL|TPMANAGER_PUBLIC_URL|PFMP_PUBLIC_URL)=' .env || true

recreate_for_env_reload() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "Recréation des conteneurs applicatifs pour recharger .env..."
    docker compose up -d --force-recreate \
      lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app lp-gateway
    return 0
  fi
  echo "AVERTISSEMENT: docker compose introuvable. Les fichiers .env sont corrigés, mais les conteneurs doivent être recréés depuis SSH :" >&2
  echo "  cd $(pwd)" >&2
  echo "  docker compose up -d --force-recreate lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app lp-gateway" >&2
  return 0
}

recreate_for_env_reload
