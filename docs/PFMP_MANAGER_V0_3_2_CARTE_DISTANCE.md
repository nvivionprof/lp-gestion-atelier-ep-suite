# PFMP Manager — Bêta V0.3.2 carte et distance

## Type de livraison

Évolution complète du module PFMP Manager, installable comme mise à jour SSH sur une installation V0.3.1a.

## Objectif

Ajouter une vue géographique des entreprises PFMP :

- affichage des entreprises géolocalisées sur une carte Leaflet / OpenStreetMap ;
- ajout des champs latitude et longitude dans le formulaire entreprise ;
- création d’un point élève par clic sur la carte ou géolocalisation navigateur ;
- filtrage côté navigateur par distance maximale en kilomètres ;
- liste des entreprises sans coordonnées GPS pour les compléter progressivement ;
- endpoint GeoJSON `/pfmp/api/entreprises.geojson/` pour une future intégration GeoDjango/PostGIS.

## Choix technique

GeoDjango complet n’est pas activé dans cette version, car il impose une base spatiale et des bibliothèques système GEOS/GDAL/PROJ. La suite actuelle utilise SQLite simple pour PFMP. Cette version conserve donc les champs latitude/longitude déjà présents et applique un calcul Haversine côté interface.

## Évolution future recommandée

Quand le module PFMP sera stabilisé :

1. migrer PFMP de SQLite vers PostgreSQL ;
2. activer PostGIS ;
3. ajouter `django.contrib.gis` ;
4. remplacer latitude/longitude par un `PointField` ou ajouter un champ spatial `location` ;
5. faire le filtrage par distance côté base avec index spatial.

## Fichiers modifiés

- `pfmp-app/pfmp_manager/forms.py`
- `pfmp-app/pfmp_manager/views.py`
- `pfmp-app/pfmp_manager/urls.py`
- `pfmp-app/pfmp_manager/templates/pfmp_manager/map.html`
- `pfmp-app/pfmp_manager/templates/pfmp_manager/company_detail.html`
- `pfmp-app/pfmp_manager/static/pfmp_manager/pfmp.css`
- `manifest.json`

## Après installation

Redémarrer PFMP et la passerelle :

```bash
docker compose up -d --build pfmp-app lp-gateway
```

Tester :

```bash
curl -I http://localhost:9000/pfmp/carte/
curl http://localhost:9000/pfmp/api/entreprises.geojson/
```
