# HTTPS direct et certificats — V2.4

Cette version ajoute un mode **HTTPS direct par module**, sans reverse proxy obligatoire.

Objectif : conserver des QR codes simples du type :

```text
https://homeassistantcc.duckdns.org:9004/...
```

au lieu d'une publication par chemins type `/system/`, `/tp/`, etc.

## Principe

Chaque application reste sur son port :

```text
LP Core        : 9000
ToolMag        : 9001
Safety Manager : 9002
PedaShop       : 9003
System Manager : 9004
TP Manager     : 9005
```

Quand `ENABLE_HTTPS=1`, chaque conteneur Django/Gunicorn démarre avec :

```text
/ssl/fullchain.pem
/ssl/privkey.pem
```

Le même certificat est donc partagé en lecture seule avec tous les modules.

## Chemins serveur

Dossier des certificats sur l'hôte :

```text
/home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite/ssl/
```

Fichiers finaux attendus :

```text
ssl/fullchain.pem
ssl/privkey.pem
```

## Interface LP Core

Une page a été ajoutée :

```text
LP Core > URLs / HTTPS
```

Elle permet de choisir :

- domaine public ;
- protocole HTTP ou HTTPS ;
- mode d'exposition ;
- ports publics ;
- méthode Let's Encrypt :
  - `DNS-01 via DuckDNS` ;
  - `HTTP-01 via port 80` ;
- email Let's Encrypt ;
- token DuckDNS, si méthode DNS.

Après enregistrement, LP Core génère :

```text
lp-core-db/data/cert-manager.env
```

Ce fichier sert ensuite aux scripts SSH.

## Appliquer la configuration

Depuis le dossier du projet :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
./scripts/apply_public_settings.sh
```

Ce script applique les URLs publiques dans `.env`.

## Générer le certificat

```bash
./scripts/cert_manager.sh issue
```

Le script lit automatiquement :

```text
.env
lp-core-db/data/cert-manager.env
```

## Renouveler le certificat

```bash
./scripts/cert_manager.sh renew
```

## Installer le renouvellement automatique

```bash
./scripts/install_cert_renew_cron.sh
```

Cela ajoute une tâche quotidienne dans la crontab de l'utilisateur.

## Challenge DNS-01 DuckDNS

Avantages :

- ne nécessite pas d'ouvrir le port 80 ;
- fonctionne même si le serveur n'est pas joignable temporairement en HTTP ;
- proche de la logique DuckDNS/Let's Encrypt de Home Assistant.

Pré-requis :

```text
DUCKDNS_TOKEN renseigné
PUBLIC_DOMAIN renseigné
LETSENCRYPT_EMAIL renseigné
```

Le script utilise le conteneur Docker `goacme/lego`.

## Challenge HTTP-01

Avantages :

- méthode classique Let's Encrypt ;
- pas besoin de token DuckDNS.

Pré-requis :

```text
port 80 externe de la box → port 80 du serveur Debian
port 80 libre sur le serveur pendant la génération/renouvellement
```

Le script utilise le conteneur Docker `certbot/certbot`.

## Redirections box en HTTPS direct

Si le serveur Debian est :

```text
192.168.101.19
```

Rediriger :

```text
TCP 9000 → 192.168.101.19:9000
TCP 9001 → 192.168.101.19:9001
TCP 9002 → 192.168.101.19:9002
TCP 9003 → 192.168.101.19:9003
TCP 9004 → 192.168.101.19:9004
TCP 9005 → 192.168.101.19:9005
```

Pour HTTP-01 seulement, ajouter temporairement ou durablement :

```text
TCP 80 → 192.168.101.19:80
```

## Ordre recommandé

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
./start.sh
```

Puis dans LP Core :

```text
URLs / HTTPS
```

Enregistrer la configuration.

Ensuite en SSH :

```bash
./scripts/apply_public_settings.sh
./scripts/cert_manager.sh issue
docker compose up -d --build
./scripts/install_cert_renew_cron.sh
```

## Vérification

```bash
./scripts/cert_manager.sh status
curl -k -I https://127.0.0.1:9000
curl -k -I https://127.0.0.1:9004
```

Depuis l'extérieur :

```text
https://homeassistantcc.duckdns.org:9000
https://homeassistantcc.duckdns.org:9004
https://homeassistantcc.duckdns.org:9005
```
