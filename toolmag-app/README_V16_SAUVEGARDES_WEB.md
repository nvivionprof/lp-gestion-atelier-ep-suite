# ToolMag V16 — Sauvegardes et restauration web

## Fonctions ajoutées

- Page `/admin-toolmag/sauvegardes/` réservée aux super admins ToolMag : rôle `RESPONSABLE` ou `ADMIN`, connecté comme magasinier.
- Bouton de sauvegarde manuelle.
- Liste des sauvegardes disponibles.
- Téléchargement d'une sauvegarde.
- Restauration web avec confirmation forte : il faut taper `RESTAURER`.
- Création automatique d'une sauvegarde `pre-restore` avant toute restauration.
- Suppression web uniquement pour les sauvegardes manuelles et pré-restauration.
- Les sauvegardes automatiques restent gérées par le service Docker `backup` avec 7 jours de rétention.

## Types de sauvegarde

- `auto-toolmag-YYYYMMDD-HHMMSS.tar.gz` : sauvegarde automatique, purgée après 7 jours.
- `manual-toolmag-YYYYMMDD-HHMMSS.tar.gz` : sauvegarde manuelle, conservée jusqu'à suppression volontaire.
- `pre-restore-toolmag-YYYYMMDD-HHMMSS.tar.gz` : sauvegarde créée automatiquement avant restauration, conservée jusqu'à suppression volontaire.

## Commandes utiles

Créer une sauvegarde manuelle par commande :

```bash
python manage.py backup_toolmag --type manual --note "avant import élèves"
```

Restaurer par commande :

```bash
python manage.py restore_toolmag NOM_DU_BACKUP.tar.gz
```

