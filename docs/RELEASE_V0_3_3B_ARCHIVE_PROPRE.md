# LP Gestion Atelier EP Suite — Bêta V0.3.3b archive propre consolidée

## Nature

Archive complète consolidée intégrant :

- V0.3.3 System Manager : classeur système, GMAO, blocs atelier LP Core ;
- hotfix V0.3.3a : correction `SystemUser` manquant dans `system_manager/forms.py` ;
- correction des indications de test TP Manager : URL correcte `/tpmanager/`.

## Recommandation

- Pour une installation neuve : utiliser cette archive complète.
- Pour une installation existante : utiliser de préférence le patch V0.3.3b afin d’éviter de recopier inutilement les autres modules.

## Tests principaux

```bash
curl -I http://localhost:9000/
curl -I http://localhost:9000/system/
curl -I http://localhost:9000/blocs-atelier/
curl -I http://localhost:9000/tpmanager/
```

## Conteneurs attendus

```bash
docker compose ps
```

`lp-core-app`, `system-manager-app`, `tpmanager-app` et `lp-gateway` doivent être `Up`.
