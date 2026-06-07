#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose exec -T toolmag-app python manage.py sync_lp_core_users
