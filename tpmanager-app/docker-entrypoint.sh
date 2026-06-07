#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

# TP Manager V2 : chargement non destructif des référentiels Bac Pro.
# Idempotent : n'écrase pas les TP, documents, ressources ni critères créés par les utilisateurs.
if [ "${TPMANAGER_SEED_V2:-1}" = "1" ]; then
  python manage.py seed_tpmanager_v2 || true
  python manage.py seed_sequence_manager || true
fi

python manage.py collectstatic --noinput

GUNICORN_ARGS="--bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT:-120}"
if [ "${ENABLE_HTTPS:-0}" = "1" ]; then
  if [ ! -f "${SSL_CERT_FILE:-/ssl/fullchain.pem}" ] || [ ! -f "${SSL_KEY_FILE:-/ssl/privkey.pem}" ]; then
    echo "ERREUR: ENABLE_HTTPS=1 mais certificat ou clé introuvable." >&2
    echo "Certificat attendu: ${SSL_CERT_FILE:-/ssl/fullchain.pem}" >&2
    echo "Clé attendue: ${SSL_KEY_FILE:-/ssl/privkey.pem}" >&2
    exit 1
  fi
  echo "Démarrage HTTPS direct avec certificat ${SSL_CERT_FILE:-/ssl/fullchain.pem}"
  exec gunicorn "$DJANGO_WSGI_MODULE" $GUNICORN_ARGS --certfile "${SSL_CERT_FILE:-/ssl/fullchain.pem}" --keyfile "${SSL_KEY_FILE:-/ssl/privkey.pem}"
fi

echo "Démarrage HTTP interne/direct"
exec gunicorn "$DJANGO_WSGI_MODULE" $GUNICORN_ARGS
