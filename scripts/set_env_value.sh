#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$#" -ne 2 ]; then echo "Usage: $0 CLE VALEUR" >&2; exit 1; fi
ENV_FILE=".env"
[ -f "$ENV_FILE" ] || cp .env.example "$ENV_FILE"
key="$1"; value="$2"
if grep -q "^${key}=" "$ENV_FILE"; then
  sed -i "s#^${key}=.*#${key}=${value}#" "$ENV_FILE"
else
  printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
fi
