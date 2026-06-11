#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

STRICT=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
  esac
done

require_docker_compose
require_project_files
check_disk_space 1024
check_compose_services

ver="$(current_version)"
log "Version détectée : $ver"
case "$ver" in
  V0.0.1-RC*|V0.0.1|UNKNOWN)
    log "Compatibilité version : acceptable pour RC14."
    ;;
  *)
    if [ "$STRICT" = "1" ] && [ "${LP_SUITE_ALLOW_UNSUPPORTED:-0}" != "1" ]; then
      fatal "Version non reconnue pour upgrade automatique : $ver. Pose LP_SUITE_ALLOW_UNSUPPORTED=1 pour forcer."
    else
      warn "Version non reconnue : $ver. Continuer avec prudence."
    fi
    ;;
esac

if dc ps postgres 2>/dev/null | grep -q postgres; then
  if dc exec -T postgres sh -lc 'pg_isready -U "$POSTGRES_USER" -d postgres >/dev/null 2>&1'; then
    log "PostgreSQL accessible."
  else
    warn "PostgreSQL présent mais pas encore accessible."
  fi
else
  warn "PostgreSQL non démarré ; normal avant une installation neuve."
fi

log "Préflight compatibilité terminé."
