# V2.1 — LP Core / Safety / PedaShop

## Corrections principales

- Correction de la synchronisation LP Core → PedaShop : endpoint interne exempté CSRF et protégé par `LP_CORE_API_TOKEN`.
- LP Core porte maintenant les magasins PedaShop visibles, droits, habilitations et certifications.
- Gestion individuelle depuis la fiche utilisateur LP Core.
- Gestion par lot avec filtres classe, formation, rôle et recherche.
- API LP Core enrichie : `pedashop_magasins` et `certifications`.
- PedaShop synchronise les magasins visibles depuis LP Core.
- Safety Manager : accueil public sans connexion, déclaration connectée obligatoire, affichage dynamique en 3 priorités, situations dangereuses hors DUERP ou DUERP.

## Après upgrade

```bash
docker compose build --no-cache lp-core-app pedashop-app safety-app
docker compose up -d --force-recreate lp-core-app pedashop-app safety-app
docker compose exec -T lp-core-app python manage.py migrate --noinput
docker compose exec -T pedashop-app python manage.py migrate --noinput
docker compose exec -T safety-app python manage.py makemigrations safety_manager
docker compose exec -T safety-app python manage.py migrate --noinput
docker compose exec -T lp-core-app python manage.py collectstatic --noinput
docker compose exec -T pedashop-app python manage.py collectstatic --noinput
docker compose exec -T safety-app python manage.py collectstatic --noinput
docker compose restart lp-core-app pedashop-app safety-app
```
