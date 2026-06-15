#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

require_project_files
wait_postgres 180

svc="${1:-all}"

repair_core(){
  log "Réparation état migrations LP Core, si nécessaire"
  dc exec -T postgres sh -lc '
psql -U "$POSTGRES_USER" -d lp_core -v ON_ERROR_STOP=1 <<SQL
INSERT INTO django_migrations(app, name, applied)
SELECT '\''core'\'', '\''0005_rgpd_profiles_rights'\'', NOW()
WHERE EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = '\''public'\''
      AND table_name = '\''core_coreuser'\''
      AND column_name = '\''personal_email'\''
)
AND NOT EXISTS (
    SELECT 1
    FROM django_migrations
    WHERE app = '\''core'\''
      AND name = '\''0005_rgpd_profiles_rights'\''
);
SQL
'
}

repair_pfmp(){
  log "Réparation état/schéma migrations PFMP RC16/RC17, si nécessaire"
  # La commande est tolérante : elle ajoute seulement les objets manquants et marque 0002 si cohérent.
  if run_manage pfmp-app repair_pfmp_rc16_schema; then
    return 0
  fi
  warn "repair_pfmp_rc16_schema indisponible ou en erreur ; poursuite sans blocage."
  return 0
}

case "$svc" in
  all)
    repair_core || true
    repair_pfmp || true
    ;;
  lp-core-app|core|lp-core)
    repair_core || true
    ;;
  pfmp-app|pfmp)
    repair_pfmp || true
    ;;
  *)
    warn "Aucune réparation connue pour le service : $svc"
    ;;
esac

log "Réparation d'état migrations terminée."
