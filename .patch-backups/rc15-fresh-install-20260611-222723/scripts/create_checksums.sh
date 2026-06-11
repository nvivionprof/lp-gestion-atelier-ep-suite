#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
OUT="CHECKSUMS.sha256"
TMP="${OUT}.tmp"
find . -type f \
  ! -path './.git/*' \
  ! -name 'CHECKSUMS.sha256' \
  ! -name 'CHECKSUMS.sha256.tmp' \
  ! -name '*.pyc' \
  ! -path './__pycache__/*' \
  ! -path './*/__pycache__/*' \
  ! -path './postgres-db/data/*' \
  ! -path './backups/*' \
  ! -path './logs/*' \
  ! -path './updates/incoming/*' \
  ! -path './updates/logs/*' \
  ! -path './ssl/acme/*' \
  ! -path './lp-core-db/data/*' \
  ! -path './toolmag-db/data/*' \
  ! -path './safety-db/data/*' \
  ! -path './pedashop-db/data/*' \
  ! -path './system-manager-db/data/*' \
  ! -path './tpmanager-db/data/*' \
  ! -path './pfmp-db/data/*' \
  ! -name '.env' \
  -print0 | sort -z | xargs -0 sha256sum > "$TMP"
mv "$TMP" "$OUT"
echo "${OUT} généré."
