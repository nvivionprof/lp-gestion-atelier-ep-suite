# RC19 Fusion — PFMP géocodage + TLS DuckDNS / certificat établissement

Type : **upgrade classique / maintenance SSH**.

Ce paquet fusionne :

- RC19 PFMP géocodage entreprises ;
- TLS Cert Manager DuckDNS / certificat manuel ;
- scripts `tls-*` adaptés au service `lp-gateway` et au dossier `./ssl` déjà monté par Docker Compose.

## Points importants

- Les certificats réels ne sont jamais versionnés.
- Le dossier attendu côté hôte est `./ssl`.
- Le reverse proxy `lp-gateway` lit déjà `/ssl/fullchain.pem` et `/ssl/privkey.pem` lorsque `ENABLE_HTTPS=1`.
- DuckDNS utilise un challenge DNS-01 : aucun port 80/443 entrant n'est nécessaire pour émettre le certificat.

## Commandes principales

### Certificat auto-signé de test

```bash
bash scripts/tls-selfsigned-test.sh
bash scripts/tls-env-apply.sh selfsigned lp-suite.local
docker compose --env-file .env up -d --force-recreate lp-gateway
```

### Certificat manuel lycée

```bash
bash scripts/tls-manual-install.sh /chemin/fullchain.pem /chemin/privkey.pem
bash scripts/tls-env-apply.sh manual lp-suite.mon-lycee.fr
docker compose --env-file .env up -d --force-recreate lp-gateway
```

### DuckDNS + Let's Encrypt DNS-01

```bash
bash scripts/tls-env-apply.sh duckdns-acme stjo-lpsuite.duckdns.org 'TOKEN_DUCKDNS'
bash scripts/tls-duckdns-issue.sh
docker compose --env-file .env up -d --force-recreate lp-gateway
```

### Statut certificat

```bash
bash scripts/tls-status.sh
```

## Variables .env utiles

```env
ENABLE_HTTPS=1
HTTPS_MODE=duckdns-acme
PUBLIC_DOMAIN=stjo-lpsuite.duckdns.org:9000
EXTERNAL_PUBLIC_DOMAIN=stjo-lpsuite.duckdns.org
SSL_CERT_FILE=/ssl/fullchain.pem
SSL_KEY_FILE=/ssl/privkey.pem
TLS_HOST_CERT_DIR=./ssl
DUCKDNS_DOMAIN=stjo-lpsuite
DUCKDNS_FULL_DOMAIN=stjo-lpsuite.duckdns.org
DUCKDNS_TOKEN=CHANGE_ME_NEVER_COMMIT
TLS_EMAIL=nvivion.prof@gmail.com
```
