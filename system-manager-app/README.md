# System Manager — module systèmes pédagogiques

Application Django intégrée à LP Gestion Atelier EP Suite.

Fonctions V0.1 :

- création et gestion des systèmes pédagogiques ;
- localisation zone / sous-zone ;
- photo principale ;
- formations et niveaux concernés ;
- classeur documentaire ;
- QR code de prise de poste ;
- check personnalisable ;
- réservation calendrier ;
- historique prise / restitution ;
- anomalies ;
- synchronisation LP Core.

## Démarrage Docker

Depuis la racine de la suite :

```bash
docker compose build system-manager-app
docker compose up -d system-manager-app
```

Puis :

```bash
docker compose exec -T system-manager-app python manage.py migrate --noinput
docker compose exec -T system-manager-app python manage.py seed_system_manager
docker compose exec -T system-manager-app python manage.py sync_lp_core_users
```

Port par défaut : `9004`.
