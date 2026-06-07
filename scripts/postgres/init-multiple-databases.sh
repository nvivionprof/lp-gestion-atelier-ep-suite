#!/usr/bin/env bash
set -euo pipefail

# Création automatique des bases PostgreSQL nécessaires aux modules Django.
# Variables attendues : POSTGRES_USER, POSTGRES_MULTIPLE_DATABASES.

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
  echo "Création des bases PostgreSQL : ${POSTGRES_MULTIPLE_DATABASES}"
  for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
    db="$(echo "$db" | xargs)"
    [ -z "$db" ] && continue
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
      SELECT 'CREATE DATABASE "$db" OWNER "$POSTGRES_USER"'
      WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
      GRANT ALL PRIVILEGES ON DATABASE "$db" TO "$POSTGRES_USER";
EOSQL
  done
fi
