# LP Gestion Atelier EP Suite — V0.3.3 System Manager

## Type de mise à jour

Mise à jour SSH recommandée. Cette version modifie LP Core et System Manager, ajoute des migrations de base et nécessite un rebuild ciblé.

## Évolutions principales

- Fiche système restructurée en huit conteneurs documentaires :
  01 Présentation/CCTP/analyse fonctionnelle ; 02 plans/schémas/notes ; 03 documentations ; 04 programmes ; 05 TP/TD ; 06 sécurité/risques/consignation ; 07 maintenance/dépannage ; 08 historique.
- Sous-catégories proposées et créées automatiquement par migration.
- Liens TP/TD ajoutables manuellement, préparés pour synchronisation TP Manager.
- Liens sécurité/risques/consignation ajoutables manuellement, préparés pour synchronisation Safety Manager.
- Page maintenance/GMAO : intervention, dépannage, hypothèses, contrôles, conditions, valeurs attendues/mesurées, conclusion, EPI/ECS/EIS, mesures, mise en service et contrôles périodiques.
- Zones photo/dessin tablette : photo/appareil photo, quadrillage, dessin direct sur tablette.
- LP Core : blocs atelier avec formations concernées et demi-journées/créneaux paramétrables.
- System Manager : réservation par bloc atelier entre deux dates, avec création automatique par demi-journée et filtrage des réservations par zone, formation, niveau, classe et statut.
- Page de sauvegarde/import du module System Manager avec export ZIP et accès à l’import/export SQL.

## Installation avec archive dans /home/user

```bash
cd /home/user
unzip lp-gestion-atelier-ep-suite-patch-v0.3.3-system-manager-gmao-blocs.zip -d patch-v0.3.3-system-manager
cd patch-v0.3.3-system-manager
chmod +x scripts/apply_update_v0.3.3_system_manager.sh
./scripts/apply_update_v0.3.3_system_manager.sh /home/user/docker/lp-gestion-atelier-ep-suite
```

## Installation manuelle

```bash
cd /home/user/docker/lp-gestion-atelier-ep-suite
mkdir -p /home/user/backups-lp-suite
BACKUP_NAME="lp-suite-before-v0.3.3-system-manager-$(date +%Y%m%d-%H%M%S)"
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

rsync -a /home/user/patch-v0.3.3-system-manager/ ./ \
  --exclude '.env' \
  --exclude 'lp-core-db/data/' \
  --exclude 'toolmag-db/data/' \
  --exclude 'safety-db/data/' \
  --exclude 'pedashop-db/data/' \
  --exclude 'system-manager-db/data/' \
  --exclude 'tpmanager-db/data/' \
  --exclude 'pfmp-db/data/' \
  --exclude 'backups/' \
  --exclude 'ssl/'

docker compose up -d --build lp-core-app system-manager-app lp-gateway
docker compose exec -T lp-core-app python manage.py migrate --noinput
docker compose exec -T system-manager-app python manage.py migrate --noinput
docker compose restart lp-core-app system-manager-app lp-gateway
```

## Points à tester

- LP Core : `/blocs-atelier/`
- System Manager : `/system/parametrage/`
- Fiche système : `/system/systemes/<id>/`
- Réservation par bloc : `/system/reservations/bloc/creer/`
- Sauvegarde module : `/system/sauvegarde/`
