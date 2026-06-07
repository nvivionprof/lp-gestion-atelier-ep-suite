# Migration vers Git — LP Gestion Atelier EP Suite

## Objectif

Passer d’une gestion par ZIP successifs à une gestion par dépôt Git structuré.

## Dépôt recommandé

Nom possible :

```text
lp-gestion-atelier-ep-suite
```

Visibilité recommandée au départ : privé.

## Première initialisation locale

Depuis le dossier de la suite :

```bash
cd /home/user/docker/lp-gestion-atelier-ep-suite
git init
git add .
git commit -m "Initial import - Beta 2 V0.0.1"
```

## Connexion à GitHub

Créer le dépôt vide sur GitHub, puis :

```bash
git branch -M main
git remote add origin https://github.com/<COMPTE>/<DEPOT>.git
git push -u origin main
```

## Règle importante

Ne jamais versionner :

- `.env` ;
- bases SQLite réelles ;
- médias élèves / photos / documents ;
- certificats ;
- sauvegardes ;
- ZIP générés.

Ces éléments sont exclus dans `.gitignore`.

## Workflow recommandé

```bash
git checkout -b feature/nom-court
# modifications
git status
git diff
git add fichiers_modifies
git commit -m "Description claire"
git checkout main
git merge feature/nom-court
```

## Archives ZIP

Une archive ZIP de livraison doit toujours être générée depuis un commit propre, jamais depuis un dossier modifié manuellement sans commit.
