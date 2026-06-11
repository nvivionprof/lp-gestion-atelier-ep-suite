# Changelog

## V1.0.1 restructure suite

- Reprise de la dernière version ToolMag fournie.
- Séparation en `lp-core-app` et `toolmag-app`.
- Port 8000 pour l'administration racine LP Core.
- Port 8001 pour ToolMag.
- Base élèves centralisée dans LP Core.
- Synchronisation des utilisateurs vers ToolMag.
- Base ToolMag autonome conservée.
- Scripts d'installation, sauvegarde, restauration et mise à jour sûre.
- Base Excel fournie dans `imports/`.
- Base démo ToolMag fournie dans `demo/`.

## V1.3.0

- Ajout de `upgrade.sh` pour mise à jour sans écrasement des bases.
- Ajout de `scripts/backup_before_upgrade.sh`.
- Ajout de `scripts/migrate_all.sh`.
- Ajout de `scripts/check_health.sh`.
- Ajout de `scripts/restore_pre_upgrade.sh`.
- Réinitialisation mot de passe ToolMag : reprise automatique du code utilisateur sélectionné depuis la fiche.
- Accueil ToolMag : actualisation automatique toutes les 15 secondes.


## V1.5.0 — Identité visuelle cohérente

- Intégration des logos fournis dans les tuiles LP Core.
- Remplacement du logo ToolMag dans le bandeau supérieur par le nouveau visuel fourni.
- Ajout du logo Safety Manager dans le bandeau du module Safety.
- Refonte visuelle Safety Manager pour se rapprocher de l’ergonomie ToolMag : fond gris clair, cartes blanches, bandeau supérieur bordeaux, boutons et accents bordeaux.
- Aucun changement volontaire de structure de base de données.
- Compatible avec la procédure d’upgrade-safe : données et `.env` préservés.
