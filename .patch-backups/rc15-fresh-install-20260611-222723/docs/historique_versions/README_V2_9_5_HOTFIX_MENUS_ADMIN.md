# LP Gestion Atelier EP Suite v2.9.5 — hotfix menus admin

Correctif transversal d’interface.

## Correction

Certaines entrées des menus déroulants **Fonctions admin** pouvaient apparaître comme zones cliquables sans libellé selon les styles hérités ou le rendu des formulaires POST.

La version corrige :

- ToolMag ;
- System Manager ;
- TP Manager / Sequence Manager / Evaluation Manager ;
- styles communs de dropdown ;
- boutons de synchronisation affichés avec libellé explicite ;
- liens admin munis de classes/titres explicites.

## Installation conseillée

Comme plusieurs modules statiques/templates sont concernés :

```bash
./upgrade.sh /home/lp-gestion-atelier-ep-suite-v2.9.5-hotfix-menus-admin-libelles.zip
```

Si seul TP Manager est urgent :

```bash
./upgrade_module.sh tpmanager /home/lp-gestion-atelier-ep-suite-v2.9.5-hotfix-menus-admin-libelles.zip
```

