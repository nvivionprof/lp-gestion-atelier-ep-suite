# Update rapide Git — LP Gestion Atelier EP Suite

## Commandes stables

Dernière version stable :

```bash
./update.sh --channel stable
```

Dernière RC :

```bash
./update.sh --channel rc
```

Archive locale :

```bash
./update.sh --zip /home/lp-suite.zip
```

## Règle

Un update ne fait pas de réinstallation complète :

- pas de `docker compose down -v` ;
- pas de `docker builder prune -af` ;
- pas de `--no-cache` par défaut ;
- conservation de `.env`, PostgreSQL, médias, sauvegardes, SSL et imports.

Le mode lourd est réservé à la réparation :

```bash
./update.sh --channel rc --repair-no-cache
```
