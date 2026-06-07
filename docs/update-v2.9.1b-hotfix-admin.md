# v2.9.1b — hotfix TP Manager admin

Correctif de reprise après installation 2.9.1 puis 2.9.0.

## Correction

- Correction de `tp_manager.admin.BacCompetenceOfficialAdmin` : retrait du champ inexistant `ordre` de `list_display`.
- Correction de `tp_manager.admin.TPV2OfficialAdmin` : remplacement des champs inexistants `niveau`, `theme_principal`, `date_creation` par `niveau_classe`, `domaine_principal`, `updated_at`.
- Conservation d’Evaluation Manager et de l’export/import SQL par module.

## Type

Mise à jour SSH, compatible `upgrade_module.sh tpmanager`.
