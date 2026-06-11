# LP Gestion Atelier EP Suite — V0.0.1-RC13

## Objet

RC13 réintroduit l’historique PFMP Manager demandé : page `/pfmp/historique/`, lien de menu, filtres dynamiques avec suggestions et export CSV.

## Contenu

- Historique consolidé des affectations PFMP.
- Historique des démarches élèves.
- Historique des annonces entreprises.
- Filtres : recherche libre, élève, entreprise, période, formation, statut, type d’événement.
- Droits : professeur/admin voient tout ; élève voit uniquement son propre historique.
- Export CSV.

## Déploiement

Upgrade semi-rapide conseillé :

```bash
lp-suite upgrade rc
```
