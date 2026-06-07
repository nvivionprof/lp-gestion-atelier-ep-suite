# Bêta V0.2.0 — logos et lanceurs harmonisés

Cette version complète harmonise les lanceurs LP Core et les logos de modules.

## Corrections

- Tous les modules affichent la version Bêta V0.2.0.
- Les lanceurs LP Core sont organisés en 3 cartes par rangée sur grand écran.
- Les logos ToolMag, Safety Manager, PedaShop, System Manager et TP Manager utilisent des visuels larges homogènes.
- Ajout des logos horizontaux System Manager et TP Manager dans leurs bandeaux applicatifs respectifs.
- Conservation du routage explicite du portail : /toolmag, /safety, /pedashop, /system, /tpmanager.

## Installation conseillée

```bash
cd /home/user/docker/lp-gestion-atelier-ep-suite
./upgrade.sh --skip-seed /home/lp-gestion-atelier-ep-suite-beta-v0.2.0-full-logos-lanceurs.zip
```

En cas de cache Docker instable :

```bash
./upgrade.sh --clean-build --skip-seed /home/lp-gestion-atelier-ep-suite-beta-v0.2.0-full-logos-lanceurs.zip
```
