#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${ROOT_DIR:-$(pwd)}"
CERT_DIR="${TLS_HOST_CERT_DIR:-$ROOT_DIR/ssl}"
CERT="$CERT_DIR/fullchain.pem"
KEY="$CERT_DIR/privkey.pem"

if [ ! -f "$CERT" ]; then echo "ERREUR: certificat absent : $CERT"; exit 1; fi
if [ ! -f "$KEY" ]; then echo "ERREUR: clé privée absente : $KEY"; exit 1; fi

echo "=== Certificat ==="
openssl x509 -in "$CERT" -noout -subject -issuer -dates -serial

echo
echo "=== Correspondance certificat / clé ==="
CERT_MD5="$(openssl x509 -noout -modulus -in "$CERT" | openssl md5 | awk '{print $2}')"
KEY_MD5="$(openssl rsa -noout -modulus -in "$KEY" 2>/dev/null | openssl md5 | awk '{print $2}')"
echo "cert=$CERT_MD5"
echo "key =$KEY_MD5"
if [ "$CERT_MD5" = "$KEY_MD5" ]; then
  echo "OK: certificat et clé correspondent."
else
  echo "KO: certificat et clé ne correspondent pas."
  exit 2
fi
