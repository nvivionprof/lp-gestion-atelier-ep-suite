# V0.0.1-RC12 — UI, droits par lot, PFMP carte, réparation routes

## Points corrigés

- LP Core : `CoreUser.rights` passe en `TextField` pour éviter l'erreur `value too long for type character varying(255)`.
- LP Core : gestion par lot avec action `Modifier rôle principal`.
- LP Core : ajout des droits PFMP dans la page de gestion par lot.
- LP Core : page `/droits-par-lot/` en largeur 100 %.
- PedaShop : page `/pedashop/bons/nouveau/` en largeur 100 %, disposition 30 % recherche / 70 % bon.
- Tous modules : pastilles de connexion harmonisées type ToolMag.
- PFMP : correction de l'affichage carte Leaflet lorsque le CSS CDN ne se charge pas correctement.
- Ajout `scripts/repair_routes_after_wsl.sh` pour relancer les routes après coupure WSL sans supprimer les volumes.

## Déploiement

Upgrade semi-rapide obligatoire : migration LP Core.

```bash
lp-suite upgrade rc
```

Après une coupure sauvage WSL :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-rc
./scripts/repair_routes_after_wsl.sh
```
