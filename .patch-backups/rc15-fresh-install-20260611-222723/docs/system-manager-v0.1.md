# System Manager V0.1 — Gestion des systèmes pédagogiques

## Objectif

Ce module ajoute à la suite LP Gestion Atelier EP une application Django dédiée aux systèmes pédagogiques :

- base des systèmes avec photo, zone, sous-zone, formations et niveaux concernés ;
- classeur documentaire par rubriques ;
- réservation des systèmes par créneaux horaires avec vue calendrier semaine ;
- QR code par système ;
- prise de poste et restitution de poste avec check configurable ;
- historique complet d'utilisation ;
- signalement d'anomalie et changement d'état du système ;
- synchronisation des utilisateurs et formations depuis LP Core.

## Service Docker

Le service ajouté est :

```bash
docker compose up -d system-manager-app
```

Port par défaut : `9004`.

URL par défaut :

```text
http://localhost:9004
```

## Installation complète

Depuis la racine de la suite :

```bash
./install.sh
```

Le script construit et démarre désormais :

- LP Core ;
- ToolMag ;
- Safety Manager ;
- PedaShop ;
- System Manager.

## Mise à jour d'une installation existante

```bash
docker compose build system-manager-app lp-core-app
docker compose up -d system-manager-app lp-core-app
./scripts/migrate_all.sh
```

Puis ouvrir LP Core : la tuile **System Manager** apparaît dans les modules de la suite.

## Commandes utiles

```bash
# Initialiser les référentiels du module
docker compose exec -T system-manager-app python manage.py seed_system_manager

# Synchroniser les utilisateurs et formations LP Core
docker compose exec -T system-manager-app python manage.py sync_lp_core_users

# Migrations seules
docker compose exec -T system-manager-app python manage.py migrate --noinput
```

## Droits

Les utilisateurs sont synchronisés depuis LP Core.

- utilisateur / élève : consultation, prise de poste, restitution ;
- professeur / magasinier / responsable : réservation, création/modification système, documents, checks ;
- admin / responsable / SYSTEM_ADMIN / CORE_ADMIN : paramétrage et synchronisation.

## Données techniques principales

Tables principales :

- `EducationalSystem` ;
- `WorkshopZone` ;
- `WorkshopSubZone` ;
- `Formation` ;
- `Niveau` ;
- `SystemDocument` ;
- `DocumentCategory` ;
- `CheckItem` ;
- `Reservation` ;
- `WorkSession` ;
- `CheckResponse` ;
- `SystemAnomaly` ;
- `SystemUser`.

## Limites V0.1

- Le module TP n'est pas encore développé : les réservations stockent `tp_code` et `tp_titre` pour préparer la liaison future.
- Les réservations groupées multi-systèmes et récurrentes sont prévues en V1.
- La vue calendrier est volontairement simple et sans dépendance JavaScript externe.
