# ToolMag Bêta V1.0.1 - Production

## Changements

- Import Excel utilisateurs : création contrôlée des classes inconnues.
  - En simulation, ToolMag liste les classes inconnues détectées.
  - En application réelle, les classes sont créées automatiquement dans la table `Classe pédagogique`.
- Ajout du logo ToolMag Éducation dans le bandeau.
- Ajout du crédit VIVION Nicolas et de la licence Creative Commons BY-SA 4.0 dans le pied de page.
- Regroupement des fonctions réservées aux professeurs dans le menu déroulant `Fonctions admin`.
- Nouvelle table `SchoolClass` / `Classe pédagogique`.

## Mise à jour

```powershell
docker compose down
docker rm -f toolmag_web
docker compose build --no-cache
docker compose up -d
docker exec -it toolmag_web python manage.py migrate
docker exec -it toolmag_web python manage.py seed_demo
docker exec -it toolmag_web python manage.py generate_qr
```

## Vérification

```powershell
docker exec -it toolmag_web cat VERSION.txt
```

Résultat attendu :

```text
ToolMag Bêta V1.0.1 - Production — import contrôlé des classes, logo et fonctions admin regroupées — 2026-05-18
```
