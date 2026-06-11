#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-/home/user/docker/lp-gestion-atelier-ep-suite}"
PATCH_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -d "$TARGET" || ! -f "$TARGET/docker-compose.yml" ]]; then
  echo "ERREUR: dossier cible invalide: $TARGET" >&2
  exit 1
fi

cd "$TARGET"
echo "[1/6] Sauvegarde applicative avant V0.4.0a..."
mkdir -p backups/pre_upgrade
BACKUP="backups/pre_upgrade/app-before-v0.4.0a-domain-cert-$(date +%Y%m%d-%H%M%S).tar.gz"
tar --exclude='./lp-core-db/data' \
    --exclude='./toolmag-db/data' \
    --exclude='./safety-db/data' \
    --exclude='./pedashop-db/data' \
    --exclude='./system-manager-db/data' \
    --exclude='./tpmanager-db/data' \
    --exclude='./pfmp-db/data' \
    --exclude='./backups' \
    --exclude='./ssl' \
    -czf "$BACKUP" . || true

echo "[2/6] Copie du patch V0.4.0a..."
if command -v rsync >/dev/null 2>&1; then
  rsync -a "$PATCH_ROOT/" "$TARGET/"
else
  echo "rsync introuvable : copie du patch avec tar/cp fallback..."
  (cd "$PATCH_ROOT" && tar -cf - .) | (cd "$TARGET" && tar -xf -)
fi
chmod +x scripts/*.sh || true
chmod +x suite-admin-agent/agent.py || true

echo "[3/6] Reconstruction de LP Core, suite-admin-agent et passerelle..."
docker compose up -d --build lp-core-app suite-admin-agent lp-gateway

echo "[4/6] Migrations LP Core..."
docker compose run --rm --entrypoint python lp-core-app manage.py check --traceback
docker compose run --rm --entrypoint python lp-core-app manage.py migrate

echo "[5/6] Collectstatic LP Core..."
docker compose exec lp-core-app python manage.py collectstatic --noinput || true

echo "[6/6] Redémarrage ciblé..."
docker compose restart lp-core-app suite-admin-agent lp-gateway

echo ""
echo "V0.4.0a appliquée."
echo "Ouvre LP Core > URLs / HTTPS : http://localhost:9000/parametres-publics/"
echo "1) Renseigne le domaine DuckDNS, protocole HTTPS, token DuckDNS et email."
echo "2) Enregistre."
echo "3) Clique 'Appliquer les URLs dans .env'."
echo "4) Clique 'Générer le certificat'."
echo "5) Redémarre la suite si nécessaire : docker compose up -d --build"
