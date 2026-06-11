# Update Bêta V0.0.1 — RGPD et sauvegardes paramétrables

## Type de livraison

Installation complète / reprise SSH recommandée si appliquée en production.

## Ajouts

- Cahier des charges RGPD : `docs/CAHIER_DES_CHARGES_RGPD.md`.
- Paramètres de sauvegarde dans LP Core : heure, minute, durée, sauvegarde pré-MAJ obligatoire, blocage mise à jour si sauvegarde échoue, restauration web.
- Génération de `lp-core-db/data/backup-policy.env` depuis LP Core.
- Planificateur `suite-backup-scheduler` qui relit ce fichier à chaque boucle.
- Conservation par défaut : 7 jours glissants pour les quotidiennes, manuelles et pré-MAJ conservées sans suppression automatique.
- Interface LP Core listant les sauvegardes présentes sur le serveur via `suite-admin-agent`.
- Restauration d’une sauvegarde existante sur le serveur depuis LP Core, avec confirmation `RESTAURER`.
- Mise à jour complète bloquée si la sauvegarde pré-MAJ échoue lorsque l’option est activée.

## Point d’attention

La restauration web reste réservée aux administrateurs LP Core. En cas d’incident majeur, le script SSH `scripts/restore_full_backup.sh` reste la référence de dernier recours.
