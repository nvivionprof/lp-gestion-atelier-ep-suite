#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
YES=0
LIST=0
DRY=0
usage(){
  cat <<'USAGE'
Usage : ./scripts/restore_last_backup.sh [--yes] [--list] [--dry-run]

Restaure la sauvegarde la plus récente trouvée dans backups/.
Ordre de priorité : pre_upgrade, pre-restore/pre_restore, manual, daily, puis tout backups/.

Commande d'urgence après échec de mise à jour :
  ./scripts/restore_last_backup.sh --yes
USAGE
}
while [ $# -gt 0 ]; do
  case "$1" in
    --yes|-y) YES=1; shift;;
    --list) LIST=1; shift;;
    --dry-run) DRY=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Option inconnue : $1" >&2; usage >&2; exit 1;;
  esac
done
find_backups(){
  for d in backups/pre_upgrade backups/pre-upgrade backups/pre_restore backups/pre-restore backups/manual backups/daily backups; do
    [ -d "$d" ] || continue
    find "$d" -type f \( -name '*.zip' -o -name '*.tar.gz' -o -name '*.tgz' \) -printf '%T@ %p\n' 2>/dev/null || true
  done | sort -rn
}
if [ "$LIST" = "1" ]; then
  find_backups | sed -n '1,20p'
  exit 0
fi
LATEST="$(find_backups | awk 'NR==1{$1=""; sub(/^ /,""); print; exit}')"
if [ -z "$LATEST" ]; then
  echo "ERREUR : aucune sauvegarde trouvée dans backups/." >&2
  exit 1
fi
echo "Dernière sauvegarde détectée : $LATEST"
if [ "$DRY" = "1" ]; then exit 0; fi
if [ "$YES" != "1" ]; then
  echo "Cette action va restaurer les données depuis cette sauvegarde."
  read -rp "Taper RESTAURER pour confirmer : " confirm
  [ "$confirm" = "RESTAURER" ] || { echo "Restauration annulée."; exit 1; }
fi
case "$LATEST" in
  *.zip)
    if unzip -l "$LATEST" | grep -q 'databases/.*\.dump'; then
      echo "Type détecté : sauvegarde base PostgreSQL."
      exec ./scripts/postgres/restore_database_backup.sh "$LATEST" all
    else
      echo "Type détecté : sauvegarde complète ZIP."
      exec ./scripts/restore_full_backup.sh "$LATEST"
    fi
    ;;
  *.tar.gz|*.tgz)
    echo "Type détecté : archive tar. Conversion/restauration non automatisée pour cette archive."
    echo "Extraire manuellement dans un dossier de reprise ou utiliser une sauvegarde ZIP produite par full_backup.sh."
    exit 2
    ;;
  *) echo "Type de sauvegarde non reconnu : $LATEST" >&2; exit 2;;
esac
