# System Manager — hiérarchie récursive et documents locaux

## Arborescence

- Un système sans parent est une racine.
- Un système peut contenir des sous-systèmes sans limite fonctionnelle de profondeur.
- Les boucles sont interdites par validation du modèle et par filtrage du formulaire.
- Chaque page permet d’ajouter un équipement local et un sous-système direct.
- La navigation existante parent/enfants est conservée.

## Documents

Un système affiche :

1. les documents de tous ses ancêtres, de la racine vers son parent ;
2. ses propres documents locaux.

Un document ajouté à un sous-système n’est jamais visible depuis son parent ni
depuis un système frère. Il devient uniquement visible pour ce sous-système et
ses descendants.

Les lignes héritées indiquent leur système source. Leur administration s’effectue
depuis la fiche de ce système source.

## Ouverture des rubriques

- Une rubrique contenant au moins un document visible est ouverte au chargement.
- Une rubrique vide reste repliée.
- Les boutons **Tout dérouler** et **Tout réduire** modifient l’affichage courant.

## Base de données et LP Core

Ce correctif ne crée aucune nouvelle table et ne modifie aucun champ de base de
données. La migration `0007_system_hierarchy_equipment` reste la seule migration
nécessaire pour la hiérarchie et les équipements. LP Core n’est pas modifié.
