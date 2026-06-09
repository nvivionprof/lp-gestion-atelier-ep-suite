# LP Gestion Atelier EP Suite — V0.0.1-RC1

> Release candidate d’exploitation encadrée. Périmètre prioritaire : **ToolMag**, **System Manager minimal** et **PedaShop**.
> Mobile ciblé uniquement : prise de poste System Manager, inventaire ToolMag et prise de photo.

Voir :

- `docs/ROADMAP_RC_V0_0_1.md`
- `docs/ERGONOMIE_TERRAIN_RC_V0_0_1.md`
- `CHECKLIST_RECETTE_RC_V0_0_1.md`

---


## Exploitation sécurisée V0.0.1

Cette version pose la base officielle **V0.0.1**.

- Application et mises à jour applicatives : SSH / Git / wget GitHub uniquement.
- Interface web LP Core : supervision, sauvegarde et restauration des bases.
- Commande d’urgence après échec de mise à jour :

```bash
./scripts/restore_last_backup.sh --yes
```

- Installation / mise à jour depuis GitHub : voir `BOOTSTRAP-WGET.md`.
- Politique de version : voir `versions/version-registry.json`.


# LP Gestion Atelier EP Suite — Bêta 2 V0.0.2

Suite Django/Docker pour la gestion d’atelier pédagogique : LP Core, ToolMag, Safety Manager, PedaShop, System Manager, TP Manager et PFMP Manager.

Cette version est une **rebase propre préparatoire à la migration Git**. Elle repart de la consolidation V0.4.0c et ajoute les fichiers de pilotage technique nécessaires pour éviter les régressions lors des futures évolutions.

## Accès par défaut

Mode local WSL/PC :

```text
http://localhost:9000/
```

Compte initial LP Core :

```text
admin / admin
```

Le changement du mot de passe est demandé côté LP Core à la première connexion.

## Architecture Bêta 2

La suite passe par une passerelle unique `lp-gateway` basée sur Nginx :

```text
/              -> LP Core
/toolmag/      -> ToolMag
/safety/       -> Safety Manager
/pedashop/     -> PedaShop
/system/       -> System Manager
/tpmanager/    -> TP Manager
/pfmp/         -> PFMP Manager
```

Les modules **ne sont plus pensés comme des services exposés par ports publics séparés**. Les URLs publiques sont générées par domaine + chemin, par exemple :

```text
https://stjoseph-lpsuite.duckdns.org/system/
https://stjoseph-lpsuite.duckdns.org/toolmag/
```

## Installation complète

```bash
unzip lp-gestion-atelier-ep-suite-beta2-v0.0.2-git-ready.zip
cd lp-gestion-atelier-ep-suite-beta2-v0.0.2
chmod +x install.sh start.sh stop.sh upgrade.sh scripts/*.sh
./install.sh
```

## Paramètres publics / DuckDNS / HTTPS

Depuis LP Core :

```text
Administration > URLs / HTTPS
```

La page permet de régler :

- domaine public ;
- protocole HTTP/HTTPS ;
- token DuckDNS ;
- e-mail Let’s Encrypt ;
- génération/renouvellement du certificat ;
- application des URLs publiques dans `.env`.

La saisie de ports par module a été retirée de l’interface : la suite utilise une passerelle unique et des chemins `/toolmag`, `/system`, etc.

## Documents techniques obligatoires

Avant toute nouvelle évolution, lire :

```text
SUIVI_TECHNIQUE_SUITE.md
MIGRATIONS_ETAT.md
CHECKLIST_TESTS.md
GIT_MIGRATION.md
CONTRIBUTING.md
```

## Règle de développement

Toute modification future doit :

1. partir d’une base Git propre ;
2. modifier les sources, pas un ZIP historique ;
3. mettre à jour `SUIVI_TECHNIQUE_SUITE.md` ;
4. vérifier la syntaxe Python/YAML/shell ;
5. documenter les migrations ;
6. fournir une procédure de test reproductible.

## Type de livraison

Cette version est une **archive complète d’installation/reprise SSH**, pas un patch web.


## Bêta 2 V0.0.4

Cette version ajoute la vérification d’intégrité SHA256, le chargement optionnel de bases de démonstration et la supervision des bases PostgreSQL depuis LP Core. Voir `docs/RELEASE_BETA2_V0_0_4.md`.


## Décision sécurité — mises à jour et sauvegardes web

Les mises à jour applicatives se font exclusivement par SSH/Git. LP Core peut en revanche piloter les sauvegardes/restaurations de bases PostgreSQL par module ou totales, avec manifest, checksums et confirmation administrateur.


## Update rapide

```bash
./update.sh --channel stable
./update.sh --channel rc
```

Documentation : `docs/UPDATE_RAPIDE_GIT.md`.

## HTTPS DuckDNS

```bash
./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org email@example.com TOKEN_DUCKDNS 443 80
```

Documentation : `docs/HTTPS_DUCKDNS_RAPIDE.md`.
