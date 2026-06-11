# Mise à jour v2.8.2 — TP Manager V2 : mécanique référentiel MELEC

Type de paquet : **installation complète / mise à jour SSH**.

## Objectif

Cette version corrige la logique de création des TP pour suivre la mécanique réelle du référentiel MELEC :

```text
Activités officielles A1 à A5
  → tâches officielles T1-1 à T5-3
  → compétences associables C1 à C13 selon le tableau de correspondance
  → critères officiels d’évaluation liés aux compétences
  → AP / attitudes professionnelles visibles et cochables
```

## Points ajoutés

- Case à cocher des activités.
- Affichage conditionnel des tâches selon les activités cochées.
- Affichage conditionnel des compétences selon les tâches cochées.
- Affichage conditionnel des critères officiels selon les compétences cochées.
- Affichage et sélection des AP liées aux compétences.
- Affichage de l’autonomie et des responsabilités associées aux tâches quand l’information est disponible.
- Numérotation automatique : `TYPE-CLASSE-DOMAINE-001`.

## Protection des données

Migration additive `0003_tpv2_referentiel_mecanique_melec.py`.

Elle ne supprime pas les TP existants, ne modifie pas ToolMag, ne modifie pas PedaShop et ne modifie pas System Manager.

## Commandes après mise à jour

```bash
docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py seed_tpmanager_v2
```

