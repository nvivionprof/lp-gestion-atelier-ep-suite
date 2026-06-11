#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
BRANCH="${1:-main}"
if [ ! -d .git ]; then echo "ERREUR : ce dossier n'est pas un dépôt Git." >&2; exit 1; fi
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "ERREUR : modifications locales détectées sur des fichiers suivis par Git." >&2
  git status --short
  exit 1
fi
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
./install.sh --mode update
