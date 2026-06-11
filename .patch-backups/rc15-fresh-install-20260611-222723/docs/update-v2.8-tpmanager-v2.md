# Mise à jour v2.8.0 — TP Manager V2

## Type de livraison

Cette archive est une **installation complète / mise à jour SSH de la suite**. Elle repart du ZIP fonctionnel `v2.7.2-correctif-install-demo` et ajoute une refonte fonctionnelle de TP Manager.

Elle n'est pas une simple mise à jour web isolée : elle contient des modèles Django, migrations et commandes de seed.

## Périmètre

- Refonte fonctionnelle de TP Manager en V2.
- Conservation de l'identité visuelle existante : base HTML, CSS, couleurs, navigation, logo et logique générale d'interface.
- Aucune modification destructive de ToolMag, PedaShop, Safety Manager ou System Manager.
- Ajout de tables V2 en parallèle des anciennes tables TP Manager.

## Règles pédagogiques implémentées

- Le choix du diplôme pilote les champs proposés lors de la création d'un TP.
- Les référentiels officiels CIEL / MFER / MELEC sont chargés dans des tables verrouillées.
- Depuis l'écran de création/adaptation du TP, le professeur peut sélectionner les compétences officielles du diplôme choisi, mais ne les modifie pas.
- Le professeur peut ajouter uniquement :
  - des critères de réussite propres au TP ;
  - des critères d'évaluation finale propres au TP.
- La duplication inter-référentiel crée une copie brouillon et impose de revalider les compétences officielles du diplôme cible.

## Ressources optionnelles

Un TP peut référencer, sans obligation :

- des systèmes de System Manager ;
- des outils ou appareils de mesure de ToolMag ;
- du matériel ou des consommables de PedaShop ;
- une ressource manuelle non encore présente dans la suite.

La logique de ressources est organisée en groupes :

- `ALL` = ET : toutes les ressources du groupe sont nécessaires ;
- `ANY` = OU : une seule ressource du groupe suffit.

TP Manager ne modifie pas les données des modules source. Il stocke uniquement des références.

## Base démo et seed

La commande `seed_tpmanager_v2` charge les référentiels Bac de manière idempotente et non destructive.

Elle ne supprime pas :

- les TP existants ;
- les documents ;
- les critères professeur ;
- les ressources ;
- les données ToolMag / PedaShop / System Manager.

## Installation / mise à jour

Depuis le dossier déjà installé sur le serveur :

```bash
./upgrade.sh /chemin/lp-gestion-atelier-ep-suite-v2.8.0-tpmanager-v2.zip
```

Ou en installation neuve :

```bash
unzip lp-gestion-atelier-ep-suite-v2.8.0-tpmanager-v2.zip
cd lp-gestion-atelier-ep-suite
./install.sh
```

## Contrôle après installation

```bash
docker compose ps
docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py seed_tpmanager_v2
docker compose exec -T tpmanager-app python manage.py check
```

