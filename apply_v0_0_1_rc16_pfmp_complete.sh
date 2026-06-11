#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(pwd)"
PAYLOAD_DIR="$(cd "$(dirname "$0")" && pwd)/rc16_payload"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$ROOT/.rc16-backup-$STAMP"

if [[ ! -f "$ROOT/docker-compose.yml" || ! -d "$ROOT/pfmp-app/pfmp_manager" ]]; then
  echo "ERREUR : lance ce script à la racine du dépôt LP Suite (dossier contenant docker-compose.yml)." >&2
  exit 1
fi
if [[ ! -d "$PAYLOAD_DIR" ]]; then
  echo "ERREUR : payload RC16 introuvable : $PAYLOAD_DIR" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
echo "Sauvegarde locale des fichiers remplacés : $BACKUP_DIR"
for path in \
  pfmp-app/pfmp_manager/models.py \
  pfmp-app/pfmp_manager/forms.py \
  pfmp-app/pfmp_manager/views.py \
  pfmp-app/pfmp_manager/urls.py \
  pfmp-app/pfmp_manager/admin.py \
  pfmp-app/pfmp_manager/templates/pfmp_manager/base.html \
  pfmp-app/pfmp_manager/templates/pfmp_manager/company_list.html \
  pfmp-app/pfmp_manager/templates/pfmp_manager/company_detail.html \
  pfmp-app/pfmp_manager/templates/pfmp_manager/map.html; do
  if [[ -e "$ROOT/$path" ]]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$path")"
    cp -a "$ROOT/$path" "$BACKUP_DIR/$path"
  fi
done

cp -a "$PAYLOAD_DIR/." "$ROOT/"
chmod +x "$ROOT/scripts/pfmp_rc16_import_companies.sh" 2>/dev/null || true

cat <<'EOF'

RC16 PFMP Manager complet appliqué.

Étapes recommandées :

  bash scripts/migrate_all.sh
  bash scripts/collectstatic_all.sh
  docker compose --env-file .env restart

Puis import de simulation :

  bash scripts/pfmp_rc16_import_companies.sh simulation code_entreprise

Puis import réel :

  bash scripts/pfmp_rc16_import_companies.sh upsert code_entreprise

EOF
