#!/usr/bin/env bash
set -euo pipefail
MODE="replace"
if [ "${1:-}" = "--additive" ]; then MODE="additive"; shift; fi
MODULE="${1:-}"
SQL_FILE="${2:-}"
if [ -z "$MODULE" ] || [ -z "$SQL_FILE" ]; then
  echo "Usage: $0 [--additive] <lp-core|toolmag|safety|pedashop|system-manager|tpmanager> <fichier.sql>" >&2
  exit 1
fi
if [ ! -f "$SQL_FILE" ]; then echo "Fichier introuvable: $SQL_FILE" >&2; exit 1; fi
case "$MODULE" in
  lp-core) SERVICE="lp-core-app";;
  toolmag) SERVICE="toolmag-app";;
  safety) SERVICE="safety-app";;
  pedashop) SERVICE="pedashop-app";;
  system-manager) SERVICE="system-manager-app";;
  tpmanager) SERVICE="tpmanager-app";;
  *) echo "Module inconnu: $MODULE" >&2; exit 1;;
esac
echo "Import SQL $MODE vers $MODULE — sauvegarde préalable..."
docker compose exec -T "$SERVICE" python -c "import os, shutil, pathlib, datetime; p=pathlib.Path(os.environ['DB_NAME']); b=p.parent/'sql_import_backups'; b.mkdir(parents=True, exist_ok=True); print('DB',p); shutil.copy2(p, b/(p.stem+'-preimport-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+p.suffix)) if p.exists() else None"
if [ "$MODE" = "replace" ]; then
  docker compose stop "$SERVICE"
  cat "$SQL_FILE" | docker compose run --rm -T --entrypoint python "$SERVICE" -c "import os, sys, sqlite3, pathlib, tempfile; sql=sys.stdin.read(); p=pathlib.Path(os.environ['DB_NAME']); p.parent.mkdir(parents=True, exist_ok=True); fd,tmp=tempfile.mkstemp(prefix='import-',suffix='.sqlite3',dir=str(p.parent)); os.close(fd); c=sqlite3.connect(tmp); c.executescript(sql); c.commit(); c.close(); os.replace(tmp,p); print('Base remplacée',p)"
  docker compose up -d "$SERVICE"
  docker compose exec -T "$SERVICE" python manage.py migrate --noinput
else
  cat "$SQL_FILE" | docker compose exec -T "$SERVICE" python -c "import os, sys, sqlite3; sql=sys.stdin.read(); c=sqlite3.connect(os.environ['DB_NAME']); c.executescript(sql); c.commit(); c.close(); print('Script SQL additif exécuté')"
fi
