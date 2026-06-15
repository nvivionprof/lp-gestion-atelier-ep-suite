#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-missing}"
LIMIT="${2:-}"
CONTACTS="${3:-no}"
REPORT_DIR="./pfmp-db/data/reports"
REPORT_FILE="$REPORT_DIR/geocodage-pfmp-$(date +%Y%m%d-%H%M).csv"
mkdir -p "$REPORT_DIR"

ARGS=()
case "$MODE" in
  missing|missing-only|a_geocoder)
    ARGS+=(--missing-only)
    ;;
  retry|retry-failed|echecs)
    ARGS+=(--retry-failed)
    ;;
  force|all|tout)
    ARGS+=(--force)
    ;;
  dry-run|simulation)
    ARGS+=(--missing-only --dry-run)
    ;;
  *)
    echo "Mode inconnu : $MODE" >&2
    echo "Modes : missing | retry | force | dry-run" >&2
    exit 2
    ;;
esac

if [ -n "$LIMIT" ]; then
  ARGS+=(--limit "$LIMIT")
fi

if [[ "$CONTACTS" =~ ^(yes|oui|true|1|contacts)$ ]]; then
  ARGS+=(--include-contacts)
fi

ARGS+=(--report "/data/pfmp/reports/$(basename "$REPORT_FILE")")

docker compose --env-file .env exec -T pfmp-app python manage.py geocode_pfmp_companies "${ARGS[@]}"

echo "Rapport conteneur : /data/pfmp/reports/$(basename "$REPORT_FILE")"
echo "Rapport hôte      : $REPORT_FILE"
