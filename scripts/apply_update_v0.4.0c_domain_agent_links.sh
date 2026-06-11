#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-/home/user/docker/lp-gestion-atelier-ep-suite}"
PATCH_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -d "$TARGET" || ! -f "$TARGET/docker-compose.yml" ]]; then
  echo "ERREUR: dossier cible invalide: $TARGET" >&2
  exit 1
fi

cd "$TARGET"
echo "[1/7] Sauvegarde applicative avant V0.4.0c..."
mkdir -p backups/pre_upgrade
BACKUP="backups/pre_upgrade/app-before-v0.4.0c-domain-agent-links-$(date +%Y%m%d-%H%M%S).tar.gz"
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

echo "[2/7] Copie du patch V0.4.0c..."
if command -v rsync >/dev/null 2>&1; then
  rsync -a "$PATCH_ROOT/" "$TARGET/"
else
  echo "rsync introuvable : copie du patch avec tar fallback..."
  (cd "$PATCH_ROOT" && tar -cf - .) | (cd "$TARGET" && tar -xf -)
fi
chmod +x scripts/*.sh || true
chmod +x suite-admin-agent/agent.py || true

echo "[3/7] Reconstruction forcée de suite-admin-agent avec Docker CLI + Docker Compose + lego..."
docker compose build --no-cache suite-admin-agent

echo "[4/7] Reconstruction LP Core, System Manager et passerelle..."
docker compose up -d --build --force-recreate lp-core-app system-manager-app lp-gateway suite-admin-agent

echo "[5/7] Vérification des commandes disponibles dans suite-admin-agent..."
docker compose exec suite-admin-agent sh -lc 'echo -n "docker="; command -v docker; docker --version; echo -n "compose="; docker compose version; echo -n "lego="; command -v lego; lego --version'

echo "[6/7] Vérification Django LP Core + System Manager..."
docker compose run --rm --entrypoint python lp-core-app manage.py check --traceback
docker compose run --rm --entrypoint python system-manager-app manage.py check --traceback

echo "[7/7] Collectstatic + redémarrage ciblé..."
docker compose exec lp-core-app python manage.py collectstatic --noinput || true
docker compose exec system-manager-app python manage.py collectstatic --noinput || true
docker compose restart lp-core-app system-manager-app lp-gateway suite-admin-agent

echo ""
echo "V0.4.0c appliquée."
echo "Étape suivante : LP Core > URLs / HTTPS :"
echo "  1. Enregistrer le domaine DuckDNS."
echo "  2. Cliquer sur Appliquer les URLs dans .env."
echo "  3. Vérifier que les liens affichés utilisent le domaine public."
echo "  4. Générer le certificat."
