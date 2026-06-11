#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
QUIET=0
if [ "${1:-}" = "--quiet" ]; then QUIET=1; fi
if [ ! -f CHECKSUMS.sha256 ]; then
  echo "ERREUR : CHECKSUMS.sha256 absent." >&2
  exit 1
fi
if ! command -v sha256sum >/dev/null 2>&1; then
  echo "ERREUR : sha256sum est indisponible." >&2
  exit 1
fi
if [ "$QUIET" = "0" ]; then
  echo "Vérification des fichiers de l'archive avec CHECKSUMS.sha256..."
fi
sha256sum -c CHECKSUMS.sha256
if [ "$QUIET" = "0" ]; then
  echo "Vérification OK."
fi
