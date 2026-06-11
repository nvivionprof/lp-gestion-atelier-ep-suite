#!/usr/bin/env bash
set -Eeuo pipefail
REPO="${LP_SUITE_GITHUB_REPO:-nvivionprof/lp-gestion-atelier-ep-suite}"
VERSION="${1:-${LP_SUITE_VERSION:-latest}}"
APP_DIR="${LP_SUITE_DIR:-/home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite}"
ASSET_PREFIX="lp-gestion-atelier-ep-suite"
YES=0
AUTO_RESTORE=0
usage(){
  cat <<'USAGE'
Usage : bash github_bootstrap.sh [V0.0.1|latest] [--dir /chemin/app] [-y] [--auto-restore]

Télécharge une release GitHub avec wget, vérifie le .sha256, extrait l'archive,
puis lance l'orchestrateur install/update/upgrade.

Exemple :
  wget -O /tmp/lp-suite-bootstrap.sh https://raw.githubusercontent.com/nvivionprof/lp-gestion-atelier-ep-suite/main/scripts/github_bootstrap.sh
  bash /tmp/lp-suite-bootstrap.sh V0.0.1 --dir /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
USAGE
}
while [ $# -gt 0 ]; do
  case "$1" in
    --dir) APP_DIR="$2"; shift 2;;
    --repo) REPO="$2"; shift 2;;
    --auto-restore) AUTO_RESTORE=1; shift;;
    -y|--yes) YES=1; shift;;
    -h|--help) usage; exit 0;;
    V*|v*|latest) VERSION="$1"; shift;;
    *) echo "Option inconnue : $1" >&2; usage >&2; exit 1;;
  esac
done
need(){ command -v "$1" >/dev/null 2>&1 || { echo "ERREUR : commande absente : $1" >&2; exit 1; }; }
need wget; need unzip; need sha256sum; need tar
mkdir -p "$(dirname "$APP_DIR")"
TMP="$(mktemp -d)"
cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT
if [ "$VERSION" = "latest" ]; then
  BASE="https://github.com/$REPO/releases/latest/download"
  ZIP="$ASSET_PREFIX-latest.zip"
else
  BASE="https://github.com/$REPO/releases/download/$VERSION"
  ZIP="$ASSET_PREFIX-$VERSION.zip"
fi
cd "$TMP"
echo "Téléchargement : $BASE/$ZIP"
wget -O "$ZIP" "$BASE/$ZIP"
wget -O "$ZIP.sha256" "$BASE/$ZIP.sha256"
sha256sum -c "$ZIP.sha256"
unzip -q "$ZIP" -d extracted
SRC="$(find extracted -mindepth 1 -maxdepth 2 -name VERSION -print -quit | xargs -r dirname)"
[ -n "$SRC" ] || { echo "ERREUR : archive invalide, fichier VERSION absent." >&2; exit 1; }
mkdir -p "$APP_DIR"
# Préserver les données locales si dossier déjà existant.
if [ -f "$APP_DIR/.suite-version" ] || [ -f "$APP_DIR/.env" ]; then
  echo "Installation existante détectée : copie du nouveau code en préservant données locales."
  (cd "$SRC" && tar --exclude='./.env' --exclude='./backups' --exclude='./ssl' --exclude='./postgres-db/data' --exclude='./*-db/data' -cf - .) | (cd "$APP_DIR" && tar -xf -)
else
  echo "Nouvelle installation : copie complète du socle applicatif."
  (cd "$SRC" && tar --exclude='./.env' -cf - .) | (cd "$APP_DIR" && tar -xf -)
fi
cd "$APP_DIR"
chmod +x install.sh start.sh stop.sh upgrade.sh scripts/*.sh scripts/postgres/*.sh 2>/dev/null || true
ARGS=(auto)
[ "$YES" = "1" ] && ARGS+=(--yes)
[ "$AUTO_RESTORE" = "1" ] && ARGS+=(--auto-restore)
./scripts/release_apply.sh "${ARGS[@]}"
