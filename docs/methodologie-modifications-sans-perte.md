# Méthodologie de modification sans perte de données

## Règle centrale

Le code et les données sont séparés.

- Code : `lp-core-app/`, `toolmag-app/`, futurs modules.
- Données : `lp-core-db/data/`, `toolmag-db/data/`.

Une mise à jour ne doit jamais remplacer les dossiers `*-db/data`.

## Cycle recommandé

1. Sauvegarde complète :

```bash
./scripts/backup_all.sh
```

2. Copie de travail ou branche Git :

```bash
git checkout -b modif-toolmag-YYYYMMDD
```

3. Modification du module concerné uniquement.

4. Redémarrage du service :

```bash
docker compose build toolmag-app
docker compose up -d toolmag-app
docker compose exec -T toolmag-app python manage.py migrate --noinput
```

5. Test des fonctions métier :

- connexion LP Core ;
- import Excel ;
- synchronisation ToolMag ;
- emprunt ;
- retour ;
- affichage dynamique ;
- sauvegarde.

6. Validation ou retour arrière.

## Retour arrière

Les scripts de mise à jour créent une copie de l'ancien code dans `versions/`.

Les données peuvent être restaurées depuis `backups/`.

## Règles pour futurs modules

Chaque futur logiciel doit avoir :

```text
nommodule-app/
nommodule-db/data/
```

Il doit récupérer les utilisateurs via l'API LP Core, puis stocker localement seulement ce qui lui est nécessaire.
