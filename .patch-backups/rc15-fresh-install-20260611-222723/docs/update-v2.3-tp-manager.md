# Mise à jour V2.3 — TP Manager

Cette version repart de la V2.2 System Manager et ajoute le module `tpmanager-app`.

## Services

- LP Core : 9000
- ToolMag : 9001
- Safety Manager : 9002
- PedaShop : 9003
- System Manager : 9004
- TP Manager : 9005

## Mise à jour serveur

Avant remplacement :

```bash
./scripts/backup_all.sh
```

Dossiers de données à conserver :

```text
lp-core-db/data/
toolmag-db/data/
safety-db/data/
pedashop-db/data/
system-manager-db/data/
tpmanager-db/data/
```

Puis :

```bash
./scripts/migrate_all.sh
```

## Notes

Le module TP Manager utilise un modèle documentaire : le TP source est unique. Les parcours élèves stockent les traces, photos, commentaires et évaluations sans dupliquer le document TP.
