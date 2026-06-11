# RC9 — System Manager : nettoyage SQL et synchronisation LP Core

## Corrections

- Suppression de l'ancienne page SQLite `/system/admin-sql/`.
- Suppression de l'entrée `Base SQL` dans le menu System Manager.
- Suppression de la synchronisation directe depuis le menu admin System Manager.
- Conservation des synchronisations uniquement dans `Paramétrage`.
- Correction du 403 lors de `System Manager → LP Core` : l'endpoint LP Core `/api/system-manager/referentials/import/` est une API interne authentifiée par `X-API-Key`; elle ne doit pas être bloquée par le CSRF navigateur.

## Contrôles attendus

```bash
curl -sSI http://localhost:9000/system/admin-sql/ | head
```

La page ne doit plus être active.

```bash
curl -sSL http://localhost:9000/system/ | grep -Ei 'Base SQL|Synchroniser LP Core' || echo OK
```

Le menu admin ne doit plus afficher ces entrées.
