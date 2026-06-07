# ToolMag Bêta V1.8 — correction ajout rapide catégorie/emplacement

Cette version corrige l’erreur `NameError: Category is not defined` rencontrée lors de l’ajout rapide d’une catégorie ou d’un emplacement depuis la fiche matériel.

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

L’interface doit afficher `Bêta V1.8`.
