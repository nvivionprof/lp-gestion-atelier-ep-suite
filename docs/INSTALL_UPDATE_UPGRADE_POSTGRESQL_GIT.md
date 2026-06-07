# Installation, update et upgrade PostgreSQL/Git

Version archive : `beta2-v0.0.4`.

## Principe

Cette archive bascule la suite en mode PostgreSQL par défaut.
Chaque module Django utilise sa propre base PostgreSQL :

- `lp_core`
- `toolmag`
- `safety`
- `pedashop`
- `system_manager`
- `tpmanager`
- `pfmp`

Cette séparation évite les collisions entre tables Django communes (`auth_*`, `django_migrations`, `django_session`).

## Installation neuve

```bash
chmod +x install.sh scripts/*.sh scripts/postgres/*.sh
./install.sh --mode install
```

L'installateur demande :

1. le mot de passe PostgreSQL ;
2. l'identifiant administrateur LP Core ;
3. le mot de passe administrateur LP Core.

Il met ensuite `.env` à jour, démarre PostgreSQL, construit les conteneurs et lance les migrations.

## Mise à jour depuis Git

```bash
./scripts/update_from_git.sh main
```

Ce script fait :

1. contrôle des modifications locales suivies par Git ;
2. `git fetch` / `git pull --ff-only` ;
3. `./install.sh --mode update` ;
4. sauvegarde pré-update si la politique l'exige ;
5. migrations directes par défaut.

## Upgrade depuis ZIP

```bash
./upgrade.sh /chemin/nouvelle_archive.zip
```

Le script conserve : `.env`, données PostgreSQL, données modules, backups et logs.

## Politique de versions minimales

La politique est stockée dans :

```text
versions/migration-policy.json
```

Pour cette version :

- update minimal : `beta2-v0.0.2`
- upgrade minimal : `beta2-v0.0.1`
- migrations activées par défaut
- sauvegarde pré-update/upgrade requise par défaut

## Désactiver les migrations

Réservé au diagnostic :

```bash
./install.sh --mode update --skip-migrations
```

Ne pas utiliser en fonctionnement normal.


## Données de démonstration

Pendant l’installation, choisir le chargement démo ou utiliser :

```bash
./install.sh --mode install --demo
# ou après installation
./scripts/load_demo_data.sh
```

## Vérification checksum

Avant ou après extraction :

```bash
sha256sum -c lp-gestion-atelier-ep-suite-beta2-v0.0.4-checksum-demo-supervision.zip.sha256
./scripts/verify_checksums.sh
```
