# Installation RC19 — TLS DuckDNS ou certificat lycée

## 1. Copier les fichiers du paquet

Depuis la racine de LP Suite :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
cp -r /chemin/du/paquet/scripts ./
cp -r /chemin/du/paquet/certs ./
```

Puis rendre les scripts exécutables :

```bash
chmod +x ./scripts/tls-*.sh
```

## 2. Ajouter les variables dans `.env`

Choisir un mode :

```env
HTTPS_MODE=duckdns-acme
EXTERNAL_PUBLIC_DOMAIN=stjo-lpsuite.duckdns.org
PUBLIC_DOMAIN=stjo-lpsuite.duckdns.org:9000
DUCKDNS_DOMAIN=stjo-lpsuite
DUCKDNS_FULL_DOMAIN=stjo-lpsuite.duckdns.org
DUCKDNS_TOKEN=xxxxxxxxxxxxxxxxxxxx
TLS_EMAIL=nvivion.prof@gmail.com
TLS_HOST_CERT_DIR=./certs/manual
```

Pour un certificat lycée :

```env
HTTPS_MODE=manual
EXTERNAL_PUBLIC_DOMAIN=lp-suite.lycee.local
TLS_HOST_CERT_DIR=./certs/manual
```

## 3. Mode DuckDNS

```bash
./scripts/tls-duckdns-issue.sh
```

Le certificat généré sera installé ici :

```text
./certs/manual/fullchain.pem
./certs/manual/privkey.pem
```

## 4. Mode certificat lycée

Le lycée doit fournir au minimum :

```text
fullchain.pem ou certificat serveur + chaîne intermédiaire
privkey.pem
```

Installation :

```bash
./scripts/tls-manual-install.sh /chemin/fullchain.pem /chemin/privkey.pem
```

## 5. Relance

```bash
docker compose up -d --force-recreate
```

ou au minimum :

```bash
docker compose restart lp-core-proxy
```

Adapter le nom du service proxy si besoin.
