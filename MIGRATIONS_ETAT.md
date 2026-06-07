# État des migrations — Bêta 2 V0.0.1

Ce fichier doit être mis à jour à chaque modification de modèle Django.

## LP Core

- Migrations historiques conservées.
- `PublicSuiteSettings` conserve les anciens champs de ports en base pour compatibilité, mais l’interface ne les expose plus.
- Le mode d’exposition fonctionnel est `reverse_proxy` / passerelle unique.

## ToolMag

- Migrations historiques conservées.
- À surveiller lors du futur chantier exports PDF anonymisés / non anonymisés.

## Safety Manager

- Migrations historiques conservées.
- À surveiller lors du futur chantier évaluations IA / exports.

## PedaShop

- Migrations historiques conservées.
- À surveiller lors du futur chantier évaluations IA / exports.

## System Manager

- Migrations historiques conservées jusqu’aux évolutions documents, checks, anomalies, affichage dynamique et droits temporaires.
- Points sensibles : modèles de réservation, modèles de checks, anomalies et documents versionnés.
- Avant toute migration : tester `python manage.py makemigrations --check --dry-run`.

## TP Manager

- Migrations historiques conservées.
- À surveiller lors de la synchronisation TP vers System Manager.

## PFMP Manager

- Migrations historiques conservées.
- À surveiller lors de futures évolutions carte / entreprises / conventions.

## Commandes de contrôle

```bash
docker compose exec lp-core-app python manage.py showmigrations
docker compose exec system-manager-app python manage.py showmigrations
docker compose exec tpmanager-app python manage.py showmigrations
```

Contrôle de cohérence avant livraison :

```bash
docker compose exec lp-core-app python manage.py makemigrations --check --dry-run
docker compose exec system-manager-app python manage.py makemigrations --check --dry-run
```
