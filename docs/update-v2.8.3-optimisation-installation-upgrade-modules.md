# LP Gestion Atelier Suite v2.8.3 — Optimisation installation et mises à jour par module

## Objectif

Cette version optimise les installations et mises à jour de la suite, notamment lorsque seule une application change, par exemple TP Manager.

## Changements principaux

- `upgrade.sh` ne reconstruit plus les images Docker avec `--no-cache` par défaut.
- `--full-rebuild` reste disponible pour forcer une reconstruction complète sans cache.
- Ajout de `upgrade_module.sh` à la racine du projet.
- Extension de `scripts/update_module_safe.sh` à tous les modules principaux.
- `scripts/migrate_all.sh` accepte désormais `--module`, `--skip-seed` et `--skip-static`.
- Suppression de `makemigrations` côté serveur lors des mises à jour.
- Sauvegarde pré-upgrade fiabilisée pour inclure également System Manager et TP Manager.
- Journalisation horodatée des étapes de mise à jour.

## Mise à jour complète optimisée

```bash
./upgrade.sh /chemin/lp-gestion-atelier-ep-suite-v2.8.3-optimisation-installation-upgrade-modules.zip
```

Par défaut, le cache Docker est conservé.

Pour forcer une reconstruction complète plus lente :

```bash
./upgrade.sh --full-rebuild /chemin/lp-gestion-atelier-ep-suite-v2.8.3-optimisation-installation-upgrade-modules.zip
```

Pour éviter les seeds lors d’un correctif purement technique :

```bash
./upgrade.sh --skip-seed /chemin/archive.zip
```

## Mise à jour rapide d’un module

Exemple pour TP Manager :

```bash
./upgrade_module.sh tpmanager /chemin/lp-gestion-atelier-ep-suite-v2.8.3-optimisation-installation-upgrade-modules.zip
```

Modules acceptés :

- `lp-core`
- `toolmag`
- `safety`
- `pedashop`
- `system-manager`
- `tpmanager`
- `suite-admin-agent`

Exemple avec reconstruction sans cache uniquement pour TP Manager :

```bash
./upgrade_module.sh --full-rebuild tpmanager /chemin/archive.zip
```

Exemple sans seed :

```bash
./upgrade_module.sh --skip-seed tpmanager /chemin/archive.zip
```

## Migrations ciblées

```bash
./scripts/migrate_all.sh --module tpmanager
./scripts/migrate_all.sh --module pedashop --skip-seed
./scripts/migrate_all.sh --module toolmag --skip-static
```

## Protection des données

Les scripts conservent les dossiers de données existants :

- `lp-core-db/data/`
- `toolmag-db/data/`
- `safety-db/data/`
- `pedashop-db/data/`
- `system-manager-db/data/`
- `tpmanager-db/data/`

Une sauvegarde pré-upgrade est créée dans `backups/pre_upgrade_*` avant chaque mise à jour complète ou ciblée.

## Remarque importante

Cette version ne modifie pas la logique fonctionnelle de TP Manager V2. Elle optimise uniquement le cycle d’installation/mise à jour et prépare les futurs correctifs rapides par module.
