# LP Gestion Atelier EP Suite — Bêta 2 V0.0.4

## Type de version

Installation complète / update compatible depuis `beta2-v0.0.3` / upgrade contrôlé depuis `beta2-v0.0.1`.

## Ajouts

- `CHECKSUMS.sha256` intégré à l’archive.
- `scripts/verify_checksums.sh` pour vérification rapide après extraction.
- Fichier externe `.zip.sha256` fourni en complément pour vérifier l’archive téléchargée.
- Option interactive de chargement de bases de démonstration à l’installation.
- Script relançable `scripts/load_demo_data.sh`.
- LP Core : page `Supervision bases` pour contrôler l’état des bases PostgreSQL des modules.

## Commandes

Vérifier l’archive extraite :

```bash
./scripts/verify_checksums.sh
```

Installer avec démo :

```bash
./install.sh --mode install --demo
```

Installer sans démo :

```bash
./install.sh --mode install --no-demo
```

Charger ou recharger les données de démonstration après installation :

```bash
./scripts/load_demo_data.sh
```

## LP Core

Accès supervision :

```text
http://serveur:9000/supervision-bases/
```

La page liste : module, base, état de connexion, taille, nombre de tables, nombre de migrations et dernière migration Django connue.
