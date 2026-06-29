# Installation LP Display Manager v0.1 dans LP Suite

## 1. Copier les fichiers

Depuis la racine du dépôt LP Suite :

```bash
./install-lpdisplaymanager.sh /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
```

## 2. Intégrer Docker

Ajouter le service `lp-display-manager-app` du fichier :

```text
docker-compose.lpdisplaymanager.snippet.yml
```

au `docker-compose.yml` principal.

Ne pas ajouter :

```yaml
ports:
  - "9007:8000"
```

Le module ne doit pas exposer de port externe.

## 3. Intégrer le reverse proxy

Ajouter le contenu de :

```text
nginx.lpdisplaymanager.snippet.conf
```

au reverse proxy principal.

L'URL cible doit être :

```text
http://<serveur>:9000/lpdisplaymanager
```

## 4. Démarrer

```bash
docker compose build lp-display-manager-app
docker compose up -d lp-display-manager-app
```

Puis, si nécessaire :

```bash
docker compose exec lp-display-manager-app python manage.py migrate
docker compose exec lp-display-manager-app python manage.py createsuperuser
```

## 5. Ajouter la tuile LP Core

Tuile :

```text
Nom : LP Display Manager
URL : /lpdisplaymanager
Description : Gestion des écrans, layouts, médias et players Raspberry Pi.
```

## 6. Sauvegarde/restauration

Ajouter au mécanisme de sauvegarde :

```text
./data/lpdisplaymanager/db
./data/lpdisplaymanager/media
```
