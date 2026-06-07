# LP Gestion Atelier EP Suite — V2.7.1

## Type de livraison

**Installation complète conseillée.**

Cette archive repart de la V2.7 fournie et intègre des corrections de stabilité ainsi qu'une évolution structurante de TP Manager. Elle modifie le `docker-compose.yml`, LP Core, TP Manager, les migrations et les données de démonstration.

## Corrections principales

1. Correction du doublon `PEDASHOP_INTERNAL_SYNC_URL` dans `docker-compose.yml`.
2. Compte LP Core natif créé par défaut : `admin` / `admin`, distinct de l'administration Django `/admin/`.
3. Ajout du champ `force_password_change` dans LP Core et redirection vers `Mon compte` lors de la première connexion si le mot de passe initial doit être changé.
4. Préparation de nouveaux droits LP Core : `TP_ELEVE_CONTRIBUTEUR` et `TP_REFERENTIEL_ADMIN`.
5. Conservation du mécanisme de sauvegarde/restauration et des scripts existants de reprise après crash.

## Évolution TP Manager

TP Manager évolue d'un gestionnaire documentaire vers un outil de pilotage pédagogique :

- conservation des appellations officielles propres aux diplômes ;
- modèle homogène pour CAP, Bac Pro et BTS ;
- ajout des pôles d'activités, unités certificatives, savoirs associés, critères et indicateurs ;
- liaison tâches / compétences ;
- liaison TP / tâches, TP / savoirs, TP / critères ;
- distinction des compétences `mobilisée`, `travaillée`, `dominante`, `évaluée`, `certificative` ;
- listes pédagogiques locales extensibles depuis le formulaire TP : zone, thème général, sous-thème, type de TP ;
- droits temporaires de contribution élève encadrés par professeur ;
- brouillons élèves non publiables directement.

## Base de démonstration TP Manager

Le chargement `seed_tp_manager` crée désormais :

- niveaux : 2nde, 1ère, terminale, CAP1/CAP2, BTS1/BTS2 ;
- formations : MTNE, CIEL, MELEC, MFER, CAP Électricien, BTS FED, BTS Électrotechnique ;
- zones : FORM, MAINT, MES, ECQU, INT, CHA ;
- thèmes et sous-thèmes techniques ;
- référentiels synthétiques exploitables pour CAP Électricien, Bac Pro CIEL, Bac Pro MFER, BTS FED et BTS Électrotechnique ;
- unités certificatives, pôles, activités, tâches, blocs, compétences, savoirs, critères et indicateurs ;
- 3 TP de démonstration : MELEC, CIEL et FED.

## Vérifications effectuées hors Docker

- `python manage.py check` validé sur LP Core, ToolMag, Safety Manager, PedaShop, System Manager et TP Manager.
- Migrations LP Core et TP Manager générées et testées sur SQLite local.
- Parsing YAML du `docker-compose.yml` validé avec PyYAML ; `PEDASHOP_INTERNAL_SYNC_URL` n'apparaît plus qu'une seule fois.

## Limite de vérification

Docker n'est pas disponible dans l'environnement de génération : la commande `docker compose config` n'a pas pu être exécutée ici. La syntaxe YAML a cependant été validée par parseur Python.
