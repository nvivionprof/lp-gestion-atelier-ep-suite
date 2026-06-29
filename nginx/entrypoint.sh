#!/usr/bin/env bash
set -euo pipefail
PUBLIC_DOMAIN="${PUBLIC_DOMAIN:-localhost}"
ENABLE_HTTPS="${ENABLE_HTTPS:-0}"
SSL_CERT_FILE="${SSL_CERT_FILE:-/ssl/fullchain.pem}"
SSL_KEY_FILE="${SSL_KEY_FILE:-/ssl/privkey.pem}"
mkdir -p /var/www/certbot /etc/nginx/conf.d

cat >/etc/nginx/conf.d/lp-proxy-common.inc <<'EOF'
proxy_http_version 1.1;
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Host $http_host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Port $server_port;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_redirect off;
client_max_body_size 2048m;
EOF

write_locations(){
cat <<'EOF'
  absolute_redirect off;
  port_in_redirect off;

  resolver 127.0.0.11 valid=10s ipv6=off;
  resolver_timeout 5s;

  location ^~ /.well-known/acme-challenge/ {
    root /var/www/certbot;
    default_type "text/plain";
  }

  # Redirections relatives : ne perdent jamais le port externe du portail.
  location = /toolmag { return 301 /toolmag/; }
  location = /safety { return 301 /safety/; }
  location = /pedashop { return 301 /pedashop/; }
  location = /system { return 301 /system/; }
  location = /tpmanager { return 301 /tpmanager/; }
  location = /pfmp { return 301 /pfmp/; }
  location = /lpdisplaymanager { return 301 /lpdisplaymanager/; }
  location = /displaymanager { return 301 /lpdisplaymanager/; }
  location ^~ /displaymanager/ { return 301 /lpdisplaymanager/; }

  # Fichiers statiques servis directement par le portail depuis les STATIC_ROOT collectés.
  location ^~ /static/core/ { alias /gateway-static/lp-core/core/; expires 1h; access_log off; }
  location ^~ /static/admin/ { alias /gateway-static/lp-core/admin/; expires 1h; access_log off; }
  location ^~ /static/inventory/ { alias /gateway-static/toolmag/inventory/; expires 1h; access_log off; }
  location ^~ /static/safety_manager/ { alias /gateway-static/safety/safety_manager/; expires 1h; access_log off; }
  location ^~ /static/pedashop/ { alias /gateway-static/pedashop/pedashop/; expires 1h; access_log off; }
  location ^~ /static/system_manager/ { alias /gateway-static/system-manager/system_manager/; expires 1h; access_log off; }
  location ^~ /static/tp_manager/ { alias /gateway-static/tpmanager/tp_manager/; expires 1h; access_log off; }
  location ^~ /static/evaluation_manager/ { alias /gateway-static/tpmanager/evaluation_manager/; expires 1h; access_log off; }
  location ^~ /static/sequence_manager/ { alias /gateway-static/tpmanager/sequence_manager/; expires 1h; access_log off; }
  location ^~ /static/pfmp_manager/ { alias /gateway-static/pfmp/pfmp_manager/; expires 1h; access_log off; }
  location ^~ /static/display_manager/ { alias /gateway-static/lp-display-manager/display_manager/; expires 1h; access_log off; }
  location ^~ /lpdisplaymanager/static/ { alias /gateway-static/lp-display-manager/; expires 1h; access_log off; }
  location ^~ /lpdisplaymanager/uploads/ { alias /gateway-media/lp-display-manager/; expires 1h; access_log off; }

  # Médias utilisateurs : photos, documents et pièces jointes.
  # Servis directement par la passerelle pour éviter les pertes de préfixe /system, /tpmanager, etc.
  location ^~ /media/ { alias /gateway-media/lp-core/; expires 1h; access_log off; }
  location ^~ /toolmag/media/ { alias /gateway-media/toolmag/; expires 1h; access_log off; }
  location ^~ /safety/media/ { alias /gateway-media/safety/; expires 1h; access_log off; }
  location ^~ /pedashop/media/ { alias /gateway-media/pedashop/; expires 1h; access_log off; }
  location ^~ /system/media/ { alias /gateway-media/system-manager/; expires 1h; access_log off; }
  location ^~ /tpmanager/media/ { alias /gateway-media/tpmanager/; expires 1h; access_log off; }
  location ^~ /pfmp/media/ { alias /gateway-media/pfmp/; expires 1h; access_log off; }

  # Compatibilité si une application génère une URL statique préfixée par son chemin public.
  location ^~ /toolmag/static/ { alias /gateway-static/toolmag/; expires 1h; access_log off; }
  location ^~ /safety/static/ { alias /gateway-static/safety/; expires 1h; access_log off; }
  location ^~ /pedashop/static/ { alias /gateway-static/pedashop/; expires 1h; access_log off; }
  location ^~ /system/static/ { alias /gateway-static/system-manager/; expires 1h; access_log off; }
  location ^~ /tpmanager/static/ { alias /gateway-static/tpmanager/; expires 1h; access_log off; }
  location ^~ /pfmp/static/ { alias /gateway-static/pfmp/; expires 1h; access_log off; }

  # Routage contrôlé : chaque préfixe pointe explicitement vers son conteneur.
  location ^~ /toolmag/ {
    add_header X-LP-Gateway-Module "toolmag" always;
    include /etc/nginx/conf.d/lp-proxy-common.inc;
    proxy_set_header X-Forwarded-Prefix /toolmag;
    proxy_set_header X-Script-Name /toolmag;
    set $toolmag_upstream toolmag-app:8000;
    rewrite ^/toolmag/(.*)$ /$1 break;
    proxy_pass http://$toolmag_upstream;
  }
  location ^~ /safety/ {
    add_header X-LP-Gateway-Module "safety" always;
    include /etc/nginx/conf.d/lp-proxy-common.inc;
    proxy_set_header X-Forwarded-Prefix /safety;
    proxy_set_header X-Script-Name /safety;
    set $safety_upstream safety-app:8000;
    rewrite ^/safety/(.*)$ /$1 break;
    proxy_pass http://$safety_upstream;
  }
  location ^~ /pedashop/ {
    add_header X-LP-Gateway-Module "pedashop" always;
    include /etc/nginx/conf.d/lp-proxy-common.inc;
    proxy_set_header X-Forwarded-Prefix /pedashop;
    proxy_set_header X-Script-Name /pedashop;
    set $pedashop_upstream pedashop-app:8000;
    rewrite ^/pedashop/(.*)$ /$1 break;
    proxy_pass http://$pedashop_upstream;
  }
  location ^~ /system/ {
    add_header X-LP-Gateway-Module "system" always;
    include /etc/nginx/conf.d/lp-proxy-common.inc;
    proxy_set_header X-Forwarded-Prefix /system;
    proxy_set_header X-Script-Name /system;
    set $system_upstream system-manager-app:8000;
    rewrite ^/system/(.*)$ /$1 break;
    proxy_pass http://$system_upstream;
  }
  location ^~ /tpmanager/ {
    add_header X-LP-Gateway-Module "tpmanager" always;
    include /etc/nginx/conf.d/lp-proxy-common.inc;
    proxy_set_header X-Forwarded-Prefix /tpmanager;
    proxy_set_header X-Script-Name /tpmanager;
    set $tpmanager_upstream tpmanager-app:8000;
    rewrite ^/tpmanager/(.*)$ /$1 break;
    proxy_pass http://$tpmanager_upstream;
  }
  location ^~ /pfmp/ {
    add_header X-LP-Gateway-Module "pfmp" always;
    include /etc/nginx/conf.d/lp-proxy-common.inc;
    proxy_set_header X-Forwarded-Prefix /pfmp;
    proxy_set_header X-Script-Name /pfmp;
    set $pfmp_upstream pfmp-app:8000;
    rewrite ^/pfmp/(.*)$ /$1 break;
    proxy_pass http://$pfmp_upstream;
  }
  location ^~ /lpdisplaymanager/ {
    add_header X-LP-Gateway-Module "lpdisplaymanager" always;
    include /etc/nginx/conf.d/lp-proxy-common.inc;
    proxy_set_header X-Forwarded-Prefix /lpdisplaymanager;
    proxy_set_header X-Script-Name /lpdisplaymanager;
    set $lpdisplay_upstream lp-display-manager-app:8000;
    rewrite ^/lpdisplaymanager/(.*)$ /$1 break;
    proxy_pass http://$lpdisplay_upstream;
  }
  location / {
    add_header X-LP-Gateway-Module "lp-core" always;
    include /etc/nginx/conf.d/lp-proxy-common.inc;
    set $lpcore_upstream lp-core-app:8000;
    proxy_pass http://$lpcore_upstream;
  }
EOF
}


wait_for_upstreams(){
  echo "[INFO] Attente résolution DNS des conteneurs applicatifs..."
  UPSTREAMS="
    lp-core-app
    toolmag-app
    safety-app
    pedashop-app
    system-manager-app
    tpmanager-app
    pfmp-app
    lp-display-manager-app
  "

  for host in $UPSTREAMS; do
    echo "[INFO] Vérification DNS: $host"
    ok=0
    for i in $(seq 1 60); do
      if getent hosts "$host" >/dev/null 2>&1; then
        echo "[OK] $host résolu"
        ok=1
        break
      fi
      sleep 1
    done

    if [ "$ok" != "1" ]; then
      echo "[WARN] $host non résolu après attente, Nginx tentera quand même de démarrer"
    fi
  done
}

if [[ "$ENABLE_HTTPS" == "1" && -f "$SSL_CERT_FILE" && -f "$SSL_KEY_FILE" ]]; then
  cat >/etc/nginx/conf.d/default.conf <<EOF
server {
  listen 80;
  server_name ${PUBLIC_DOMAIN};
  location ^~ /.well-known/acme-challenge/ {
    root /var/www/certbot;
    default_type "text/plain";
  }
  location / { return 301 https://\$http_host\$request_uri; }
}
server {
  listen 443 ssl http2;
  server_name ${PUBLIC_DOMAIN};
  ssl_certificate ${SSL_CERT_FILE};
  ssl_certificate_key ${SSL_KEY_FILE};
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_prefer_server_ciphers on;
  add_header Strict-Transport-Security "max-age=31536000" always;
$(write_locations)
}
EOF
else
  cat >/etc/nginx/conf.d/default.conf <<EOF
server {
  listen 80;
  server_name ${PUBLIC_DOMAIN} localhost _;
$(write_locations)
}
EOF
fi

wait_for_upstreams
nginx -t
exec "$@"
