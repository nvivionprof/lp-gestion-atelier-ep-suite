# Installation / mise à jour V0.3.2 PFMP carte distance

Hypothèses serveur :

- archives ZIP déposées dans `/home/user/` ;
- projet Docker installé dans `/home/user/docker/lp-gestion-atelier-ep-suite`.

## Mise à jour recommandée depuis une version existante

```bash
cd /home/user
unzip lp-gestion-atelier-ep-suite-patch-v0.3.2-pfmp-carte-distance.zip -d patch-v0.3.2-pfmp-carte-distance

cd /home/user/docker/lp-gestion-atelier-ep-suite
mkdir -p /home/user/backups-lp-suite
BACKUP_NAME="lp-suite-before-v0.3.2-pfmp-$(date +%Y%m%d-%H%M%S)"
tar --exclude='./lp-core-db/data' \
    --exclude='./toolmag-db/data' \
    --exclude='./safety-db/data' \
    --exclude='./pedashop-db/data' \
    --exclude='./system-manager-db/data' \
    --exclude='./tpmanager-db/data' \
    --exclude='./pfmp-db/data' \
    --exclude='./backups' \
    --exclude='./ssl' \
    -czf "/home/user/backups-lp-suite/${BACKUP_NAME}.tar.gz" .

docker compose down
rsync -a /home/user/patch-v0.3.2-pfmp-carte-distance/ ./
docker compose up -d --build pfmp-app lp-gateway
```

Contrôles :

```bash
curl -I http://localhost:9000/pfmp/carte/
curl http://localhost:9000/pfmp/api/entreprises.geojson/
```

## Installation complète depuis l’archive full

À n’utiliser que pour une nouvelle installation ou pour réappliquer toute l’arborescence en excluant les données existantes.

```bash
cd /home/user
unzip lp-gestion-atelier-ep-suite-beta-v0.3.2-pfmp-carte-distance.zip -d lp-suite-v0.3.2-full

cd /home/user/docker/lp-gestion-atelier-ep-suite
docker compose down

rsync -a --delete \
  --exclude '.env' \
  --exclude 'lp-core-db/data/' \
  --exclude 'toolmag-db/data/' \
  --exclude 'safety-db/data/' \
  --exclude 'pedashop-db/data/' \
  --exclude 'system-manager-db/data/' \
  --exclude 'tpmanager-db/data/' \
  --exclude 'pfmp-db/data/' \
  --exclude 'backups/' \
  --exclude 'ssl/' \
  /home/user/lp-suite-v0.3.2-full/ ./

docker compose up -d --build pfmp-app lp-gateway
```

## Remarque

Cette mise à jour ne nécessite pas de migration de base : les champs `latitude` et `longitude` existaient déjà dans le modèle PFMP. Ils sont maintenant visibles dans le formulaire entreprise et exploités par la carte.
