# LP Gestion Atelier Suite v2.8.7 — TP Manager nom auto / classes / préparation CAP

Évolution ciblée TP Manager.

## Modifications

- Nouveau format de repère automatique : `FORMATION-THEME-SOUSTHEME-001`.
- La prévisualisation affiche le nom complet : `FORMATION-THEME-SOUSTHEME-001 — Titre`.
- Le type de TP et la classe ne sont plus utilisés dans le repère automatique.
- Les trois caractères du thème principal et du sous-thème sont extraits depuis les listes au format `RES - Réseau`, `IPA - Adressage IP`, etc.
- Le champ `Nom` peut être modifié manuellement si la case `Nom - Auto` est décochée.
- En modification d’un TP existant, les paramètres avancés sont ouverts et restent modifiables.
- Les listes de niveaux sont filtrées selon le diplôme :
  - Bac Pro : `2nde`, `1ère`, `Tale` ;
  - BTS : `1ère année`, `2ème année` ;
  - CAP : logique prévue pour ajout ultérieur des bases.
- Alignement vertical haut des champs du formulaire.

## Installation

Mise à jour module recommandée :

```bash
./upgrade_module.sh tpmanager lp-gestion-atelier-ep-suite-v2.8.7-tpmanager-nom-auto-classes-cap-prep.zip
```

Puis :

```bash
docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py check
```

Aucune migration destructive.
