#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
ZIP_PATH=""
FULL_REBUILD=0
CLEAN_BUILD=0
SKIP_SEED=0
YES=0
usage(){
  cat <<'EOF'
Usage : ./upgrade.sh [options] /chemin/nouvelle_version.zip
Options :
  --full-rebuild    Reconstruit les images Docker sans cache.
  --clean-build     Nettoie le cache Docker/BuildKit, volumes conservés.
  --skip-seed       Désactive les seeds après migrations.
  -y, --yes         Confirmations non critiques automatiques.
EOF
}
while [ $# -gt 0 ]; do
  case "$1" in
    --full-rebuild) FULL_REBUILD=1; shift;;
    --clean-build) CLEAN_BUILD=1; FULL_REBUILD=1; shift;;
    --skip-seed) SKIP_SEED=1; shift;;
    -y|--yes) YES=1; shift;;
    -h|--help) usage; exit 0;;
    *) ZIP_PATH="$1"; shift;;
  esac
done
[ -n "$ZIP_PATH" ] && [ -f "$ZIP_PATH" ] || { usage >&2; exit 1; }
command -v unzip >/dev/null 2>&1 || { echo "unzip est nécessaire." >&2; exit 1; }
command -v rsync >/dev/null 2>&1 || { echo "rsync est nécessaire." >&2; exit 1; }

if [ -x scripts/full_backup.sh ]; then scripts/full_backup.sh pre-upgrade; fi
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
unzip -q "$ZIP_PATH" -d "$TMP_DIR"
SRC="$TMP_DIR/lp-gestion-atelier-ep-suite"
[ -d "$SRC" ] || SRC="$TMP_DIR"
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude '.suite-version' \
  --exclude 'postgres-db/data/' \
  --exclude 'lp-core-db/data/' \
  --exclude 'toolmag-db/data/' \
  --exclude 'safety-db/data/' \
  --exclude 'pedashop-db/data/' \
  --exclude 'system-manager-db/data/' \
  --exclude 'tpmanager-db/data/' \
  --exclude 'pfmp-db/data/' \
  --exclude 'backups/' \
  --exclude 'logs/' \
  --exclude 'updates/incoming/' \
  --exclude 'updates/logs/' \
  "$SRC/" "$PROJECT_DIR/"
chmod +x install.sh upgrade.sh start.sh stop.sh scripts/*.sh scripts/postgres/*.sh 2>/dev/null || true
ARGS=(--mode upgrade)
[ "$FULL_REBUILD" = "1" ] && ARGS+=(--full-rebuild)
[ "$CLEAN_BUILD" = "1" ] && ARGS+=(--clean-build)
[ "$SKIP_SEED" = "1" ] && ARGS+=(--skip-seed)
[ "$YES" = "1" ] && ARGS+=(--yes)
./install.sh "${ARGS[@]}"
