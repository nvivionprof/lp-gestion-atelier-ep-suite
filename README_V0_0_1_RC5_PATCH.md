# Patch V0.0.1-RC5 — nettoyage final installation

Objectifs :

- supprimer les `RequestsDependencyWarning` en bornant les dépendances HTTP compatibles ;
- corriger la synchronisation System Manager -> TP Manager en supportant l'URL interne directe et l'URL préfixée ;
- passer la version en `V0.0.1-RC5` ;
- recalculer `CHECKSUMS.sha256` après toutes les modifications ;
- exclure `CHECKSUMS.sha256`, `__pycache__`, `*.pyc` et les dossiers runtime du checksum.

Application :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-git-rc2
git checkout rc
git pull
unzip -o /home/lp-gestion-atelier-ep-suite-v0.0.1-rc5-final-clean.zip
bash apply_v0_0_1_rc5_final_clean.sh
```

Validation attendue :

```text
CHECKSUMS OK
```
