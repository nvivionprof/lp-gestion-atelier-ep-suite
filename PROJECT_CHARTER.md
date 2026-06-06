# Charte projet

## Nom du projet

LP Gestion Atelier EP Suite

## Nom technique recommandé

`lp-gestion-atelier-ep-suite`

## Public visé

- Lycées professionnels.
- Enseignants d’atelier.
- Magasiniers.
- Élèves.
- Administrateurs techniques.

## Finalité

Fournir une suite cohérente d’outils web permettant de gérer l’atelier, les ressources, les systèmes, les TP, la sécurité et les traces d’activité élèves.

## Règles de développement

- Code lisible et documenté.
- Nommage explicite.
- Migrations Django versionnées.
- Pas de secrets dans Git.
- Pas de données élèves réelles dans le dépôt.
- Documentation mise à jour avec les évolutions.
- Chaque ZIP de livraison doit indiquer s’il s’agit d’une mise à jour web ou d’une installation complète.

## Convention de version

Format conseillé :

```text
MAJEUR.MINEUR.CORRECTIF
```

Exemples :

```text
0.3.1
0.4.0
1.0.0
```

## Branches

- `main` : stable.
- `dev` : intégration.
- `feature/*` : fonctions.
- `fix/*` : corrections.
- `release/*` : préparation livraison.
