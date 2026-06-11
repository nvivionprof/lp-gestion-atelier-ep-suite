#!/usr/bin/env bash
set -euo pipefail
MODULE="${1:-}"
OUT="${2:-}"
if [ -z "$MODULE" ] || [ -z "$OUT" ]; then
  echo "Usage: $0 <lp-core|toolmag|safety|pedashop|system-manager|tpmanager> <sortie.sql>" >&2
  exit 1
fi
case "$MODULE" in
  lp-core) SERVICE="lp-core-app";;
  toolmag) SERVICE="toolmag-app";;
  safety) SERVICE="safety-app";;
  pedashop) SERVICE="pedashop-app";;
  system-manager) SERVICE="system-manager-app";;
  tpmanager) SERVICE="tpmanager-app";;
  *) echo "Module inconnu: $MODULE" >&2; exit 1;;
esac
mkdir -p "$(dirname "$OUT")"
docker compose exec -T "$SERVICE" python -c "import sqlite3, os; p=os.environ.get('DB_NAME'); c=sqlite3.connect('file:'+p+'?mode=ro', uri=True); print('PRAGMA foreign_keys=OFF;'); print('BEGIN TRANSACTION;'); [print(x) for x in c.iterdump() if x not in ('BEGIN TRANSACTION;','COMMIT;')]; print('COMMIT;'); print('PRAGMA foreign_keys=ON;'); c.close()" > "$OUT"
echo "Export SQL créé : $OUT"
