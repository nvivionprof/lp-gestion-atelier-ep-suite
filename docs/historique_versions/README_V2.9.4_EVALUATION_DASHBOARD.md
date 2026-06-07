# v2.9.4 — Evaluation Manager : tableau compact années/bilans

Correctif d'interface pour le tableau de bord élève Evaluation Manager.

## Changements

- Regroupement des colonnes d'évaluation par année/niveau de réalisation : 2nde, 1ère, Tale, 1ère année, 2ème année.
- Colonnes très compactes pour limiter le défilement horizontal et permettre une lecture sur plusieurs années.
- Vue développée : les sous-compétences restent sous les compétences ; les bilans sont positionnés uniquement sur la ligne de compétence générale.
- Le bilan n'est plus affiché sur les lignes de sous-compétences.
- La démo MELEC place EV01 à EV05 en 1MELEC puis les suivantes en TMELEC pour tester l'entête 1ère / Tale.

## Commandes

```bash
./upgrade_module.sh tpmanager /chemin/lp-gestion-atelier-ep-suite-v2.9.4-evaluation-dashboard-compact-years.zip

docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py check
```

Démo optionnelle :

```bash
docker compose exec -T tpmanager-app python manage.py seed_evaluation_demo
```
