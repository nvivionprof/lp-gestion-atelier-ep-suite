# LP Gestion Atelier EP Suite — V0.0.1-RC11

Type : **upgrade semi-rapide obligatoire**.

## Contenu

- LP Core : champ `CoreUser.rights` converti en `TextField` pour corriger l'erreur PostgreSQL `value too long for type character varying(255)` dans `/droits-par-lot/`.
- LP Core : ajout de l'action par lot **Modifier rôle principal** : élève, utilisateur, magasinier, professeur, responsable, administrateur.
- LP Core : nettoyage des droits avant sauvegarde pour éviter les doublons et valeurs vides.
- PedaShop : pastilles de connexion style ToolMag, vrai switch utilisateur/magasinier, page bon dynamique 30/70 avec recherche article/code-barres.
- PedaShop : suppression/désactivation des magasins cochés depuis la page magasins.
- System Manager, TP Manager, Safety Manager, PFMP Manager : pastilles de connexion harmonisées type ToolMag.
- PFMP Manager : correction d'affichage carte Leaflet par CSS local minimal + `map.invalidateSize()` après rendu et resize.

## Application

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-git-rc2
git checkout rc
git pull
unzip -o /home/lp-gestion-atelier-ep-suite-v0.0.1-rc11-ui-rights-pfmp-bulk.zip
bash apply_v0_0_1_rc11_ui_rights_pfmp_bulk.sh
```

Puis commit / push / tag :

```bash
git add -A
git commit -m "RC11 corrige droits par lot UI globale et carte PFMP"
git push origin rc
git tag -f V0.0.1-RC11
git push --force origin V0.0.1-RC11
```

Déploiement :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-rc
lp-suite upgrade rc
```
