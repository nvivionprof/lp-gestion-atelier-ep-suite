# HTTPS DuckDNS rapide — LP Gestion Atelier EP Suite

Objectif : activer HTTPS avec un domaine `*.duckdns.org` sans refaire une installation complète.

## Principe

- Challenge DNS-01 DuckDNS via lego.
- Pas besoin d'ouvrir le port 80 pour obtenir le certificat.
- Le portail Nginx `lp-gateway` sert ensuite HTTPS.
- Les bases, médias et sauvegardes ne sont pas modifiés.

## Commande

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-rc

./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org nvivion.prof@gmail.com TOKEN_DUCKDNS 443 80
```

Si la box redirige le port externe 443 vers le port interne 9443 du serveur :

```bash
./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org nvivion.prof@gmail.com TOKEN_DUCKDNS 9443 9000
```

## Variables modifiées

Le script met à jour `.env` :

```env
PUBLIC_DOMAIN=stjo-lpsuite.duckdns.org
PUBLIC_SCHEME=https
ENABLE_HTTPS=1
GATEWAY_HTTPS_PORT=443
LP_CORE_PUBLIC_URL=https://stjo-lpsuite.duckdns.org
TOOLMAG_PUBLIC_BASE_URL=https://stjo-lpsuite.duckdns.org/toolmag/
SESSION_COOKIE_SECURE=1
CSRF_COOKIE_SECURE=1
CERT_CHALLENGE_METHOD=dns_duckdns
```

## Renouvellement

```bash
./scripts/cert_manager.sh renew
```
