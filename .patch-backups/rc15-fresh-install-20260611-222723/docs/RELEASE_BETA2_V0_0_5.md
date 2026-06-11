# LP Gestion Atelier EP Suite — beta2-v0.0.5

## Nature de version

Cette version est une **installation / update / upgrade SSH-Git**. Les mises à jour applicatives par interface web sont abandonnées.

LP Core conserve en revanche un rôle de supervision et d'exploitation des données :

- sauvegarde PostgreSQL par module ;
- sauvegarde PostgreSQL totale ;
- restauration PostgreSQL par module depuis une sauvegarde serveur ou un ZIP uploadé ;
- restauration PostgreSQL totale depuis une sauvegarde serveur ou un ZIP uploadé ;
- sauvegarde complète de reprise après crash incluant dumps PostgreSQL, médias, imports, SSL, `.env` et métadonnées.

## Règle de sécurité

L'interface web ne modifie pas le code applicatif et ne lance pas de mise à jour logicielle. Elle peut seulement demander à `suite-admin-agent` des actions prédéfinies de sauvegarde/restauration des données.

Les sauvegardes restaurées sont contrôlées :

- extension `.zip` obligatoire ;
- chemins absolus et `../` interdits ;
- `manifest.json` obligatoire ;
- `checksums.sha256` vérifié quand présent ;
- module restauré limité à une liste blanche ;
- confirmation textuelle `RESTAURER` obligatoire côté LP Core ;
- journalisation des jobs agent.

## Scripts ajoutés

- `scripts/postgres/db_common.sh`
- `scripts/postgres/export_database_dumps.sh`
- `scripts/postgres/backup_database.sh`
- `scripts/postgres/restore_database_backup.sh`

## Usage SSH

Sauvegarde d'un module :

```bash
./scripts/postgres/backup_database.sh toolmag manual
```

Sauvegarde de toutes les bases :

```bash
./scripts/postgres/backup_database.sh all manual
```

Restauration :

```bash
./scripts/postgres/restore_database_backup.sh backups/databases/manual/lp-suite-db-all-YYYYMMDD-HHMMSS.zip
```

## Usage Web

LP Core > Sauvegardes :

- choisir un module ou `Toutes les bases` ;
- lancer une sauvegarde base ;
- restaurer une sauvegarde serveur ;
- ou déposer une archive ZIP de sauvegarde base et confirmer la restauration.
