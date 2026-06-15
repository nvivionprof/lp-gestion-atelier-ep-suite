#!/usr/bin/env bash
set -Eeuo pipefail

# LP Suite RC19 — génération certificat DuckDNS Let's Encrypt par DNS-01.
# Usage recommandé :
#   cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
#   export DUCKDNS_TOKEN="..."
#   ./scripts/tls-duckdns-issue.sh

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

DUCKDNS_DOMAIN="${DUCKDNS_DOMAIN:-}"
DUCKDNS_FULL_DOMAIN="${DUCKDNS_FULL_DOMAIN:-}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"
TLS_EMAIL="${TLS_EMAIL:-admin@example.local}"
ACME_DNS_SLEEP="${ACME_DNS_SLEEP:-120}"
ACME_SERVER="${ACME_SERVER:-letsencrypt}"

if [ -z "$DUCKDNS_FULL_DOMAIN" ] && [ -n "$DUCKDNS_DOMAIN" ]; then
  DUCKDNS_FULL_DOMAIN="${DUCKDNS_DOMAIN}.duckdns.org"
fi

if [ -z "$DUCKDNS_DOMAIN" ]; then
  err "DUCKDNS_DOMAIN manquant. Exemple : DUCKDNS_DOMAIN=stjo-lpsuite"
  exit 1
fi
if [ -z "$DUCKDNS_FULL_DOMAIN" ]; then
  err "DUCKDNS_FULL_DOMAIN manquant. Exemple : stjo-lpsuite.duckdns.org"
  exit 1
fi
if [ -z "$DUCKDNS_TOKEN" ] || [ "$DUCKDNS_TOKEN" = "CHANGE_ME_NEVER_COMMIT" ]; then
  err "DUCKDNS_TOKEN manquant ou non configuré. Ne pas le commiter dans GitHub."
  exit 1
fi

mkdir -p "$CERT_DIR" "$ACME_HOME"

log "Vérification dépendances..."
if ! command -v curl >/dev/null 2>&1; then
  err "curl absent. Installer : sudo apt install curl -y"
  exit 1
fi
if ! command -v openssl >/dev/null 2>&1; then
  err "openssl absent. Installer : sudo apt install openssl -y"
  exit 1
fi

if ! command -v acme.sh >/dev/null 2>&1 && [ ! -x "$HOME/.acme.sh/acme.sh" ]; then
  log "Installation acme.sh..."
  curl https://get.acme.sh | sh -s email="$TLS_EMAIL"
fi

ACME_BIN="$(command -v acme.sh || true)"
if [ -z "$ACME_BIN" ]; then
  ACME_BIN="$HOME/.acme.sh/acme.sh"
fi
if [ ! -x "$ACME_BIN" ]; then
  err "acme.sh introuvable après installation."
  exit 1
fi

export DuckDNS_Token="$DUCKDNS_TOKEN"

log "Test API DuckDNS TXT..."
DUCK_TEST="$(curl -fsS "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&txt=lp-suite-rc19-test&verbose=true" || true)"
printf '%s\n' "$DUCK_TEST" | grep -q "OK" || {
  err "Réponse DuckDNS inattendue : $DUCK_TEST"
  exit 1
}

log "Génération certificat pour $DUCKDNS_FULL_DOMAIN via DNS-01 DuckDNS..."
"$ACME_BIN" --set-default-ca --server "$ACME_SERVER"
"$ACME_BIN" --issue \
  --dns dns_duckdns \
  -d "$DUCKDNS_FULL_DOMAIN" \
  --dnssleep "$ACME_DNS_SLEEP" \
  --home "$ACME_HOME" \
  --server "$ACME_SERVER"

log "Installation certificat dans $CERT_DIR..."
"$ACME_BIN" --install-cert \
  -d "$DUCKDNS_FULL_DOMAIN" \
  --home "$ACME_HOME" \
  --fullchain-file "$CERT_DIR/fullchain.pem" \
  --key-file "$CERT_DIR/privkey.pem" \
  --reloadcmd "docker compose restart lp-gateway 2>/dev/null || docker compose restart lp-core-proxy 2>/dev/null || docker compose restart suite-proxy 2>/dev/null || docker compose restart nginx 2>/dev/null || true"

chmod 644 "$CERT_DIR/fullchain.pem"
chmod 600 "$CERT_DIR/privkey.pem"

log "Vérification certificat..."
openssl x509 -in "$CERT_DIR/fullchain.pem" -noout -subject -issuer -dates

log "Terminé. Certificat disponible :"
log "  $CERT_DIR/fullchain.pem"
log "  $CERT_DIR/privkey.pem"
log "Relancer la suite si nécessaire : docker compose up -d --force-recreate"
