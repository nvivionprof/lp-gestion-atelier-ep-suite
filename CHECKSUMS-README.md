# Vérification d’intégrité — LP Gestion Atelier EP Suite

Cette archive contient deux niveaux de vérification.

## 1. Vérification externe du ZIP

Le fichier distribué en complément `*.zip.sha256` permet de vérifier l’archive avant extraction :

```bash
sha256sum -c lp-gestion-atelier-ep-suite-beta2-v0.0.4-checksum-demo-supervision.zip.sha256
```

## 2. Vérification interne après extraction

Après extraction de l’archive :

```bash
cd lp-gestion-atelier-ep-suite
./scripts/verify_checksums.sh
```

Le fichier `CHECKSUMS.sha256` vérifie les fichiers livrés dans l’archive. Les fichiers variables ou locaux sont volontairement exclus : `.env`, bases de données, médias, sauvegardes, logs, certificats ACME et caches Python.

## Pendant l’installation

`install.sh` lance automatiquement cette vérification si `CHECKSUM_VERIFY_ON_INSTALL=1` dans `.env`.

Pour diagnostic uniquement :

```bash
./install.sh --skip-checksum
```
