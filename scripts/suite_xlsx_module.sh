#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage :
  bash scripts/suite_xlsx_module.sh <module> <template|export|import> <fichier.xlsx> [--dry-run]

Modules acceptés :
  core | lp-core | lp_core
  toolmag
  safety | safety-manager
  pedashop
  system | system-manager | system_manager
  tp | tpmanager | tp-manager
  pfmp | pfmp-manager

Exemples :
  bash scripts/suite_xlsx_module.sh toolmag template ./exports/toolmag_modele.xlsx
  bash scripts/suite_xlsx_module.sh toolmag export ./exports/toolmag.xlsx
  bash scripts/suite_xlsx_module.sh toolmag import ./exports/toolmag.xlsx --dry-run
  bash scripts/suite_xlsx_module.sh toolmag import ./exports/toolmag.xlsx

  bash scripts/suite_xlsx_module.sh pfmp export ./exports/pfmp.xlsx
  bash scripts/suite_xlsx_module.sh core export ./exports/lp_core.xlsx
EOF
}

if [ "$#" -lt 3 ]; then
  usage
  exit 1
fi

MODULE="$1"
ACTION="$2"
FILE="$3"
DRY_RUN="${4:-}"

SERVICE=""
PREFIX=""

case "$MODULE" in
  core|lp-core|lp_core)
    SERVICE="lp-core-app"
    PREFIX="lp_core"
    ;;
  toolmag)
    SERVICE="toolmag-app"
    PREFIX="toolmag"
    ;;
  safety|safety-manager|safety_manager)
    SERVICE="safety-app"
    PREFIX="safety"
    ;;
  pedashop)
    SERVICE="pedashop-app"
    PREFIX="pedashop"
    ;;
  system|system-manager|system_manager)
    SERVICE="system-manager-app"
    PREFIX="system_manager"
    ;;
  tp|tpmanager|tp-manager)
    SERVICE="tpmanager-app"
    PREFIX="tpmanager"
    ;;
  pfmp|pfmp-manager|pfmp_manager)
    SERVICE="pfmp-app"
    PREFIX="pfmp"
    ;;
  *)
    echo "Module inconnu : $MODULE"
    usage
    exit 1
    ;;
esac

if ! docker compose ps --services | grep -qx "$SERVICE"; then
  echo "Service Docker introuvable : $SERVICE"
  echo "Services disponibles :"
  docker compose ps --services
  exit 1
fi

CID="$(docker compose ps -q "$SERVICE")"

if [ -z "$CID" ]; then
  echo "Conteneur non trouvé pour : $SERVICE"
  exit 1
fi

mkdir -p "$(dirname "$FILE")"

case "$ACTION" in
  template|modele|modèle)
    echo "[MODELE] $MODULE -> $FILE"
    docker compose exec "$SERVICE" python manage.py suite_xlsx template --output "/tmp/${PREFIX}_modele.xlsx"
    docker cp "$CID:/tmp/${PREFIX}_modele.xlsx" "$FILE"
    echo "OK : modèle généré -> $FILE"
    ;;

  export)
    echo "[EXPORT] $MODULE -> $FILE"
    docker compose exec "$SERVICE" python manage.py suite_xlsx export --output "/tmp/${PREFIX}.xlsx"
    docker cp "$CID:/tmp/${PREFIX}.xlsx" "$FILE"
    echo "OK : export généré -> $FILE"
    ;;

  import)
    if [ ! -f "$FILE" ]; then
      echo "Fichier XLSX introuvable : $FILE"
      exit 1
    fi

    echo "[IMPORT] $MODULE <- $FILE"
    docker cp "$FILE" "$CID:/tmp/${PREFIX}_import.xlsx"

    if [ "$DRY_RUN" = "--dry-run" ]; then
      echo "[DRY-RUN] Aucun écrit définitif en base"
      docker compose exec "$SERVICE" python manage.py suite_xlsx import --input "/tmp/${PREFIX}_import.xlsx" --dry-run
    else
      docker compose exec "$SERVICE" python manage.py suite_xlsx import --input "/tmp/${PREFIX}_import.xlsx"
    fi

    echo "OK : import terminé pour $MODULE"
    ;;

  *)
    echo "Action inconnue : $ACTION"
    usage
    exit 1
    ;;
esac
