# LP Gestion Atelier Suite v2.8.6 — TP Manager parcours, affectations et formulaire

Type : installation complète / mise à jour SSH. Compatible mise à jour ciblée par module via `upgrade_module.sh tpmanager`.

## Évolutions TP Manager

- Création TP : réorganisation du cadre général selon la structure demandée :
  - ligne 1 : titre / thème principal / durée ;
  - ligne 2 : sous-thème / niveau / type / usage ;
  - ligne Nom - Auto séparée ;
  - résumé élève, contexte et problématique conservés sur trois lignes dédiées.
- Thèmes et sous-thèmes : format conseillé à préfixe court, ex. `RES - Réseau`; la numérotation reprend seulement `RES`.
- Les statuts `mobilisé`, `travaillé`, `évalué`, `certification`, les pourcentages et les points ne sont plus dans la page de création : ils sont réglés après création dans la page `Affecter / barème`.
- Suppression visuelle de la logique transfert inter-référentiel. La duplication devient une copie brouillon dans le même diplôme pour modification.
- TP liés : ajout de filtres de recherche pour sélectionner les TP liés depuis la base TP à jour.
- Ressources : recherche améliorée par origine, type et statut sur ToolMag, PedaShop et System Manager, en lecture seule.
- Parcours : nouvelle page pour sélectionner plusieurs TP et plusieurs élèves, puis affecter les TP aux élèves.

## Migration

- `0006_tpv2_parcours_affectation_bareme.py`
- Ajout de `bareme_total` sur TPV2.
- Ajout de `pourcentage` sur les compétences et critères officiels associés au TP.

## Commandes recommandées

```bash
./upgrade_module.sh tpmanager lp-gestion-atelier-ep-suite-v2.8.6-tpmanager-parcours-affectations-formulaire.zip

docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py seed_tpmanager_v2
docker compose exec -T tpmanager-app python manage.py check
```
