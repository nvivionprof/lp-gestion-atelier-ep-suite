# Mise à jour v2.8.1 — TP Manager V2 : bases BTS FED et BTS Électrotechnique

## Nature de la mise à jour

Cette mise à jour complète la refonte TP Manager V2 en ajoutant les bases de référentiels :

- **BTS Électrotechnique** ;
- **BTS Fluides Énergies Domotique — options GCF, FCA, DBC**.

Elle est non destructive : elle ne modifie pas ToolMag, PedaShop, Safety Manager ou System Manager.

## Principe conservé

Les termes officiels du référentiel restent prioritaires. La couche pivot ne sert qu’à :

- rechercher ;
- proposer des transferts ;
- dupliquer un TP vers un autre diplôme ;
- lisser l’interface utilisateur.

La couche pivot ne remplace jamais les blocs, unités ou compétences du référentiel cible.

## Bases ajoutées

### BTS Électrotechnique

Sources : `12188-referentiel-bts-electrotechnique.pdf`.

Base intégrée :

- 5 pôles : conception étude préliminaire, conception étude détaillée, conduite de projet/chantier, réalisation/mise en service, analyse/diagnostic/maintenance ;
- 5 unités professionnelles : U4, U51, U52, U61, U62 ;
- 18 compétences officielles C1 à C18 ;
- 5 champs dynamiques de création de TP.

### BTS FED

Sources : `3851-referentiel-bts-fed-mars14.pdf`.

Base intégrée :

- 5 fonctions : concevoir et définir, mettre en service/optimiser, conduire un projet, communiquer, assurer la relation client ;
- options GCF, FCA et DBC ;
- unités professionnelles U41, U42, U5, U61 et U62 ;
- 16 compétences officielles C1 à C16 ;
- 5 champs dynamiques de création de TP, dont le choix d’option GCF/FCA/DBC.

## Création de TP

Lorsqu’un professeur choisit un diplôme BTS dans TP Manager V2, les champs dynamiques proposés changent selon le diplôme :

- secteur ou phase projet pour BTS Électrotechnique ;
- option GCF/FCA/DBC et système support pour BTS FED.

Les compétences officielles sont sélectionnables mais non modifiables depuis la création d’un TP.

Le professeur peut ajouter uniquement :

- des critères de réussite ;
- des critères d’évaluation finale ;
- des documents et ressources associées ;
- des groupes de ressources optionnelles ET/OU.

## Transferts ajoutés

Des règles de transfert initiales sont ajoutées entre :

- MELEC ↔ BTS Électrotechnique ;
- MFER ↔ BTS FED ;
- CIEL ↔ BTS FED, notamment option DBC ;
- MELEC ↔ BTS FED, notamment bâtiment connecté / GTB ;
- BTS Électrotechnique ↔ BTS FED ;
- CIEL ↔ BTS Électrotechnique pour supervision, réseaux techniques et données.

Chaque transfert reste une proposition. Après duplication, les compétences du diplôme cible doivent être sélectionnées et validées manuellement.

## Commande de chargement

Après installation ou mise à jour :

```bash
python manage.py seed_tpmanager_v2
```

Dans Docker :

```bash
docker compose exec -T tpmanager-app python manage.py seed_tpmanager_v2
```

La commande est idempotente : elle met à jour les bases officielles et les règles de transfert sans supprimer les TP existants.

## Protection de la base démo

La base démo n’écrase pas les données réelles. Le chargement des référentiels par `seed_tpmanager_v2` ne supprime pas les TP, critères, documents ou ressources déjà créés.
