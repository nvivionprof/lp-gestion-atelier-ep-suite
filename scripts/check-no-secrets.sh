#!/usr/bin/env bash
set -euo pipefail

printf "Contrôle basique des secrets...\n"

if git grep -nE "(SECRET_KEY|PASSWORD|TOKEN|PRIVATE KEY|BEGIN RSA|BEGIN OPENSSH)" -- . ':!.env.example' ':!scripts/check-no-secrets.sh'; then
  printf "\nAttention : motifs sensibles trouvés. Vérifier avant commit.\n"
  exit 1
fi

printf "Aucun motif sensible évident trouvé.\n"
