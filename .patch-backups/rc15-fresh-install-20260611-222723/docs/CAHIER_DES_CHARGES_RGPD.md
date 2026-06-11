# Cahier des charges RGPD — LP Gestion Atelier EP Suite

Version : Bêta V0.0.1 — mise à jour RGPD / sauvegardes

## 1. Objectif

Le présent cahier des charges décrit les exigences RGPD applicables à LP Gestion Atelier EP Suite : LP Core, ToolMag, PedaShop, TP Manager, Safety Manager, System Manager et les modules futurs.

La suite est utilisée dans un contexte scolaire avec des élèves, dont des mineurs. Les traitements doivent donc rester strictement nécessaires à l’organisation pédagogique, à la traçabilité atelier, à la sécurité et à la gestion des matériels.

## 2. Principes retenus

- Minimisation : ne collecter que les données nécessaires.
- Information : l’utilisateur voit un écran RGPD à la première connexion et confirme qu’il en a pris connaissance.
- Mineurs : l’écran RGPD ne remplace pas le papier signé par les représentants légaux.
- Droit à l’image : photo facultative, refus sans conséquence pédagogique.
- Blocage élève : les élèves, notamment mineurs, ne peuvent pas téléverser librement leur photo ou leurs documents personnels si le dossier RGPD le bloque.
- Traçabilité : les actions sensibles sont journalisées.
- Sauvegarde : restauration possible sans perte de données, mais accès réservé aux administrateurs habilités.

## 3. Données traitées

### 3.1 LP Core

- Identité : nom, prénom, identifiant, code utilisateur.
- Scolarité : classe, formation, groupe, année scolaire.
- Droits : rôle principal, droits par module, magasins accessibles, habilitations/certifications.
- Compte : mot de passe haché, obligation éventuelle de changement de mot de passe.
- RGPD : statut d’autorisation image, opposition parentale, blocage d’upload personnel.

### 3.2 Modules métier

Les modules reçoivent uniquement les données nécessaires à leur fonctionnement : utilisateur, classe, formation, rôle, droits, magasins ou périmètres autorisés.

## 4. Photos et documents personnels

### 4.1 Photo

- La photo est facultative.
- Le statut doit être explicite : non renseigné, autorisé, refusé/opposition.
- Si opposition ou absence d’autorisation parentale, afficher : « L’utilisateur n’a pas souhaité diffuser son image. »
- Pour les mineurs, l’autorisation image est fondée sur le document papier signé par les représentants légaux.

### 4.2 Documents personnels

- Les élèves ne doivent pas pouvoir téléverser librement photo ou documents personnels si `personal_upload_blocked` est actif.
- Les documents PFMP, CV, autorisations ou attestations doivent rester accessibles uniquement aux personnes habilitées.

## 5. Gestion par lot

LP Core doit permettre aux administrateurs habilités d’appliquer par lot :

- statut droit à l’image ;
- opposition parentale ;
- blocage d’upload photo/documents ;
- droits par module ;
- magasins accessibles ;
- habilitations/certifications.

Filtres minimaux : classe, formation, groupe, fonction, utilisateur.

## 6. Durées de conservation

Paramètres par défaut :

- Logs techniques : 90 jours, sauf obligation interne différente.
- Sauvegardes quotidiennes : 7 jours glissants par défaut, paramétrable dans LP Core.
- Sauvegardes manuelles : conservation sans suppression automatique.
- Sauvegardes pré-mise-à-jour : conservation sans suppression automatique, afin de permettre un retour arrière.
- Données scolarité : durée utile à la scolarité et à la traçabilité pédagogique interne.
- Droit à l’image / autorisations : conservation pendant la scolarité et durée raisonnable de preuve.

## 7. Sauvegarde, restauration et mise à jour

Toute mise à jour complète doit :

1. Créer une sauvegarde complète pré-mise-à-jour.
2. Vérifier que l’archive existe et contient un manifest.
3. Bloquer la mise à jour si la sauvegarde échoue lorsque l’option est active.
4. Permettre un retour arrière via script ou interface LP Core.

L’interface LP Core doit permettre :

- réglage de l’heure quotidienne ;
- réglage de la durée de conservation ;
- sauvegarde manuelle ;
- restauration d’un ZIP externe ;
- restauration d’une sauvegarde présente sur le serveur ;
- activation/désactivation de la restauration web.

## 8. Accès et habilitations

- Les administrateurs gèrent tous les paramètres.
- Les professeurs habilités accèdent aux données pédagogiques nécessaires.
- Les élèves voient leur fiche et leurs données utiles, pas la liste complète des utilisateurs.
- Les modules ne doivent pas exposer de données hors périmètre de classe, groupe, magasin ou rôle.

## 9. Journalisation

Actions sensibles à journaliser :

- connexion / première prise de connaissance RGPD ;
- modification des droits ;
- import utilisateurs ;
- synchronisation modules ;
- modification droit à l’image ;
- blocage/déblocage upload personnel ;
- création/restauration sauvegarde ;
- mise à jour complète ;
- import/export SQL ou base.

## 10. Exigences de développement

- Toute nouvelle fonctionnalité manipulant des données personnelles doit être documentée ici.
- Toute nouvelle donnée personnelle doit avoir une finalité, une durée de conservation et un périmètre d’accès.
- Toute mise à jour complète doit être précédée d’une sauvegarde vérifiée.
- Les scripts doivent préserver les bases existantes sauf action explicite de restauration.
