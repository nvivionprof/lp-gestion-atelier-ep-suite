#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ACTION="${1:-issue}"
ENV_FILE=".env"
CERT_ENV="lp-core-db/data/cert-manager.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi
if [[ -f "$CERT_ENV" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$CERT_ENV"
  set +a
fi

PUBLIC_DOMAIN="${PUBLIC_DOMAIN:-${SERVER_IP:-}}"
PUBLIC_DOMAIN="${PUBLIC_DOMAIN#http://}"
PUBLIC_DOMAIN="${PUBLIC_DOMAIN#https://}"
PUBLIC_DOMAIN="${PUBLIC_DOMAIN%%/*}"
PUBLIC_DOMAIN="${PUBLIC_DOMAIN%%:*}"

LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"
CERT_CHALLENGE_METHOD="${CERT_CHALLENGE_METHOD:-dns_duckdns}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-}"
SSL_DIR="${SSL_DIR:-$(pwd)/ssl}"
mkdir -p "$SSL_DIR"

need() {
  if [[ -z "${!1:-}" ]]; then
    echo "ERREUR: variable $1 manquante. Configure-la dans LP Core > URLs / HTTPS ou dans .env." >&2
    exit 1
  fi
}

has_docker() {
  command -v docker >/dev/null 2>&1
}

has_lego() {
  command -v lego >/dev/null 2>&1
}

compose() {
  if has_docker && docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    echo "AVERTISSEMENT: docker compose introuvable dans cet environnement. Redémarrage automatique impossible." >&2
    return 127
  fi
}

copy_from_lego() {
  local cert_dir="$SSL_DIR/lego/certificates"
  local crt="$cert_dir/${PUBLIC_DOMAIN}.crt"
  local key="$cert_dir/${PUBLIC_DOMAIN}.key"
  local issuer="$cert_dir/${PUBLIC_DOMAIN}.issuer.crt"
  [[ -f "$crt" ]] || { echo "Certificat lego introuvable: $crt" >&2; exit 1; }
  [[ -f "$key" ]] || { echo "Clé lego introuvable: $key" >&2; exit 1; }
  if [[ -f "$issuer" ]]; then
    cat "$crt" "$issuer" > "$SSL_DIR/fullchain.pem"
  else
    cp "$crt" "$SSL_DIR/fullchain.pem"
  fi
  cp "$key" "$SSL_DIR/privkey.pem"
  chmod 600 "$SSL_DIR/privkey.pem"
}

copy_from_certbot() {
  local live="$SSL_DIR/letsencrypt/live/$PUBLIC_DOMAIN"
  [[ -f "$live/fullchain.pem" ]] || { echo "Certificat certbot introuvable: $live/fullchain.pem" >&2; exit 1; }
  [[ -f "$live/privkey.pem" ]] || { echo "Clé certbot introuvable: $live/privkey.pem" >&2; exit 1; }
  cp "$live/fullchain.pem" "$SSL_DIR/fullchain.pem"
  cp "$live/privkey.pem" "$SSL_DIR/privkey.pem"
  chmod 600 "$SSL_DIR/privkey.pem"
}

restart_suite() {
  echo "Rechargement éventuel de lp-gateway..."
  if compose restart lp-gateway; then
    return 0
  fi
  echo "AVERTISSEMENT: lp-gateway n'a pas pu être redémarré automatiquement. Lance depuis SSH:" >&2
  echo "  cd $(pwd) && docker compose restart lp-gateway" >&2
  return 0
}

run_lego_cmd() {
  if has_lego; then
    DUCKDNS_TOKEN="$DUCKDNS_TOKEN" lego "$@"
    return $?
  fi
  if has_docker; then
    docker run --rm \
      -e DUCKDNS_TOKEN="$DUCKDNS_TOKEN" \
      -v "$SSL_DIR/lego:/lego" \
      goacme/lego:latest \
      "$@"
    return $?
  fi
  cat >&2 <<'EOM'
ERREUR: ni la commande lego ni la commande docker ne sont disponibles dans l'environnement qui exécute cert_manager.sh.

Correction recommandée : appliquer le patch V0.4.0b puis reconstruire l'agent :
  cd /home/user/docker/lp-gestion-atelier-ep-suite
  docker compose up -d --build --no-cache suite-admin-agent

Le patch V0.4.0b installe le binaire lego directement dans suite-admin-agent afin de ne plus dépendre de docker pour le DNS-01 DuckDNS.
EOM
  exit 127
}

issue_dns_duckdns() {
  need PUBLIC_DOMAIN
  need LETSENCRYPT_EMAIL
  need DUCKDNS_TOKEN
  echo "Génération Let's Encrypt DNS-01 via DuckDNS pour $PUBLIC_DOMAIN"
  run_lego_cmd \
    --path "$SSL_DIR/lego" \
    --email "$LETSENCRYPT_EMAIL" \
    --dns duckdns \
    --domains "$PUBLIC_DOMAIN" \
    --accept-tos \
    run
  copy_from_lego
  restart_suite
}

renew_dns_duckdns() {
  need PUBLIC_DOMAIN
  need LETSENCRYPT_EMAIL
  need DUCKDNS_TOKEN
  echo "Renouvellement Let's Encrypt DNS-01 via DuckDNS pour $PUBLIC_DOMAIN"
  set +e
  run_lego_cmd \
    --path "$SSL_DIR/lego" \
    --email "$LETSENCRYPT_EMAIL" \
    --dns duckdns \
    --domains "$PUBLIC_DOMAIN" \
    --accept-tos \
    renew --days 30
  local code=$?
  set -e
  if [[ $code -ne 0 ]]; then
    echo "Renouvellement lego non effectué ou non nécessaire. Vérification des fichiers existants..."
  fi
  copy_from_lego
  restart_suite
}

issue_http_01() {
  need PUBLIC_DOMAIN
  need LETSENCRYPT_EMAIL
  echo "Génération Let's Encrypt HTTP-01 pour $PUBLIC_DOMAIN via webroot lp-gateway"
  echo "Pré-requis: port 80 de la box redirigé vers ce serveur et lp-gateway démarré."
  mkdir -p "$SSL_DIR/acme"
  compose up -d lp-gateway || true
  if has_docker; then
    docker run --rm \
      -v "$SSL_DIR/letsencrypt:/etc/letsencrypt" \
      -v "$SSL_DIR/lib:/var/lib/letsencrypt" \
      -v "$SSL_DIR/log:/var/log/letsencrypt" \
      -v "$SSL_DIR/acme:/var/www/certbot" \
      certbot/certbot:latest certonly --webroot -w /var/www/certbot \
      --non-interactive --agree-tos --no-eff-email \
      --email "$LETSENCRYPT_EMAIL" \
      -d "$PUBLIC_DOMAIN"
    copy_from_certbot
    restart_suite
    return 0
  fi
  echo "ERREUR: HTTP-01 nécessite docker/certbot. Utilise DNS-01 DuckDNS ou lance la commande depuis SSH." >&2
  exit 127
}

renew_http_01() {
  need PUBLIC_DOMAIN
  if has_docker; then
    docker run --rm \
      -v "$SSL_DIR/letsencrypt:/etc/letsencrypt" \
      -v "$SSL_DIR/lib:/var/lib/letsencrypt" \
      -v "$SSL_DIR/log:/var/log/letsencrypt" \
      -v "$SSL_DIR/acme:/var/www/certbot" \
      certbot/certbot:latest renew --webroot -w /var/www/certbot || true
    copy_from_certbot
    restart_suite
    return 0
  fi
  echo "ERREUR: HTTP-01 nécessite docker/certbot. Utilise DNS-01 DuckDNS ou lance la commande depuis SSH." >&2
  exit 127
}

status() {
  echo "Domaine: ${PUBLIC_DOMAIN:-non défini}"
  echo "Méthode: ${CERT_CHALLENGE_METHOD:-non définie}"
  echo "SSL_DIR: $SSL_DIR"
  echo "docker: $(command -v docker || true)"
  echo "lego: $(command -v lego || true)"
  if [[ -f "$SSL_DIR/fullchain.pem" ]]; then
    echo "Certificat présent: $SSL_DIR/fullchain.pem"
    openssl x509 -in "$SSL_DIR/fullchain.pem" -noout -subject -issuer -dates || true
  else
    echo "Aucun certificat fullchain.pem trouvé."
  fi
}

case "$ACTION" in
  issue)
    case "$CERT_CHALLENGE_METHOD" in
      dns_duckdns|duckdns|dns) issue_dns_duckdns ;;
      http_01|http|webroot) issue_http_01 ;;
      *) echo "Méthode inconnue: $CERT_CHALLENGE_METHOD" >&2; exit 2 ;;
    esac
    ;;
  renew)
    case "$CERT_CHALLENGE_METHOD" in
      dns_duckdns|duckdns|dns) renew_dns_duckdns ;;
      http_01|http|webroot) renew_http_01 ;;
      *) echo "Méthode inconnue: $CERT_CHALLENGE_METHOD" >&2; exit 2 ;;
    esac
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $0 {issue|renew|status}" >&2
    exit 2
    ;;
esac
