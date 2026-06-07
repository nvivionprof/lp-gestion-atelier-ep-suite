# V1.5.0 — Identité visuelle

Cette version intègre les logos fournis par l’utilisateur dans les pages du logiciel.

## LP Core
- Le fond et la mise en page LP Core sont conservés.
- Les tuiles ToolMag et Safety Manager utilisent les logos fournis.

## ToolMag
- Le logo du bandeau supérieur est remplacé par le visuel ToolMag fourni.
- Le reste de la mise en page ToolMag est conservé.

## Safety Manager
- Safety Manager conserve son conteneur indépendant sur le port 9002.
- L’interface est rapprochée du style ToolMag.
- Le bandeau supérieur est bordeaux/rouge foncé pour distinguer le module sécurité.
- Le logo Safety Manager fourni est intégré dans le bandeau supérieur.

## Bases de données
Aucune migration destructive. Les dossiers de données restent protégés par `upgrade.sh` :

```text
lp-core-db/data/
toolmag-db/data/
safety-db/data/
.env
backups/
imports/
```
