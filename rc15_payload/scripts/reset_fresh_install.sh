#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source scripts/lp_suite_common.sh

echo "ATTENTION : suppression complète des instances LP Suite de ce dossier."
echo "Sont supprimés : conteneurs, volumes Compose, bases PostgreSQL locales, médias/statics locaux."
echo "Aucune sauvegarde n'est faite par ce script."
read -r -p "Confirmer la suppression ? écrire SUPPRIMER : " ok
[ "$ok" = "SUPPRIMER" ] || fatal "Suppression annulée."

fresh_reset_installation
log "Reset fresh terminé. Tu peux relancer : bash install.sh"
