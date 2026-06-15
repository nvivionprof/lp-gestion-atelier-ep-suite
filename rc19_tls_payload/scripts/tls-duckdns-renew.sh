#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${ROOT_DIR:-$(pwd)}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
CERT_DIR="${TLS_HOST_CERT_DIR:-$ROOT_DIR/ssl}"
ACME_HOME="${ACME_HOME:-$ROOT_DIR/ssl/acme}"

log(){ printf '\033[1;34m[LP-TLS]\033[0m %s\n' "$*"; }
err(){ printf '\033[1;31m[LP-TLS][ERREUR]\033[0m %s\n' "$*" >&2; }

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

DUCKDNS_FULL_DOMAIN="${DUCKDNS_FULL_DOMAIN:-${DUCKDNS_DOMAIN:-}.duckdns.org}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"
ACME_BIN="$(command -v acme.sh || true)"
if [ -z "$ACME_BIN" ]; then ACME_BIN="$HOME/.acme.sh/acme.sh"; fi

if [ ! -x "$ACME_BIN" ]; then err "acme.sh introuvable."; exit 1; fi
if [ -z "$DUCKDNS_TOKEN" ] || [ "$DUCKDNS_TOKEN" = "CHANGE_ME_NEVER_COMMIT" ]; then err "DUCKDNS_TOKEN manquant."; exit 1; fi

export DuckDNS_Token="$DUCKDNS_TOKEN"
mkdir -p "$CERT_DIR" "$ACME_HOME"

log "Renouvellement certificat $DUCKDNS_FULL_DOMAIN..."
"$ACME_BIN" --renew -d "$DUCKDNS_FULL_DOMAIN" --home "$ACME_HOME" --force || true
"$ACME_BIN" --install-cert \
  -d "$DUCKDNS_FULL_DOMAIN" \
  --home "$ACME_HOME" \
  --fullchain-file "$CERT_DIR/fullchain.pem" \
  --key-file "$CERT_DIR/privkey.pem" \
  --reloadcmd "docker compose restart lp-gateway 2>/dev/null || docker compose restart lp-core-proxy 2>/dev/null || docker compose restart suite-proxy 2>/dev/null || docker compose restart nginx 2>/dev/null || true"
chmod 644 "$CERT_DIR/fullchain.pem"
chmod 600 "$CERT_DIR/privkey.pem"
openssl x509 -in "$CERT_DIR/fullchain.pem" -noout -subject -issuer -dates
log "Renouvellement terminé."
