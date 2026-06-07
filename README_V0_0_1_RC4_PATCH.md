# Patch V0.0.1-RC4 — corrections de propreté post-installation

Ce patch corrige les alertes résiduelles observées après l'installation V0.0.1-RC3 :

- import LP Core démo : évite les messages duplicate key si seed_core a déjà créé PROF-0001 ;
- TP Manager → System Manager : normalise l'URL API interne Docker et évite l'appel /system/api/systems/ ;
- dépendances requests : stabilise urllib3 / charset-normalizer / chardet pour supprimer RequestsDependencyWarning ;
- CHECKSUMS : exclut __pycache__ et *.pyc.

Usage :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-git-rc2
git checkout rc
git pull
unzip -o /home/lp-gestion-atelier-ep-suite-v0.0.1-rc4-clean-fixes.zip
bash apply_v0_0_1_rc4_clean_fixes.sh
```
