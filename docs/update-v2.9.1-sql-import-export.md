# V2.9.1 — Export/import SQL par module

Ajoute dans chaque module une page d'administration SQL permettant :

- le téléchargement d'un dump SQL complet de la base SQLite du module ;
- l'import SQL en remplacement complet, avec sauvegarde automatique préalable ;
- l'import SQL additif pour scripts correctifs ;
- des scripts SSH `scripts/export_module_sql.sh` et `scripts/import_module_sql.sh`.

PedaShop conserve ses imports/exports XLSX existants : la couche SQL est complémentaire.

Modules couverts : LP Core, ToolMag, Safety Manager, PedaShop, System Manager, TP Manager / Evaluation Manager.

Après un import SQL en remplacement, redémarrer le module et exécuter les migrations Django.
