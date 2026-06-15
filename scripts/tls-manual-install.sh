#!/usr/bin/env bash
set -Eeuo pipefail

# Installe un certificat fourni par le lycée / la collectivité.
# Usage :
#   ./scripts/tls-manual-install.sh /chemin/fullchain.pem /chemin/privkey.pem

ROOT_DIR="${ROOT_DIR:-$(pwd)}"
CERT_DIR="${TLS_HOST_CERT_DIR:-$ROOT_DIR/ssl}"
SRC_CERT="${1:-}"
SRC_KEY="${2:-}"

log(){ printf '\033[1;34m[LP-TLS]\033[0m %s\n' "$*"; }
err(){ printf '\033[1;31m[LP-TLS][ERREUR]\033[0m %s\n' "$*" >&2; }

if [ -z "$SRC_CERT" ] || [ -z "$SRC_KEY" ]; then
  err "Usage : $0 /chemin/fullchain.pem /chemin/privkey.pem"
  exit 1
fi
if [ ! -f "$SRC_CERT" ]; then err "Certificat introuvable : $SRC_CERT"; exit 1; fi
if [ ! -f "$SRC_KEY" ]; then err "Clé privée introuvable : $SRC_KEY"; exit 1; fi

log "Vérification format certificat..."
openssl x509 -in "$SRC_CERT" -noout -subject -issuer -dates >/tmp/lp_cert_info.txt
cat /tmp/lp_cert_info.txt

log "Vérification cohérence certificat / clé..."
CERT_MD5="$(openssl x509 -noout -modulus -in "$SRC_CERT" | openssl md5 | awk '{print $2}')"
KEY_MD5="$(openssl rsa -noout -modulus -in "$SRC_KEY" 2>/dev/null | openssl md5 | awk '{print $2}')"
if [ "$CERT_MD5" != "$KEY_MD5" ]; then
  err "Le certificat et la clé privée ne correspondent pas."
  exit 1
fi

mkdir -p "$CERT_DIR"
cp "$SRC_CERT" "$CERT_DIR/fullchain.pem"
cp "$SRC_KEY" "$CERT_DIR/privkey.pem"
chmod 644 "$CERT_DIR/fullchain.pem"
chmod 600 "$CERT_DIR/privkey.pem"

log "Certificat manuel installé dans $CERT_DIR."
log "Relancer le proxy : docker compose restart lp-gateway || docker compose restart lp-core-proxy || docker compose restart suite-proxy || docker compose restart nginx"
