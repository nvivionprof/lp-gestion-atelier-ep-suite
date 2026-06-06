# LP Gestion Atelier EP Suite

Suite web modulaire destinée à la gestion pédagogique et technique d’un atelier de lycée professionnel.

Le projet regroupe plusieurs outils complémentaires : gestion de stock, magasin d’outillage, sécurité atelier, ressources pédagogiques, systèmes techniques, TP, PFMP et suivi des actions élèves afin de produire des bilans d’évolution des compétences professionnelles.

> Nom court recommandé du dépôt : `lp-gestion-atelier-ep-suite`  
> Compte GitHub prévu : `nvivionprof`

---

## Principe d’accès retenu

L’architecture publique retenue est **un seul point d’entrée web** :

```text
http://serveur:9000/
```

Les modules ne sont pas exposés par des ports dédiés. Ils sont accessibles par chemins :

| Module | Rôle principal | URL publique |
|---|---|---|
| LP Core | Authentification, rôles, menu global, référentiels communs, sauvegarde/restauration | `/` |
| ToolMag | Magasin d’outillage, sorties/retours, QR codes, maintenance, inventaire | `/toolmag/` |
| Safety Manager | DUERP, risques, actions de prévention, événements sécurité | `/safety/` |
| System Manager | Systèmes techniques, zones atelier, documents, réservations | `/systemes/` |
| TP Manager | Création de TP, référentiels, compétences, documents élèves/profs | `/tp/` |
| PedaShop | Ressources pédagogiques, consommables, documents et médias | `/pedashop/` |
| PFMP Manager | Stages, suivi, bilans, compétences et documents PFMP | `/pfmp/` |

> Les anciens accès du type `:900x` par module sont abandonnés.

---

## Objectifs principaux

- Centraliser les outils de gestion d’atelier dans une suite cohérente.
- Permettre l’utilisation par les élèves avec traçabilité pédagogique.
- Faciliter l’évaluation des compétences à partir des actions réalisées.
- Fournir une architecture modulaire maintenable.
- Prévoir l’installation, la mise à jour par archive ZIP et la restauration après crash serveur.

---

## Architecture cible

Le projet est prévu comme une suite Django conteneurisée avec Docker Compose.

```text
Internet / réseau local
        │
        ▼
Port public unique :9000
        │
        ▼
Reverse proxy / routeur applicatif
        │
        ├── /              → LP Core
        ├── /toolmag/      → ToolMag
        ├── /safety/       → Safety Manager
        ├── /systemes/     → System Manager
        ├── /tp/           → TP Manager
        ├── /pedashop/     → PedaShop
        └── /pfmp/         → PFMP Manager
```

Voir : [`docs/architecture.md`](docs/architecture.md)

---

## Démarrage rapide du dépôt

Après création du dépôt GitHub vide :

```bash
git init
git add .
git commit -m "Initialisation du dépôt LP Gestion Atelier EP Suite"
git branch -M main
git remote add origin https://github.com/nvivionprof/lp-gestion-atelier-ep-suite.git
git push -u origin main
```

Voir : [`docs/github-creation-web.md`](docs/github-creation-web.md)

---

## Installation locale prévue

```bash
cp .env.example .env
docker compose up -d --build
```

Accès local prévu :

```text
http://localhost:9000/
http://localhost:9000/toolmag/
http://localhost:9000/safety/
http://localhost:9000/systemes/
http://localhost:9000/tp/
http://localhost:9000/pedashop/
http://localhost:9000/pfmp/
```

Ce dépôt est actuellement un **squelette de dépôt**. Il pose l’organisation, la documentation, les conventions et les emplacements des modules. Le code applicatif Django réel doit ensuite être ajouté dans chaque dossier `services/*`.

---

## Principes techniques retenus

- Django / Python pour les applications métiers.
- Docker Compose pour l’orchestration locale ou serveur.
- Reverse proxy frontal exposant uniquement `:9000`.
- Routage par chemins applicatifs.
- Données persistantes séparées du code.
- Sauvegarde complète : bases, médias, certificats, `.env`, métadonnées de version.
- Rôles utilisateurs centralisés par LP Core.
- Imports élèves/classes/formations via fichiers structurés.
- Traçabilité des actions élèves pour exploitation pédagogique.

---

## Statut

Projet en cadrage initial.

Prochaine étape recommandée : importer cette structure dans GitHub, puis ajouter progressivement le code réel de chaque module.
