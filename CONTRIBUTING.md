# Règles de contribution

## Principes

- Une modification = un objectif clair.
- Ne pas mélanger correction urgente, refonte UI et migration de base dans le même commit.
- Ne pas modifier les migrations historiques sans raison documentée.
- Ne pas casser les chemins publics par passerelle unique.

## Avant commit

```bash
python -m compileall lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app
bash -n scripts/*.sh
```

Si Docker est disponible :

```bash
docker compose config
docker compose up -d --build
docker compose ps
```

## Nommage versions

Pendant la restructuration :

```text
Bêta 2 V0.0.x
```

Quand la base Git sera stabilisée, reprendre un versionnement plus classique.
