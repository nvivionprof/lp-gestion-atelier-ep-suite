#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Migrations Django PFMP"
  python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  echo "Collecte des fichiers statiques PFMP"
  python manage.py collectstatic --noinput
fi

GUNICORN_ARGS="--bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT:-120}"

echo "Démarrage HTTP interne PFMP"
exec gunicorn pfmp_project.wsgi:application $GUNICORN_ARGS
