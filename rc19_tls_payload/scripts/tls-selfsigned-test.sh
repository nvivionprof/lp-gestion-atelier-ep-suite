#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${ROOT_DIR:-$(pwd)}"
CERT_DIR="${TLS_HOST_CERT_DIR:-$ROOT_DIR/ssl}"
DOMAIN="${EXTERNAL_PUBLIC_DOMAIN:-lp-suite.local}"
IP_LOCAL="${LP_LOCAL_IP:-192.168.101.19}"

mkdir -p "$CERT_DIR"
openssl req -x509 -nodes -days 365 \
  -newkey rsa:4096 \
  -keyout "$CERT_DIR/privkey.pem" \
  -out "$CERT_DIR/fullchain.pem" \
  -subj "/CN=${DOMAIN}" \
  -addext "subjectAltName=DNS:${DOMAIN},DNS:lp-suite.local,IP:${IP_LOCAL}"
chmod 644 "$CERT_DIR/fullchain.pem"
chmod 600 "$CERT_DIR/privkey.pem"
openssl x509 -in "$CERT_DIR/fullchain.pem" -noout -subject -issuer -dates
printf '\nCertificat auto-signé généré pour test uniquement.\n'
