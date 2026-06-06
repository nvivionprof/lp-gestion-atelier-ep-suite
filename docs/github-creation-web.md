# Création du dépôt GitHub depuis l’interface web

## 1. Créer le dépôt vide

Sur GitHub :

1. Cliquer sur **+** en haut à droite.
2. Choisir **New repository**.
3. Renseigner :
   - **Repository name** : `lp-gestion-atelier-ep-suite`
   - **Description** : `Suite web modulaire de gestion d’atelier pédagogique, outillage, sécurité, ressources, TP et compétences élèves.`
   - **Visibility** : `Public` si le projet doit être public.
4. Ne pas cocher automatiquement README, `.gitignore` ou licence si tu importes cette archive complète.
5. Cliquer sur **Create repository**.

## 2. Importer cette archive

Méthode simple depuis l’interface GitHub :

1. Ouvrir le dépôt vide.
2. Cliquer sur **uploading an existing file**.
3. Déposer tous les fichiers et dossiers contenus dans `lp-gestion-atelier-ep-suite/`.
4. Mettre comme message de commit :

```text
Initialisation du dépôt LP Gestion Atelier EP Suite
```

5. Cliquer sur **Commit changes**.

## 3. Méthode propre avec Git en local

Dans le dossier contenant les fichiers :

```bash
git init
git add .
git commit -m "Initialisation du dépôt LP Gestion Atelier EP Suite"
git branch -M main
git remote add origin https://github.com/nvivionprof/lp-gestion-atelier-ep-suite.git
git push -u origin main
```

## 4. Paramétrage recommandé du dépôt

Dans **Settings** :

- **General > Features** : activer Issues et Discussions si souhaité.
- **Pull Requests** : autoriser `Squash merging`.
- **Branches** : créer une protection de branche sur `main` quand le projet aura plusieurs contributeurs.
- **Security** : activer Dependabot alerts.
- **Actions** : autoriser GitHub Actions.

## 5. Branches conseillées

```text
main        version stable ou livrable
dev         développement courant
feature/*   nouvelles fonctions
fix/*       corrections ciblées
release/*   préparation d’une version
```
