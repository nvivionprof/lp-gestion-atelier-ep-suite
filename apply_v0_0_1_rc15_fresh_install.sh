#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${1:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$SCRIPT_DIR/rc15_payload"

if [ ! -d "$PAYLOAD" ]; then
  echo "ERREUR : dossier payload introuvable : $PAYLOAD" >&2
  exit 1
fi

mkdir -p "$ROOT"
cd "$ROOT"

stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir=".patch-backups/rc15-fresh-install-$stamp"
mkdir -p "$backup_dir"
for f in install.sh update.sh upgrade.sh VERSION VERSION.txt CHECKSUMS.sha256; do
  if [ -e "$f" ]; then cp -a "$f" "$backup_dir/$f"; fi
done
for d in scripts docs; do
  if [ -d "$d" ]; then mkdir -p "$backup_dir/$d"; cp -a "$d"/. "$backup_dir/$d"/; fi
done
if [ -f lp-core-app/core/management/commands/seed_core.py ]; then
  mkdir -p "$backup_dir/lp-core-app/core/management/commands"
  cp -a lp-core-app/core/management/commands/seed_core.py "$backup_dir/lp-core-app/core/management/commands/seed_core.py"
fi

cp -a "$PAYLOAD"/. "$ROOT"/

chmod +x install.sh update.sh upgrade.sh 2>/dev/null || true
find scripts -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
find scripts/postgres -type f -exec chmod +x {} \; 2>/dev/null || true
chmod +x scripts/rc15_patch_seed_core.py 2>/dev/null || true

python3 scripts/rc15_patch_seed_core.py || true

if [ -f CHECKSUMS.sha256 ]; then
  (sha256sum -c CHECKSUMS.sha256 >/dev/null 2>&1 && echo "CHECKSUMS OK") || echo "CHECKSUMS : certains fichiers applicatifs peuvent différer localement, vérifier si besoin."
fi

echo "RC15 fresh install installée dans : $ROOT"
echo "Sauvegarde des anciens fichiers : $backup_dir"
echo "Commandes disponibles :"
echo "  bash install.sh                 # installation assistée fresh/conserve"
echo "  bash scripts/reset_fresh_install.sh # suppression complète de cette instance"
echo "  bash update.sh                  # mise à jour rapide Git"
echo "  bash upgrade.sh                 # upgrade classique avec compatibilité"
echo "  bash scripts/load_demo_data.sh  # chargement base démo"
