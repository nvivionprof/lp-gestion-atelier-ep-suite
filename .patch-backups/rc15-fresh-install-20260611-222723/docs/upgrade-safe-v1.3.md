# Upgrade-safe — LP Gestion Atelier EP Suite V1.3

## Objectif

Cette version ajoute une procédure de mise à jour sûre : le code peut évoluer, mais les données métier ne sont pas écrasées.

Données protégées :

```text
.env
lp-core-db/data/
toolmag-db/data/
backups/
imports/*.xlsx
imports/*.csv
```

## Mise à jour recommandée

Depuis le dossier de la version installée :

```bash
cd /home/ecoquartier/LP_Gestion_Atelier_EP/lp-gestion-atelier-ep-suite
./upgrade.sh /chemin/lp-gestion-atelier-ep-suite-toolmag-v1.3.zip
```

Le script effectue automatiquement :

1. lecture de la version installée ;
2. sauvegarde pré-upgrade ;
3. extraction de la nouvelle archive dans un dossier temporaire ;
4. copie du code sans écraser les bases ;
5. rebuild Docker ;
6. migrations Django ;
7. synchronisation LP Core → ToolMag ;
8. contrôle HTTP des applications.

## Restauration en cas d'échec

```bash
./scripts/restore_pre_upgrade.sh
```

Le dernier dossier de sauvegarde pré-upgrade est mémorisé dans :

```text
backups/LAST_PRE_UPGRADE_BACKUP.txt
```

## Modifications fonctionnelles V1.3

- réinitialisation de mot de passe : le code utilisateur sélectionné depuis une fiche utilisateur est repris dans le formulaire ;
- ToolMag accueil : actualisation automatique toutes les 15 secondes ;
- procédure `upgrade.sh` avec sauvegarde et migration automatiques.
