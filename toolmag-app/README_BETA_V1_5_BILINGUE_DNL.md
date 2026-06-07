# ToolMag Bêta V1.5 — interface bilingue FR/EN + glossaire DNL

## Ajouts

- Sélecteur de langue `FR | EN` dans le bandeau supérieur.
- Français par défaut.
- Traduction légère côté interface pour les menus, boutons, libellés et messages principaux ToolMag.
- Préparation Django `LocaleMiddleware` pour faciliter une internationalisation complète ultérieure.
- Page `Glossaire DNL` : `/dnl/glossaire/`.
- Export CSV du glossaire : `/dnl/glossaire/?format=csv`.
- Fichier CSV fourni dans `docs/glossaire_dnl_toolmag_fr_en.csv`.

## Limite volontaire

Cette V1.5 traduit l'interface. Les données saisies dans la base ne sont pas traduites automatiquement : catégories, emplacements, noms de matériels, composants, documents, commentaires.

## Mise à jour

```powershell
docker compose down
docker rm -f toolmag_web
docker compose build --no-cache
docker compose up -d
docker exec -it toolmag_web python manage.py migrate
```

## Vérification

```powershell
docker exec -it toolmag_web cat VERSION.txt
```

La page doit afficher :

```text
ToolMag Bêta V1.5 — interface bilingue FR/EN + glossaire DNL — 2026-05-18
```
