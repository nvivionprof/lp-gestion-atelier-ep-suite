# LP Gestion Atelier EP Suite v2.9.1a — hotfix Evaluation Manager admin

Correctif de reprise après installation v2.9.1 avant v2.9.0.

## Corrige

- `SystemCheckError admin.E040` dans `evaluation_manager.admin`.
- Ajoute les `search_fields` nécessaires aux modèles utilisés par `autocomplete_fields`.
- Ajoute des ModelAdmin spécifiques pour les objets référentiel utilisés par Evaluation Manager :
  - `BacCompetence`
  - `BacCompetenceCritere`
  - `TPV2`

## Conserve

- Export/import SQL web et scripts de la v2.9.1.
- Evaluation Manager MELEC + seed de démo.
- Données existantes non modifiées.

## Installation recommandée

```bash
./upgrade_module.sh tpmanager /home/lp-gestion-atelier-ep-suite-v2.9.1a-hotfix-evaluation-admin.zip
```

Puis :

```bash
docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py check
```

Optionnel pour la démo Evaluation Manager :

```bash
docker compose exec -T tpmanager-app python manage.py seed_evaluation_demo
```
