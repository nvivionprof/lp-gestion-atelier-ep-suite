# Release — LP Gestion Atelier EP Suite Bêta 2 V0.0.1

Cette release est une rebase de stabilisation en vue d’un dépôt Git.

## Base reprise

- V0.4.0c propre consolidée.

## Changement fonctionnel principal

LP Core ne propose plus la configuration de ports publics par module dans `URLs / HTTPS`. La suite est considérée comme publiée derrière une passerelle unique :

```text
https://domaine.duckdns.org/
https://domaine.duckdns.org/system/
https://domaine.duckdns.org/toolmag/
```

## Installation

Installation complète/reprise SSH recommandée.

## Attention

Docker n’a pas été exécuté dans l’environnement de génération. Les vérifications réalisées sont statiques : compilation Python, YAML, scripts shell et cohérence d’archive.
