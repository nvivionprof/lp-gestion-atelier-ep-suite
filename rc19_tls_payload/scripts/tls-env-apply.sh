#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="${ROOT_DIR:-$(pwd)}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
MODE="${1:-manual}"
DOMAIN="${2:-}"
DUCK_TOKEN="${3:-}"

log(){ printf '[LP-TLS] %s\n' "$*"; }
upsert(){ local k="$1" v="$2"; if grep -qE "^${k}=" "$ENV_FILE" 2>/dev/null; then sed -i "s|^${k}=.*|${k}=${v}|" "$ENV_FILE"; else printf '%s=%s\n' "$k" "$v" >> "$ENV_FILE"; fi; }

[ -f "$ENV_FILE" ] || { echo "ERREUR: .env introuvable : $ENV_FILE" >&2; exit 1; }
mkdir -p "$ROOT_DIR/ssl" "$ROOT_DIR/ssl/acme"

case "$MODE" in
  disabled)
    upsert ENABLE_HTTPS 0
    upsert HTTPS_MODE disabled
    ;;
  manual|duckdns-acme|selfsigned)
    upsert ENABLE_HTTPS 1
    upsert HTTPS_MODE "$MODE"
    upsert SSL_CERT_FILE /ssl/fullchain.pem
    upsert SSL_KEY_FILE /ssl/privkey.pem
    upsert TLS_HOST_CERT_DIR ./ssl
    if [ -n "$DOMAIN" ]; then
      upsert EXTERNAL_PUBLIC_DOMAIN "$DOMAIN"
      upsert PUBLIC_DOMAIN "${DOMAIN}:9000"
      if [ "$MODE" = "duckdns-acme" ]; then
        short="${DOMAIN%.duckdns.org}"
        upsert DUCKDNS_FULL_DOMAIN "$DOMAIN"
        upsert DUCKDNS_DOMAIN "$short"
      fi
    fi
    if [ -n "$DUCK_TOKEN" ]; then upsert DUCKDNS_TOKEN "$DUCK_TOKEN"; fi
    ;;
  *)
    echo "Usage: $0 disabled|manual|duckdns-acme|selfsigned [domaine] [token_duckdns]" >&2
    exit 2
    ;;
esac
log ".env mis à jour : HTTPS_MODE=$MODE"
log "Relance recommandée : docker compose --env-file .env up -d --force-recreate lp-gateway"
