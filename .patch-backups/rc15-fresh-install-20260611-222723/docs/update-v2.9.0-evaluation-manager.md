# LP Gestion Atelier EP Suite v2.9.0 — Evaluation Manager

## Type de mise à jour

Mise à jour SSH / module TP Manager recommandée.

```bash
./upgrade_module.sh tpmanager lp-gestion-atelier-ep-suite-v2.9.0-evaluation-manager-melec-demo.zip
```

Puis :

```bash
docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py check
```

Base exemple MELEC :

```bash
docker compose exec -T tpmanager-app python manage.py seed_evaluation_demo
```

## Ajouts

- Ajout du module applicatif `evaluation_manager` dans `tpmanager-app`.
- Tableau de bord type CPRO avec colonnes par activité / TP évalué.
- Vue compacte : une ligne par compétence.
- Vue développée : compétence puis critères / sous-compétences.
- Niveaux : NE, NA, EC, A, PA, AB.
- Autoévaluation élève stockée séparément de l’évaluation professeur.
- Seule l’évaluation professeur est utilisée pour les bilans officiels.
- Case absent au niveau de l’activité : toutes les lignes de l’activité sont interprétées AB.
- TP non fait, à refaire, remédiation nécessaire.
- Note affichée uniquement si le TP est noté, calculée depuis les critères / sous-compétences.
- Base de démonstration MELEC : élève `demo-eval-melec`, douze évaluations et bilan intermédiaire P1.

## Non destructif

Aucune modification destructive de ToolMag, PedaShop, Safety Manager ou System Manager.
