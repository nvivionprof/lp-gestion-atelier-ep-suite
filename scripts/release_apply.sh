#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
TARGET_VERSION="$(cat VERSION 2>/dev/null | head -1 | tr -d '\r\n')"
CURRENT_VERSION="unknown"
[ -f .suite-version ] && CURRENT_VERSION="$(cat .suite-version | head -1 | tr -d '\r\n')"
MODE="${1:-auto}"
AUTO_RESTORE=0
YES=0
usage(){
  cat <<'USAGE'
Usage : ./scripts/release_apply.sh [auto|install|update|upgrade] [--auto-restore] [-y]

Orchestre une installation/mise à jour sécurisée depuis le code présent dans le dossier.
- détecte la version installée (.suite-version)
- classe le passage de version
- sauvegarde avant update/upgrade
- lance install.sh avec le mode adapté
- en cas d'échec, indique la commande de restauration de la dernière sauvegarde
USAGE
}
while [ $# -gt 0 ]; do
  case "$1" in
    auto|install|update|upgrade|major_release) MODE="$1"; shift;;
    --auto-restore) AUTO_RESTORE=1; shift;;
    -y|--yes) YES=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Option inconnue : $1" >&2; usage >&2; exit 1;;
  esac
done
if [ "$MODE" = "auto" ]; then
  MODE="$(python3 scripts/version_manager.py mode "$CURRENT_VERSION" "$TARGET_VERSION")"
fi
if [ "$MODE" = "noop" ]; then
  echo "Aucune mise à jour à appliquer : $CURRENT_VERSION -> $TARGET_VERSION."
  exit 0
fi
if [ "$MODE" = "major_release" ]; then MODE="upgrade"; fi
case "$MODE" in install|update|upgrade) ;; *) echo "Mode calculé invalide : $MODE" >&2; exit 1;; esac

echo "Version installée : $CURRENT_VERSION"
echo "Version cible     : $TARGET_VERSION"
echo "Mode retenu       : $MODE"
python3 scripts/version_manager.py check "$MODE" "$CURRENT_VERSION" "$TARGET_VERSION"
if [ "$MODE" != "install" ]; then
  echo "Sauvegarde de sécurité avant $MODE..."
  ./scripts/full_backup.sh pre-upgrade
fi
set +e
if [ "$YES" = "1" ]; then
  ./install.sh --mode "$MODE" -y
else
  ./install.sh --mode "$MODE"
fi
rc=$?
set -e
if [ "$rc" != "0" ]; then
  echo "ERREUR : installation/mise à jour échouée avec code $rc." >&2
  echo "Commande de restauration immédiate :" >&2
  echo "  cd $(pwd) && ./scripts/restore_last_backup.sh --yes" >&2
  if [ "$AUTO_RESTORE" = "1" ]; then
    echo "Auto-restauration demandée : restauration de la dernière sauvegarde..." >&2
    ./scripts/restore_last_backup.sh --yes || true
  fi
  exit "$rc"
fi
printf '%s\n' "$TARGET_VERSION" > .suite-version
echo "Opération terminée : $CURRENT_VERSION -> $TARGET_VERSION ($MODE)."
