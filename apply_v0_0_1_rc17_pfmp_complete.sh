#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$ROOT_DIR/rc17_payload"

if [ ! -d "$PAYLOAD" ]; then
  echo "ERREUR : dossier rc17_payload introuvable." >&2
  exit 1
fi
if [ ! -f "docker-compose.yml" ] || [ ! -d "pfmp-app/pfmp_manager" ]; then
  echo "ERREUR : lance ce script depuis la racine du dépôt LP Gestion Atelier EP Suite." >&2
  exit 1
fi

echo "Application RC17 PFMP Manager : édition web, prochaines actions et bilans par période"
cp -a "$PAYLOAD"/. .

# Nettoyage défensif des caches Python éventuellement présents.
find pfmp-app/pfmp_manager -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find pfmp-app/pfmp_manager -type f -name '*.pyc' -delete 2>/dev/null || true

# Vérification syntaxique locale.
python3 -m py_compile \
  pfmp-app/pfmp_manager/models.py \
  pfmp-app/pfmp_manager/forms.py \
  pfmp-app/pfmp_manager/views.py \
  pfmp-app/pfmp_manager/urls.py \
  pfmp-app/pfmp_manager/admin.py \
  pfmp-app/pfmp_manager/management/commands/import_pfmp_companies_xlsx.py \
  pfmp-app/pfmp_manager/migrations/0002_rc16_pfmp_complete.py

echo "RC17 appliquée. Étapes serveur conseillées :"
echo "  bash upgrade.sh --branch=rc"
echo "  bash scripts/migrate_all.sh"
echo "  bash scripts/collectstatic_all.sh"
echo "  docker compose --env-file .env restart"
