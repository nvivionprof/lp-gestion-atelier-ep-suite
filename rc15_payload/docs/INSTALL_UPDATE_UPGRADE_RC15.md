# LP Gestion Atelier EP Suite — RC15

Type : installation complète SSH + maintenance. Ce n'est pas une mise à jour web.

## Objectif RC15

RC15 corrige les problèmes observés en installation neuve :

- suppression fiable des instances précédentes quand on choisit le mode `fresh` ;
- suppression des bases et données locales de l'installation courante sans sauvegarde si confirmé ;
- migrations Django exécutées avant le démarrage des applications ;
- création des administrateurs compatible avec des applications non encore démarrées ;
- collectstatic compatible avec des applications non encore démarrées ;
- `seed_core` rendu plus idempotent lorsque l'import Excel a déjà créé `PROF-0001` ;
- ajout de `scripts/reset_fresh_install.sh`.

## Installation neuve assistée

```bash
bash install.sh
```

Choisir :

- `fresh` pour supprimer l'instance précédente de ce dossier et repartir à zéro ;
- `network` pour un accès réseau local ;
- IP serveur, par exemple `192.168.101.19` ;
- HTTPS : `non` pour un premier test ;
- base démo : `oui` ou `non`.

Le contrôle `localhost:9000` affiché en fin d'installation est un contrôle interne au serveur. En mode réseau, l'URL utilisateur est l'URL indiquée par l'installateur, par exemple :

```text
http://192.168.101.19:9000
```

## Suppression complète de l'instance courante

```bash
bash scripts/reset_fresh_install.sh
```

Ce script supprime conteneurs, volumes Compose et données locales de l'installation courante. Il ne fait aucune sauvegarde.

## Mise à jour rapide

```bash
bash update.sh --branch=rc
```

## Upgrade classique

```bash
bash upgrade.sh --branch=rc
```

## Base de démonstration après installation

```bash
bash scripts/load_demo_data.sh
bash scripts/sync_all_modules_from_core.sh
```

## Contrôle final

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

`200 OK` ou `302 Found` est correct.
