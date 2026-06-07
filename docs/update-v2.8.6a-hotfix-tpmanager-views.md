# LP Gestion Atelier Suite v2.8.6a — Correctif TP Manager démarrage

Correctif urgent pour TP Manager après la v2.8.6.

## Problème corrigé

Le conteneur `tpmanager-app` redémarrait en boucle car `tp_manager/urls.py` référençait deux vues absentes dans `views_v2.py` :

- `tp_referentiel_affect`
- `parcours_assign`

L'erreur bloquait les migrations Django dès la vérification des URL.

## Correction

- Ajout de la vue `tp_referentiel_affect` pour la page `Affecter / barème`.
- Ajout défensif de la vue `parcours_assign` pour éviter le crash URL.
- Aucune migration destructive.
- Aucun changement des bases ToolMag / PedaShop / System Manager.

## Installation conseillée

```bash
./upgrade_module.sh tpmanager lp-gestion-atelier-ep-suite-v2.8.6a-hotfix-tpmanager-views.zip
```

Puis :

```bash
docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py seed_tpmanager_v2
docker compose exec -T tpmanager-app python manage.py check
```
