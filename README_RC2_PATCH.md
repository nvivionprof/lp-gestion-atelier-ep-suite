# Patch LP Gestion Atelier EP Suite — V0.0.1-RC2

Ce ZIP n'est pas une sauvegarde de données. Il applique les correctifs RC2 sur le dépôt Git local.

Procédure courte :

```bash
cd /chemin/vers/lp-gestion-atelier-ep-suite
unzip /chemin/vers/lp-gestion-atelier-ep-suite-rc2-patch.zip
bash apply_rc2_fixes.sh
bash -n install.sh
bash -n scripts/configure_install_env.sh
bash -n scripts/set_env_value.sh
bash -n scripts/full_backup.sh
git status
git add -A
git commit -m "Passe en V0.0.1-RC2 avec installateur PostgreSQL corrige"
git push origin rc
```

Correctifs intégrés :

- écriture robuste du `.env`, sans `sed` fragile ;
- validation `.env` avant Docker Compose ;
- `docker compose --env-file .env` utilisé partout ;
- création automatique des bases PostgreSQL manquantes ;
- `pfmp-app/docker-entrypoint.sh` accepte les commandes `manage.py` ;
- `collectstatic` PFMP relancé correctement ;
- sauvegarde complète vérifie `zip`, `sha256sum`, `docker` avant de commencer ;
- ajout d'actions web via `suite-admin-agent` : migrations module, collectstatic module, sync module/tous, restart module, logs module ;
- page LP Core supervision bases enrichie avec actions.
