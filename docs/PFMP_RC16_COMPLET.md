# LP Gestion Atelier EP Suite — V0.0.1-RC16 PFMP Manager complet

Type : **upgrade classique**. Cette livraison modifie la base PFMP Manager et nécessite migrations Django.

## Contenu

- Entreprises géolocalisables et filtrables.
- Contacts associés aux entreprises avec visibilité professeur/élève.
- Règle élève : seuls les e-mails des contacts sont affichés.
- Adresse personnelle contact facultative, masquée aux élèves, utilisable comme point de proximité.
- Bouton `Ajouter à ma recherche` depuis la fiche entreprise et la carte.
- Suivi de recherche élève par période PFMP.
- Actions horodatées avec type, état, commentaire, suite à donner.
- Export PDF du tableau récapitulatif de recherche.
- Import XLSX entreprises/contacts : simulation, ajout, upsert, remplacement total.
- Correction du marqueur carte Leaflet par fallback CSS + images statiques.

## Après application du patch

```bash
bash scripts/migrate_all.sh
bash scripts/collectstatic_all.sh
docker compose --env-file .env restart
```

## Import XLSX fourni

Le fichier de base est installé dans :

```text
imports/pfmp_manager_base_entreprises_fusionnee.xlsx
```

Simulation :

```bash
bash scripts/pfmp_rc16_import_companies.sh simulation code_entreprise
```

Import ajout/mise à jour :

```bash
bash scripts/pfmp_rc16_import_companies.sh upsert code_entreprise
```

Remplacement total :

```bash
bash scripts/pfmp_rc16_import_companies.sh replace_all code_entreprise 'CONFIRMER IMPORT DESTRUCTIF'
```

## URL principales

```text
/pfmp/entreprises/
/pfmp/entreprises/import/
/pfmp/carte/
/pfmp/mes-recherches/
```

## Points de vigilance

- Le géocodage automatique n'est pas activé : les colonnes latitude/longitude sont importées si présentes.
- Les contacts avec adresse personnelle ne doivent jamais afficher l'adresse aux élèves.
- Un contact peut être utilisé comme point de proximité si `use_personal_location_for_student_search=True`.
