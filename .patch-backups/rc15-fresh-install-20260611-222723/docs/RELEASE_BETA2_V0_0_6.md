# Release beta2-v0.0.6 — Démo uniquement à l'installation neuve

## Nature

Installation / update / upgrade par SSH-Git uniquement.

## Règle démo

Les bases de démonstration sont demandées au début de l'installation uniquement en mode :

```bash
./install.sh --mode install
```

Si l'administrateur répond oui, elles sont chargées automatiquement après les migrations Django.

En modes `update` et `upgrade` :

- aucune question sur les démos ;
- aucun chargement automatique ;
- `LOAD_DEMO_DATA` est forcé à `0` ;
- les options `--demo` et `--no-demo` sont bloquées.

## Commandes

Installation neuve avec question interactive :

```bash
./install.sh --mode install
```

Installation neuve avec démo forcée :

```bash
./install.sh --mode install --demo
```

Installation neuve sans démo :

```bash
./install.sh --mode install --no-demo
```

Update/upgrade :

```bash
./install.sh --mode update
./install.sh --mode upgrade
```

Ces deux derniers modes ne chargent jamais les données de démonstration automatiquement.
