# RC18 — robustesse migrations / auto-réparation

Type : **upgrade classique / maintenance corrective**.

## Objectif

Éviter les corrections manuelles répétées lorsque Django rencontre un état hybride :

- colonne SQL déjà créée mais migration non enregistrée ;
- table SQL déjà créée mais migration non enregistrée ;
- migration PFMP RC16 partiellement appliquée.

## Fichiers ajoutés ou modifiés

- `scripts/migrate_all.sh` : relance automatiquement une réparation connue si un module échoue en migration.
- `scripts/repair_migration_state.sh` : réparations connues LP Core / PFMP.
- `pfmp-app/pfmp_manager/schema_repair.py` : réparation idempotente du schéma PFMP RC16.
- `pfmp-app/pfmp_manager/management/commands/repair_pfmp_rc16_schema.py` : commande Django utilisable à la main.
- `pfmp-app/pfmp_manager/migrations/0002_rc16_pfmp_complete.py` : migration rendue idempotente via `SeparateDatabaseAndState`.

## Utilisation serveur

```bash
bash scripts/migrate_all.sh
```

En cas de besoin manuel :

```bash
bash scripts/repair_migration_state.sh all
bash scripts/migrate_all.sh
```

Pour PFMP seul :

```bash
docker compose --env-file .env exec -T pfmp-app python manage.py repair_pfmp_rc16_schema
```
