# Hotfix V0.4.0a — script sans rsync

Correction du script `apply_update_v0.4.0_public_domain_cert.sh` : si `rsync` n’est pas disponible sur l’hôte, la copie du patch est réalisée par un flux `tar`.

Commande recommandée :

```bash
/home/patch-v0.4.0a-public-domain-cert/scripts/apply_update_v0.4.0a_public_domain_cert.sh /home/user/docker/lp-gestion-atelier-ep-suite
```
