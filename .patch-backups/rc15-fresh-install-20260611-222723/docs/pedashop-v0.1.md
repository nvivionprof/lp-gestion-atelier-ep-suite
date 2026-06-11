# PedaShop V0.1 — module consommables multi-site

Cette version ajoute un module séparé `pedashop-app` au port 9003.

## Principes retenus

- Le module est indépendant de ToolMag.
- Les utilisateurs sont synchronisés depuis LP Core.
- Le multi-magasin est natif.
- Le stock est stocké dans `StockArticleMagasin`, pas dans `Article`.
- Les mouvements de stock sont historisés.
- Les données sont sauvegardées dans `pedashop-db/data/`.

## Fonctions V0 intégrées

- Gestion articles.
- Gestion magasins.
- Gestion emplacements.
- Stock par article et magasin.
- Import Excel avec prévisualisation.
- Demande de consommables.
- Préparation / distribution définitive ou temporaire.
- Retour temporaire.
- Réservations avec blocage stock.
- Alertes stock minimum.
- Transferts internes.
- Historique des mouvements.
- Exports PDF simples.

## Mise à jour sans perte

`upgrade.sh` exclut `pedashop-db/data/` comme les autres bases métier.

## Commentaires pédagogiques

Le code ajouté contient des commentaires dans les fichiers métier principaux : modèles, services, vues, synchronisation et settings.
