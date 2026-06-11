#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${1:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$SCRIPT_DIR/rc14_maintenance_payload"

if [ ! -d "$PAYLOAD" ]; then
  echo "ERREUR : dossier payload introuvable : $PAYLOAD" >&2
  exit 1
fi

mkdir -p "$ROOT"
cd "$ROOT"

stamp="$(date +%Y%m%d-%H%M%S)"
mkdir -p ".patch-backups/rc14-maintenance-$stamp"
for f in install.sh update.sh upgrade.sh VERSION VERSION.txt CHECKSUMS.sha256; do
  if [ -e "$f" ]; then cp -a "$f" ".patch-backups/rc14-maintenance-$stamp/$f"; fi
done
for d in scripts docs; do
  if [ -d "$d" ]; then mkdir -p ".patch-backups/rc14-maintenance-$stamp/$d"; fi
done

cp -a "$PAYLOAD"/. "$ROOT"/

chmod +x install.sh update.sh upgrade.sh 2>/dev/null || true
find scripts -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
find scripts/postgres -type f -exec chmod +x {} \; 2>/dev/null || true

echo "RC14 maintenance installée dans : $ROOT"
echo "Sauvegarde des anciens fichiers : .patch-backups/rc14-maintenance-$stamp"
echo "Commandes disponibles :"
echo "  bash install.sh       # installation assistée"
echo "  bash update.sh        # mise à jour rapide Git"
echo "  bash upgrade.sh       # upgrade classique avec compatibilité"
echo "  bash scripts/load_demo_data.sh # chargement base démo"
