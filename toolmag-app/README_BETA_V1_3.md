# ToolMag Bêta V1.3

Version : formations automatiques, compte prof de démonstration, création utilisateur depuis ToolMag, droits ponctuels de modification matériel, création/modification matériel hors Django admin.

## Comptes de démo après `seed_demo`

- `PROF-0001` / `prof1234` : prof admin/responsable, connecté automatiquement comme utilisateur et magasinier.
- `MAG-0001` / `mag1234` : magasinier.
- `USR-0001` / `user1234` : utilisateur.
- `USR-0002` / `user1234` : utilisateur.

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

## Nouveautés V1.3

- `Formation.code` devient libre et auto-généré depuis le nom si vide.
- Formation `STAFF` pour l’équipe pédagogique.
- Page `/utilisateurs/nouveau/` pour créer un utilisateur avec mot de passe provisoire.
- Page `/droits-materiel/` pour droits ponctuels de création/modification matériel par formation/classe/groupe.
- Pages ToolMag : `/materiels/nouveau/`, `/materiels/<CODE>/modifier/`, `/materiels/<CODE>/composants/`, `/materiels/<CODE>/documents/`.
