# Installation / mise à jour depuis GitHub avec wget

Commande standard :

```bash
wget -O /tmp/lp-suite-bootstrap.sh https://raw.githubusercontent.com/nvivionprof/lp-gestion-atelier-ep-suite/main/scripts/github_bootstrap.sh
bash /tmp/lp-suite-bootstrap.sh V0.0.1-RC1 --dir /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
```

Commande d'urgence après échec :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
./scripts/restore_last_backup.sh --yes
```
