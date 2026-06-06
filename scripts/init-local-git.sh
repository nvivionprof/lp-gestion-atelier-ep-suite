#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/nvivionprof/lp-gestion-atelier-ep-suite.git"

git init
git add .
git commit -m "Initialisation du dépôt LP Gestion Atelier EP Suite"
git branch -M main
git remote add origin "$REPO_URL"
git push -u origin main
