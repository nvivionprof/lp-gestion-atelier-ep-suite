# Installation cible

## Pré-requis

- Serveur Linux ou WSL2 pour tests.
- Docker Engine.
- Docker Compose v2.
- Git.
- Accès réseau au port frontal unique `9000`.

## Installation locale

```bash
git clone https://github.com/nvivionprof/lp-gestion-atelier-ep-suite.git
cd lp-gestion-atelier-ep-suite
cp .env.example .env
docker compose up -d --build
```

## Comptes initiaux souhaités

LP Core devra créer automatiquement un utilisateur natif :

```text
identifiant : admin
mot de passe initial : admin
```

Le changement du mot de passe devra être obligatoire à la première connexion.

Ce compte ne doit pas être confondu avec le compte Django `/admin/`.

## Accès prévus

Tous les modules passent par le même port frontal :

```text
LP Core          http://localhost:9000/
ToolMag          http://localhost:9000/toolmag/
Safety Manager   http://localhost:9000/safety/
System Manager   http://localhost:9000/systemes/
TP Manager       http://localhost:9000/tp/
PedaShop         http://localhost:9000/pedashop/
PFMP Manager     http://localhost:9000/pfmp/
```

## Règle d’architecture à respecter

Ne pas recréer d’exposition publique par module.

À éviter : toute exposition publique séparée par module.

À utiliser :

```text
http://localhost:9000/toolmag/
http://localhost:9000/safety/
http://localhost:9000/systemes/
```

## Statut de ce dépôt

Le présent dépôt est un squelette. Il n’est pas encore exécutable tant que le code des services n’est pas ajouté dans `services/*`.
