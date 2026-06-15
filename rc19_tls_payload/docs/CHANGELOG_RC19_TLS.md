# Changelog — RC19 TLS Cert Manager

## RC19 — Ajout gestion certificats LP Core

### Ajouté

- Mode TLS `duckdns-acme` pour générer un certificat Let's Encrypt par challenge DNS-01 DuckDNS.
- Mode TLS `manual` pour déposer un certificat fourni par le lycée.
- Mode TLS `selfsigned` pour test local.
- Scripts `tls-duckdns-issue.sh`, `tls-duckdns-renew.sh`, `tls-manual-install.sh`, `tls-selfsigned-test.sh`, `tls-status.sh`.
- Modèle d'intégration LP Core : page de configuration TLS, formulaires, logs d'opération.
- Dossier standard `./certs/manual/` pour les fichiers `fullchain.pem` et `privkey.pem`.
- Documentation d'installation et de sécurité.

### Contraintes

- Ne pas exposer les tokens DuckDNS dans GitHub.
- Ne pas commiter les certificats ni clés privées.
- Le challenge DuckDNS ne nécessite pas le port 80.
- Le certificat couvre le nom de domaine, pas le port `:9000`.
