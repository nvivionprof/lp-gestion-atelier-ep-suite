# Installation cible

## Pré-requis

- Serveur Linux ou WSL2 pour tests.
- Docker Engine.
- Docker Compose v2.
- Git.
- Accès réseau au port frontal choisi.

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

```text
LP Core         http://localhost:9000/
ToolMag         http://localhost:9001/
Safety Manager  http://localhost:9002/
System Manager  http://localhost:9003/
TP Manager      http://localhost:9004/
PedaShop        http://localhost:9005/
```

## Statut de ce dépôt

Le présent dépôt est un squelette. Il n’est pas encore exécutable tant que le code des services n’est pas ajouté dans `services/*`.
