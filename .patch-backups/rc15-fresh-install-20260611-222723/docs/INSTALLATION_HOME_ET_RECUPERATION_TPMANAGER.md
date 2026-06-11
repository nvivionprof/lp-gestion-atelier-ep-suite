# Installation depuis `/home` et récupération manuelle de la base TP Manager

Document à maintenir à jour à chaque évolution touchant :

- l'arborescence du projet ;
- les noms de conteneurs ;
- les chemins de bases SQLite ;
- les procédures de sauvegarde/restauration ;
- le module TP Manager.

Version concernée : **LP Gestion Atelier EP Suite — Bêta V0.0.1**

---

## 1. Hypothèse d'installation utilisée par Nicolas

Sur le serveur de test ou le serveur lycée, l'archive ZIP est placée dans :

```bash
/home
```

Exemple :

```bash
/home/lp-gestion-atelier-ep-suite-beta-v0.0.1-camera-devdocs.zip
```

L'installation ou la reprise se fait ensuite depuis le dossier extrait.

Exemple conseillé :

```bash
cd /home
unzip lp-gestion-atelier-ep-suite-beta-v0.0.1-camera-devdocs.zip
cd lp-gestion-atelier-ep-suite-beta-v0.0.1
chmod +x install.sh start.sh stop.sh upgrade.sh scripts/*.sh
./install.sh
```

> Important : toutes les commandes `docker compose` doivent être lancées depuis le dossier racine de la suite, c'est-à-dire le dossier qui contient `docker-compose.yml`.

---

## 2. Rappel des chemins TP Manager

Dans cette version, le service Docker TP Manager est :

```text
tpmanager-app
```

Le conteneur Docker est :

```text
tpmanager-app
```

La base SQLite dans le conteneur est :

```text
/data/tpmanager/tp-manager.sqlite3
```

Le dossier persistant côté hôte est :

```text
./tpmanager-db/data/
```

La base SQLite côté hôte est donc :

```text
./tpmanager-db/data/tp-manager.sqlite3
```

---

## 3. Cas important : ancien serveur sans import/export web TP Manager

Sur certaines versions précédentes, TP Manager ne disposait pas encore d'une interface web d'import/export de base.

Dans ce cas, la récupération se fait manuellement depuis le serveur, soit :

1. par copie du fichier SQLite si la suite est arrêtée ;
2. par sauvegarde SQLite propre depuis le conteneur si la suite tourne encore.

La méthode 2 est préférable si le serveur est en fonctionnement, car elle évite de copier une base SQLite pendant une écriture.

---

## 4. Méthode recommandée : sauvegarde propre depuis le conteneur

À lancer sur l'ancien serveur, depuis le dossier racine de l'ancienne suite :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
```

Vérifier que le conteneur existe :

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep tpmanager
```

Créer une copie SQLite cohérente depuis le conteneur :

```bash
docker compose exec -T tpmanager-app python - <<'PY'
import sqlite3
from pathlib import Path

src = Path('/data/tpmanager/tp-manager.sqlite3')
dst = Path('/data/tpmanager/tp-manager-export.sqlite3')

if not src.exists():
    raise SystemExit(f'Base introuvable : {src}')

source = sqlite3.connect(str(src))
target = sqlite3.connect(str(dst))
source.backup(target)
target.close()
source.close()
print(f'Sauvegarde créée : {dst}')
PY
```

Copier ensuite la base exportée vers `/home` :

```bash
mkdir -p /home/lp-migration
cp ./tpmanager-db/data/tp-manager-export.sqlite3 /home/lp-migration/tp-manager.sqlite3
```

Créer en plus une archive du dossier complet TP Manager, utile si des médias ou fichiers associés existent :

```bash
tar -czf /home/lp-migration/tpmanager-db-data.tar.gz -C ./tpmanager-db/data .
```

À ce stade, les fichiers importants sont :

```text
/home/lp-migration/tp-manager.sqlite3
/home/lp-migration/tpmanager-db-data.tar.gz
```

---

## 5. Méthode simple si la suite ancienne est arrêtée

Si l'ancienne suite est arrêtée proprement :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
docker compose down
mkdir -p /home/lp-migration
cp ./tpmanager-db/data/tp-manager.sqlite3 /home/lp-migration/tp-manager.sqlite3
tar -czf /home/lp-migration/tpmanager-db-data.tar.gz -C ./tpmanager-db/data .
```

Cette méthode est acceptable uniquement si les conteneurs sont arrêtés.

---

## 6. Restauration dans la nouvelle version

La restauration doit idéalement être faite **avant le premier démarrage définitif** de la nouvelle suite.

Depuis le nouveau dossier extrait dans `/home` :

```bash
cd /home/lp-gestion-atelier-ep-suite-beta-v0.0.1
mkdir -p ./tpmanager-db/data
cp /home/lp-migration/tp-manager.sqlite3 ./tpmanager-db/data/tp-manager.sqlite3
```

Puis lancer l'installation :

```bash
chmod +x install.sh start.sh stop.sh upgrade.sh scripts/*.sh
./install.sh
```

Après démarrage, appliquer les migrations Django TP Manager sur la base récupérée :

```bash
docker compose exec tpmanager-app python manage.py migrate --noinput
```

Redémarrer TP Manager :

```bash
docker compose restart tpmanager-app
```

Tester ensuite :

```text
http://localhost:9000/tpmanager/
```

ou en production :

```text
https://nom.duckdns.org/tpmanager/
```

---

## 7. Restauration du dossier complet TP Manager

Si l'on veut restaurer la base et les fichiers associés :

```bash
cd /home/lp-gestion-atelier-ep-suite-beta-v0.0.1
mkdir -p ./tpmanager-db/data
tar -xzf /home/lp-migration/tpmanager-db-data.tar.gz -C ./tpmanager-db/data
```

Puis :

```bash
./install.sh
docker compose exec tpmanager-app python manage.py migrate --noinput
docker compose restart tpmanager-app
```

---

## 8. Vérifications après récupération

Depuis le dossier racine de la nouvelle suite :

```bash
docker compose ps
```

Vérifier que TP Manager tourne :

```bash
docker compose logs --tail=80 tpmanager-app
```

Vérifier la présence de la base côté hôte :

```bash
ls -lh ./tpmanager-db/data/tp-manager.sqlite3
```

Vérifier la présence de la base côté conteneur :

```bash
docker compose exec tpmanager-app ls -lh /data/tpmanager/tp-manager.sqlite3
```

Vérifier les migrations :

```bash
docker compose exec tpmanager-app python manage.py showmigrations
```

---

## 9. Erreurs fréquentes

### Commande lancée depuis le mauvais dossier

Symptôme :

```text
no configuration file provided: not found
```

Correction : revenir dans le dossier contenant `docker-compose.yml`.

```bash
cd /home/lp-gestion-atelier-ep-suite-beta-v0.0.1
```

### Mauvais nom de conteneur

Le bon service est :

```text
tpmanager-app
```

Ne pas confondre avec :

```text
tp-manager
TPManager
tp_manager
```

### Base copiée après initialisation d'une base neuve

Ce n'est pas bloquant, mais il faut arrêter le conteneur avant d'écraser la base :

```bash
docker compose stop tpmanager-app
cp /home/lp-migration/tp-manager.sqlite3 ./tpmanager-db/data/tp-manager.sqlite3
docker compose start tpmanager-app
docker compose exec tpmanager-app python manage.py migrate --noinput
```

### Base SQLite verrouillée

Si l'on copie directement la base pendant que TP Manager tourne, il peut y avoir un risque de fichier incohérent.

Méthode recommandée : utiliser la commande Python `sqlite3.backup()` depuis le conteneur, comme indiqué plus haut.

---

## 10. À prévoir dans une future version

Ajouter dans TP Manager ou LP Core :

- export web de la base TP Manager ;
- import web contrôlé ;
- sauvegarde/restauration sélective par module ;
- diagnostic de compatibilité de base ;
- message clair avant écrasement d'une base existante.
