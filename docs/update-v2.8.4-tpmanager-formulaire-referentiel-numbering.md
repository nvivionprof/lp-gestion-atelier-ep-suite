# LP Gestion Atelier Suite v2.8.4 — TP Manager formulaire référentiel et numérotation

## Type de version

Installation complète / mise à jour SSH. Compatible avec `upgrade.sh` et `upgrade_module.sh` introduits en v2.8.3.

## Modifications TP Manager

- Reprise de la page `http://localhost:9005/tps/creer/?diplome=...`.
- Le diplôme n’est plus affiché comme champ modifiable : il est fixé par le choix initial et conservé côté serveur.
- Affichage d’un cadre de création proche du modèle fourni : titre, thème principal, sous-thème, nom automatique, type, usage, durée, résumé élève, contexte et problématique métier.
- Repère automatique basé sur le code formation :
  - Bac Pro CIEL → `CIEL`
  - Bac Pro MELEC → `MELEC`
  - Bac Pro MFER → `MFER`
  - BTS FED → `FED`
  - BTS Électrotechnique → `STEL`
- Numérotation serveur au format `FORMATION-TYPE-CLASSE-DOMAINE-001`.
- Les champs marqués par `*` utilisent des listes avec ajout manuel possible : thème principal, sous-thème et type.
- Ajout du champ `sous_theme`.
- Ajout du champ `problematique_metier`.
- Les compétences pivot et mots-clés parcours ne sont plus dans le premier formulaire de création ; ils restent affichés sur la fiche TP.
- Normalisation des compétences officielles au format `C01`, `C02`, etc. pour éviter les tris incorrects.

## Migration

Migration additive : `0004_tpv2_form_numbering_and_comp_codes.py`.

Elle ajoute les champs nécessaires et renomme les codes de compétences existants de type `C1` à `C9` en `C01` à `C09`.

## Installation

Mise à jour complète :

```bash
./upgrade.sh /chemin/lp-gestion-atelier-ep-suite-v2.8.4-tpmanager-formulaire-referentiel-numbering.zip
```

Mise à jour ciblée TP Manager après installation de la v2.8.3 ou supérieure :

```bash
./upgrade_module.sh tpmanager /chemin/lp-gestion-atelier-ep-suite-v2.8.4-tpmanager-formulaire-referentiel-numbering.zip
```
