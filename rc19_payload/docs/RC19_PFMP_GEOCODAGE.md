# V0.0.1-RC19 — PFMP géocodage entreprises

Type : **upgrade classique / maintenance PFMP Manager**.

Cette RC ajoute le géocodage applicatif des entreprises PFMP quand le fichier XLSX ne fournit pas encore `latitude` et `longitude`.

## Principe

- L'import XLSX reste possible sans coordonnées GPS.
- Les entreprises sans coordonnées sont marquées `A_GEOCODER`.
- La carte affiche les entreprises ayant latitude/longitude.
- Le géocodage peut être lancé depuis l'interface web ou en ligne de commande.
- Les contacts peuvent être géocodés seulement si leur adresse personnelle est explicitement activée comme point de proximité.
- Les adresses personnelles des contacts ne doivent jamais être visibles par les élèves.

## Page web

```text
/pfmp/entreprises/geocodage/
```

## Commandes serveur

```bash
# Entreprises sans coordonnées
docker compose --env-file .env exec -T pfmp-app python manage.py geocode_pfmp_companies --missing-only

# Limiter à 20 pour test
docker compose --env-file .env exec -T pfmp-app python manage.py geocode_pfmp_companies --missing-only --limit 20

# Relancer les échecs / ambiguïtés
docker compose --env-file .env exec -T pfmp-app python manage.py geocode_pfmp_companies --retry-failed

# Forcer le recalcul
docker compose --env-file .env exec -T pfmp-app python manage.py geocode_pfmp_companies --force

# Inclure les contacts autorisés comme points de proximité
docker compose --env-file .env exec -T pfmp-app python manage.py geocode_pfmp_companies --missing-only --include-contacts
```

## Script simplifié

```bash
bash scripts/pfmp_rc19_geocode_companies.sh missing
bash scripts/pfmp_rc19_geocode_companies.sh retry
bash scripts/pfmp_rc19_geocode_companies.sh force
bash scripts/pfmp_rc19_geocode_companies.sh missing 20 contacts
```

## Statuts

```text
A_GEOCODER : coordonnées absentes
OK         : coordonnées trouvées
AMBIGU     : plusieurs résultats possibles, coordonnées du premier résultat stockées
ECHEC      : aucun résultat fiable ou erreur réseau
MANUEL     : coordonnées saisies / validées manuellement
```

## Attention réseau

Le géocodage par défaut utilise Nominatim / OpenStreetMap. Si le serveur n'a pas Internet, les entreprises restent importées mais passent en `ECHEC` ou restent `A_GEOCODER`. Le traitement pourra être relancé plus tard.
