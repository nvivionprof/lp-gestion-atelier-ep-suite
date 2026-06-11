# LP Gestion Atelier EP Suite — RC14 maintenance

## Type de livraison

Cette RC14 est une **installation complète SSH + outils de maintenance**. Elle n'est pas une simple mise à jour web.

Elle ajoute ou remplace :

- `install.sh` : installation assistée avec choix local/réseau/domaine, IP/domaine, comptes, mots de passe, chargement démo oui/non.
- `update.sh` : mise à jour rapide depuis Git avec vérification de compatibilité, sauvegarde, migrations et collectstatic.
- `upgrade.sh` : upgrade classique depuis Git ou ZIP avec compatibilité, sauvegarde, migrations et collectstatic.
- `scripts/preflight_compat.sh` : contrôle Docker, `.env`, `docker-compose.yml`, services attendus, espace disque et version.
- `scripts/backup_all.sh` : sauvegarde PostgreSQL complète + `.env` + `docker-compose.yml`.
- `scripts/migrate_all.sh` : migrations Django de tous les modules.
- `scripts/create_initial_admins.sh` : création des comptes admin LP Core et Django.
- `scripts/load_demo_data.sh` : chargement base démo globale.
- `scripts/postgres/init-multiple-databases.sh` : correction de l'initialisation PostgreSQL avec `--dbname postgres`.

## Installation neuve assistée

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-rc
bash install.sh
```

L'assistant demande :

- mode `local`, `réseau` ou `domaine` ;
- IP serveur ou nom de domaine ;
- activation HTTPS ou non ;
- identifiants admin ;
- mot de passe PostgreSQL ;
- chargement de la base de démonstration oui/non.

## Mise à jour rapide Git

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-rc
bash update.sh --branch=rc
```

Avec chargement/rechargement de la démo :

```bash
bash update.sh --branch=rc --with-demo
```

## Upgrade classique

Depuis la branche `rc` :

```bash
bash upgrade.sh --branch=rc
```

Depuis un ZIP de patch :

```bash
bash upgrade.sh --zip=/home/mon-patch.zip
```

Avec démo :

```bash
bash upgrade.sh --zip=/home/mon-patch.zip --with-demo
```

## Sauvegarde manuelle

```bash
bash scripts/backup_all.sh
```

Les sauvegardes sont stockées dans :

```text
backups/manual/
```

## Chargement démo manuel

```bash
bash scripts/load_demo_data.sh
bash scripts/sync_all_modules_from_core.sh
```

## Contrôle santé

```bash
docker compose --env-file .env ps

curl -sSI http://localhost:9000/ | head
curl -sSI http://localhost:9000/toolmag/ | head
curl -sSI http://localhost:9000/safety/ | head
curl -sSI http://localhost:9000/pedashop/ | head
curl -sSI http://localhost:9000/system/ | head
curl -sSI http://localhost:9000/tpmanager/ | head
curl -sSI http://localhost:9000/pfmp/ | head
```

`200 OK` ou `302 Found` est acceptable selon les pages protégées par connexion.
