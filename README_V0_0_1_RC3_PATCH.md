# Patch V0.0.1-RC3 — corrections techniques post-RC2

Ce patch corrige les 3 points non bloquants repérés après l’installation neuve RC2 :

1. suppression de la synchronisation post-démo trop précoce dans `load_demo_data.sh` quand le script est appelé depuis `install.sh` ;
2. synchronisation utilisateurs TP Manager rendue idempotente pour éviter le doublon `PROF-0001` ;
3. synchronisation System Manager → TP Manager rendue non bloquante et sans traceback si l’API systèmes n’est pas encore disponible.

La version passe à `V0.0.1-RC3`. Après validation d’installation neuve sans ces alertes, il sera possible de taguer la version finale `V0.0.1`.

## Application

Depuis le dépôt Git local sur la branche `rc` :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-git-rc2
git checkout rc
git pull
unzip -o /home/lp-gestion-atelier-ep-suite-v0.0.1-rc3-fixes.zip
bash apply_v0_0_1_rc3_fixes.sh
```

Puis :

```bash
git diff --stat
git add -A
git commit -m "Passe en V0.0.1-RC3 avec corrections post-installation"
git push origin rc
git tag V0.0.1-RC3
git push origin V0.0.1-RC3
```

Ensuite, refaire une installation neuve depuis GitHub pour valider.
