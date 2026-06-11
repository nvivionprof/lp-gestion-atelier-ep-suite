# README développeur — LP Gestion Atelier EP Suite

Document vivant à maintenir à chaque évolution structurante de la suite.

Version concernée : **Bêta V0.0.1**.

## 1. Philosophie générale

LP Gestion Atelier EP Suite est une suite applicative pédagogique découpée en modules Django indépendants, orchestrés par Docker et exposés par une passerelle Nginx unique.

L'objectif prioritaire est la **maintenabilité en établissement scolaire** : installation reproductible, code lisible, séparation nette des responsabilités, sauvegarde/restauration exploitable après crash serveur, et évolutions possibles module par module.

Les choix techniques doivent toujours privilégier :

- la compréhension par un développeur Django junior ou intermédiaire ;
- la traçabilité des règles métier ;
- la robustesse sur réseau local et serveur lycée ;
- la possibilité de revenir en arrière après une mise à jour ;
- la compatibilité avec un usage téléphone/tablette en atelier.

## 2. Architecture fonctionnelle

La suite est composée des modules suivants :

| Module | Responsabilité principale |
|---|---|
| LP Core | portail, utilisateurs, droits transversaux, URLs publiques, HTTPS, sauvegardes |
| ToolMag | outillage, sorties, retours, inventaires, interventions |
| Safety Manager | DUERP, situations dangereuses, événements sécurité, actions de prévention |
| PedaShop | consommables, stocks multi-magasins, bons, réservations, commandes |
| System Manager | systèmes pédagogiques, zones, réservations, QR codes, prises de poste |
| TP Manager | base documentaire TP, parcours élèves, traces, compétences |
| lp-gateway | reverse proxy Nginx, routage HTTP/HTTPS, certificats |

## 3. Architecture de publication

Depuis la Bêta V0.0.1, le mode recommandé est le reverse proxy unique :

```text
/              -> LP Core
/toolmag/      -> ToolMag
/safety/       -> Safety Manager
/pedashop/     -> PedaShop
/system/       -> System Manager
/tpmanager/    -> TP Manager
```

En local WSL :

```text
http://localhost:9000/
```

En production lycée :

```text
https://nom.duckdns.org/
```

Le certificat HTTPS est attaché au **domaine** et non aux sous-pages. Un certificat pour `nom.duckdns.org` couvre donc tous les chemins applicatifs.

## 4. Règle de séparation des responsabilités

### LP Core

LP Core est le référentiel transversal. Il centralise :

- les utilisateurs ;
- les rôles principaux ;
- les classes, formations, groupes ;
- les droits transversaux ;
- les magasins accessibles ;
- les habilitations/certifications ;
- les règles de visibilité des modules ;
- les paramètres publics HTTP/HTTPS ;
- les sauvegardes/restaurations globales.

LP Core ne doit pas contenir les règles métier fines de chaque module. Exemple : LP Core peut décider qu'un élève voit PedaShop ; PedaShop décide ensuite ce que cet élève peut faire dans PedaShop.

### Modules métier

Chaque module conserve :

- ses modèles Django métier ;
- ses vues ;
- ses templates ;
- ses fichiers statiques ;
- ses règles métier internes ;
- ses imports/synchronisations depuis LP Core.

Le couplage entre modules doit rester explicite et documenté.

## 5. Politique de commentaires dans le code

Le code ne doit pas être commenté ligne par ligne. Cela rendrait le projet plus lourd et moins lisible.

À commenter obligatoirement :

- les décisions d'architecture ;
- les règles métier non évidentes ;
- les contournements techniques ;
- les interactions entre modules ;
- les scripts d'installation, sauvegarde, restauration et HTTPS ;
- les migrations ajoutant un comportement fonctionnel important.

À ne pas commenter inutilement :

- une affectation simple ;
- un `return` évident ;
- une boucle dont le nom de variable explique déjà l'intention ;
- du code standard Django sans règle métier spécifique.

Exemple attendu :

```python
# Une règle explicite de visibilité remplace les rôles par défaut.
# Cela permet de masquer un module à toute une population sans modifier
# les permissions internes du module métier.
```

Exemple à éviter :

```python
# On retourne False
return False
```

## 6. Conventions de nommage

### Utilisateurs

Les codes utilisateurs doivent rester stables, car ils servent à synchroniser les modules.

Format recommandé :

```text
FORMATION-NOM3-PRE3
```

Exemple :

```text
MELEC-DUP-JEA
```

### Droits

Les droits transversaux doivent être écrits en majuscules avec préfixe module :

```text
CORE_ADMIN
TOOLMAG_VIEW
TOOLMAG_STOREKEEPER
SAFETY_VIEW
PEDASHOP_VIEW
SYSTEM_VIEW
TPMANAGER_VIEW
```

À terme, les droits textuels séparés par `;` devront être remplacés par une table ManyToMany normalisée.

### Variables d'environnement

Les variables publiques doivent rester explicites :

```env
LP_DEPLOY_MODE=local|production
PUBLIC_SCHEME=http|https
PUBLIC_DOMAIN=localhost|nom.duckdns.org
EXPOSURE_MODE=reverse_proxy|direct_ports
ENABLE_HTTPS=0|1
```

## 7. Règles de développement frontend

L'interface doit rester simple, lisible et exploitable sur téléphone/tablette.

Principes :

- boutons d'action visibles ;
- libellés explicites ;
- tableaux lisibles mais pas surchargés ;
- formulaires courts quand c'est possible ;
- regroupement des fonctions d'administration ;
- messages d'erreur compréhensibles par un enseignant non développeur.

### Champs photo et caméra mobile

Tous les champs photo doivent utiliser le composant transversal `camera_upload.js`.

Le composant crée deux chemins utilisateur :

```text
Prendre une photo   -> champ fichier avec capture=environment
Choisir une photo   -> champ fichier galerie classique
```

Raison : selon les téléphones et navigateurs, un simple champ :

```html
<input type="file" accept="image/*" capture="environment">
```

peut ouvrir seulement la galerie, seulement la caméra, ou un sélecteur incomplet. Le composant évite ce comportement instable.

Source de référence :

```text
shared-camera/camera_upload.js
```

Copies utilisées par les modules :

```text
lp-core-app/core/static/core/camera_upload.js
toolmag-app/inventory/static/inventory/camera_upload.js
safety-app/safety_manager/static/safety_manager/camera_upload.js
pedashop-app/pedashop/static/pedashop/camera_upload.js
system-manager-app/system_manager/static/system_manager/camera_upload.js
tpmanager-app/tp_manager/static/tp_manager/camera_upload.js
```

Quand le composant évolue, mettre à jour la source `shared-camera/`, puis recopier dans chaque module.

## 8. Règles de développement Django

### Vues

Les vues doivent rester orientées orchestration :

- lecture des paramètres de requête ;
- appel des formulaires/services ;
- contrôle des droits ;
- rendu de template ;
- journalisation si nécessaire.

Les calculs métier longs doivent aller dans des fonctions de service dédiées.

### Formulaires

Les formulaires portent :

- les libellés utilisateur ;
- les widgets ;
- les validations simples ;
- les aides contextuelles.

Ils ne doivent pas porter des workflows complets de stock, sécurité ou réservation.

### Modèles

Les modèles portent :

- les contraintes de structure ;
- les constantes de choix ;
- les propriétés métier simples ;
- les méthodes très proches de la donnée.

Les traitements multi-objets doivent aller dans des services.

## 9. Gestion HTTPS

La gestion HTTPS doit être centralisée sur `lp-gateway`.

LP Core peut fournir l'interface d'administration, mais la terminaison TLS est réalisée par Nginx.

Deux modes sont acceptés :

1. **import manuel** : `fullchain.pem` + `privkey.pem` ;
2. **Let's Encrypt** : génération/renouvellement avec challenge HTTP-01 ou DNS DuckDNS.

À diagnostiquer systématiquement en cas d'échec :

- domaine DuckDNS renseigné ;
- résolution DNS vers la bonne IP publique ;
- redirection box port 80 vers le serveur ;
- redirection box port 443 vers le serveur ;
- présence des fichiers certificat ;
- rechargement du conteneur `lp-gateway`.

## 10. Sauvegarde et restauration

Une sauvegarde complète doit contenir :

- bases de données ;
- médias ;
- documents ;
- certificats HTTPS ;
- `.env` ;
- configuration Nginx ;
- métadonnées de version ;
- manifest de sauvegarde.

Après crash serveur, l'objectif est de pouvoir réinstaller la suite puis réinjecter la sauvegarde pour retrouver l'état fonctionnel précédent.

## 11. Tests minimaux avant livraison d'une archive

Avant de livrer un ZIP, vérifier au minimum :

```bash
python -m compileall <module>
bash -n install.sh
bash -n scripts/*.sh
python - <<'PY'
import yaml
yaml.safe_load(open('docker-compose.yml'))
PY
```

Puis, sur une machine avec Docker :

```bash
docker compose config
docker compose up -d --build
docker compose ps
```

Tester ensuite :

- connexion LP Core ;
- portail connecté ;
- accès à chaque module ;
- fichiers statiques ;
- upload photo depuis galerie ;
- upload photo depuis caméra téléphone ;
- sauvegarde ;
- restauration ;
- génération ou import certificat en production.

## 12. Mise à jour de ce document

Ce document doit être mis à jour à chaque fois qu'une modification touche :

- l'architecture Docker ;
- Nginx ;
- HTTPS ;
- les permissions transversales ;
- les sauvegardes/restaurations ;
- les conventions de données ;
- les composants frontend partagés ;
- le mode d'installation.

Ne pas laisser ce README devenir historique : les détails obsolètes doivent être déplacés dans `docs/historique_versions/`.

## Note exploitation — TP Manager

La procédure d'installation depuis `/home` et la récupération manuelle d'une base TP Manager sans interface web d'import/export sont documentées dans :

```text
docs/INSTALLATION_HOME_ET_RECUPERATION_TPMANAGER.md
```

Cette documentation doit être maintenue si le nom du service `tpmanager-app`, le chemin `/data/tpmanager/tp-manager.sqlite3` ou le volume `./tpmanager-db/data` changent.


## Politique RGPD et sauvegardes

Le cahier des charges RGPD est maintenu dans `docs/CAHIER_DES_CHARGES_RGPD.md`. Toute évolution qui ajoute une donnée personnelle, un document utilisateur, une trace sensible ou une nouvelle durée de conservation doit mettre à jour ce document.

Les paramètres opérationnels de sauvegarde sont portés par LP Core dans `BackupPolicySettings`. LP Core génère `lp-core-db/data/backup-policy.env`, lu dynamiquement par `suite-backup-scheduler` et par les scripts de mise à jour.

Règle impérative : une mise à jour complète ne doit pas modifier la production tant qu’une sauvegarde complète pré-mise-à-jour n’a pas été créée avec succès, sauf contournement volontaire en SSH et assumé par l’administrateur.
