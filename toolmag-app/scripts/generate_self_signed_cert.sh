#!/usr/bin/env sh
set -eu
mkdir -p certs
openssl req -x509 -nodes -newkey rsa:4096 \
  -keyout certs/toolmag.key \
  -out certs/toolmag.crt \
  -days 825 \
  -subj "/CN=toolmag.local" \
  -addext "subjectAltName=DNS:toolmag.local,DNS:outillage.local,DNS:localhost,IP:127.0.0.1"
echo "Certificat généré dans certs/toolmag.crt et certs/toolmag.key"
