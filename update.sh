#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

REPO="${LP_SUITE_REPO:-nvivionprof/lp-gestion-atelier-ep-suite}"
CHANNEL="stable"
ZIP=""
REPAIR_NO_CACHE=0
NO_BACKUP=0

usage() {
  cat <<'EOF'
Usage:
  ./update.sh [--channel stable|rc] [--zip /home/archive.zip] [--repair-no-cache] [--no-backup]

Update rapide par défaut :
  - sauvegarde complète obligatoire ;
  - remplacement du code uniquement ;
  - conservation .env, bases, médias, sauvegardes, SSL ;
  - docker compose up -d --build ;
  - migrations ;
  - contrôles simples.

Exemples :
  ./update.sh --channel stable
  ./update.sh --channel rc
  ./update.sh --zip /home/lp-suite.zip
  ./update.sh --channel rc --repair-no-cache
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --channel) CHANNEL="${2:?channel manquant}"; shift 2 ;;
    --zip) ZIP="${2:?zip manquant}"; shift 2 ;;
    --repair-no-cache) REPAIR_NO_CACHE=1; shift ;;
    --no-backup) NO_BACKUP=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argument inconnu: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ ! -f .env ]]; then
  echo "ERREUR: .env introuvable. Ce script doit être lancé dans une installation existante." >&2
  exit 2
fi

mkdir -p /tmp/lp-suite-update
WORK="$(mktemp -d /tmp/lp-suite-update/update.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

if [[ -z "$ZIP" ]]; then
  ZIP="$WORK/lp-suite-${CHANNEL}.zip"
  URL="https://github.com/${REPO}/archive/refs/heads/${CHANNEL}.zip"
  echo "Téléchargement $URL"
  curl -fL "$URL" -o "$ZIP"
fi

unzip -t "$ZIP" >/dev/null
unzip -q "$ZIP" -d "$WORK/src"
SRC="$(find "$WORK/src" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [[ -z "$SRC" || ! -d "$SRC" ]]; then
  echo "ERREUR: source extraite introuvable." >&2
  exit 2
fi

if [[ -f "$SRC/CHECKSUMS.sha256" ]]; then
  echo "Vérification CHECKSUMS de l'archive..."
  (cd "$SRC" && sha256sum -c CHECKSUMS.sha256 >/dev/null)
fi

if [[ "$NO_BACKUP" != "1" ]]; then
  if [[ -x ./scripts/full_backup.sh ]]; then
    echo "Sauvegarde avant update..."
    ./scripts/full_backup.sh "pre-update-$(date +%Y%m%d-%H%M%S)"
  else
    echo "ERREUR: scripts/full_backup.sh absent ou non exécutable. Utilise --no-backup uniquement en test." >&2
    exit 2
  fi
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "Installation rsync..."
  apt update && apt install -y rsync
fi

echo "Remplacement du code, conservation des données..."
rsync -a --delete \
  --exclude='.env' \
  --exclude='backups/' \
  --exclude='ssl/' \
  --exclude='imports/' \
  --exclude='postgres-db/' \
  --exclude='lp-core-db/' \
  --exclude='toolmag-db/' \
  --exclude='safety-db/' \
  --exclude='pedashop-db/' \
  --exclude='system-manager-db/' \
  --exclude='tpmanager-db/' \
  --exclude='pfmp-db/' \
  "$SRC"/ ./

chmod +x install.sh update.sh scripts/*.sh scripts/postgres/*.sh pfmp-app/docker-entrypoint.sh 2>/dev/null || true

if [[ -f CHECKSUMS.sha256 ]]; then
  echo "Vérification CHECKSUMS après rsync..."
  sha256sum -c CHECKSUMS.sha256 >/dev/null
fi

if [[ "$REPAIR_NO_CACHE" == "1" ]]; then
  echo "Mode réparation : rebuild no-cache. À utiliser seulement si images incohérentes."
  docker compose --env-file .env build --no-cache
  docker compose --env-file .env up -d
else
  echo "Update rapide : rebuild Docker incrémental."
  docker compose --env-file .env up -d --build
fi

if [[ -x ./scripts/migrate_all.sh ]]; then
  ./scripts/migrate_all.sh 2>&1 | tee /tmp/lp-suite-update-migrations.log
fi

docker compose --env-file .env ps

echo "Contrôle rapide routes/titres :"
for url in \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/toolmag/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/safety/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/pedashop/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/system/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/tpmanager/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/pfmp/
do
  echo
  echo "===== $url ====="
  curl -sSI "$url" | grep -Ei 'HTTP/|location:|x-lp-gateway-module' || true
  curl -sSL "$url" | grep -Eoi '<title>[^<]+' | head -n 1 || true
done

echo "Update terminé."
