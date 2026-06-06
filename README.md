# LP Gestion Atelier EP Suite

Suite web modulaire destinée à la gestion pédagogique et technique d’un atelier de lycée professionnel.

Le projet vise à regrouper plusieurs outils complémentaires : gestion de stock, magasin d’outillage, sécurité atelier, ressources pédagogiques, systèmes techniques, TP, PFMP et suivi des actions élèves afin de produire des bilans d’évolution des compétences professionnelles.

> Nom court recommandé du dépôt : `lp-gestion-atelier-ep-suite`  
> Compte GitHub prévu : `nvivionprof`

---

## Objectifs principaux

- Centraliser les outils de gestion d’atelier dans une suite cohérente.
- Permettre l’utilisation par les élèves avec traçabilité pédagogique.
- Faciliter l’évaluation des compétences à partir des actions réalisées.
- Fournir une architecture modulaire maintenable par services.
- Prévoir l’installation, la mise à jour par archive ZIP et la restauration après crash serveur.

---

## Modules prévus

| Module | Rôle principal | Port local prévu |
|---|---:|---:|
| LP Core | Authentification, rôles, menu global, référentiels communs, sauvegarde/restauration | `9000` |
| ToolMag | Magasin d’outillage, sorties/retours, QR codes, maintenance, inventaire | `9001` |
| Safety Manager | DUERP, risques, actions de prévention, événements sécurité | `9002` |
| System Manager | Systèmes techniques, zones atelier, documents, réservations | `9003` |
| TP Manager | Création de TP, référentiels, compétences, documents élèves/profs | `9004` |
| PedaShop | Ressources pédagogiques, consommables, documents et médias | `9005` |
| PFMP Manager | Stages, suivi, bilans, compétences et documents PFMP | à définir |

---

## Architecture cible

Le projet est prévu comme une suite multi-services Django conteneurisée avec Docker Compose.

```text
Internet / réseau local
        │
        ▼
Reverse proxy HTTPS
        │
        ├── LP Core           :9000
        ├── ToolMag           :9001
        ├── Safety Manager    :9002
        ├── System Manager    :9003
        ├── TP Manager        :9004
        └── PedaShop          :9005
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

Ce dépôt est actuellement un **squelette de dépôt**. Il pose l’organisation, la documentation, les conventions et les emplacements des modules. Le code applicatif Django réel doit ensuite être ajouté dans chaque dossier `services/*`.

---

## Principes techniques retenus

- Django / Python pour les applications métiers.
- Docker Compose pour l’orchestration locale ou serveur.
- Reverse proxy HTTPS en frontal.
- Données persistantes séparées du code.
- Sauvegarde complète : bases, médias, certificats, `.env`, métadonnées de version.
- Rôles utilisateurs centralisés par LP Core.
- Imports élèves/classes/formations via fichiers structurés.
- Traçabilité des actions élèves pour exploitation pédagogique.

---

## Statut

Projet en cadrage initial.

Prochaine étape recommandée : importer cette structure dans GitHub, puis ajouter progressivement le code réel de chaque module.
