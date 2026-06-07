# Hotfix V0.4.0b — Certificats DuckDNS depuis LP Core

## Correction

Ce hotfix corrige le cas où l'action LP Core `issue_cert` échoue avec :

```text
ERREUR: commande docker introuvable dans l'environnement qui exécute cert_manager.sh
```

## Changement technique

- `suite-admin-agent` embarque maintenant :
  - le client Docker statique ;
  - le binaire `lego`.
- `cert_manager.sh` peut générer un certificat DNS-01 DuckDNS directement avec `lego`, sans dépendre de `docker run`.
- Le script d'application force un rebuild `--no-cache` de `suite-admin-agent` et vérifie `docker --version` et `lego --version` dans le conteneur.
