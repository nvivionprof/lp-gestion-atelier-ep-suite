#!/usr/bin/env bash
set -e

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec gunicorn pfmp_project.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
