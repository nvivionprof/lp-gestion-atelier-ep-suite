# Feuille de route V0.0.1-RC1

## Objectif

Passer en **release candidate V0.0.1-RC1** pour une exploitation encadrée avec les élèves.

La priorité est de stabiliser trois fonctions :

1. **ToolMag** : outillage, sorties/retours, inventaire utilisateur et QR code.
2. **System Manager** : base système minimale, documentation, QR code et prise de poste.
3. **PedaShop** : consultation des ressources, articles, stock et documents associés.

Les autres modules restent présents, mais ne sont pas bloquants pour la RC.

## Périmètre prioritaire

### ToolMag

Validation minimale :

- liste du matériel accessible ;
- fiche matériel accessible ;
- sortie et retour utilisables ;
- inventaire utilisateur lisible sur téléphone ;
- QR code / lien direct fonctionnel ;
- photo matériel utilisable lors de création ou modification ;
- historique des mouvements consultable.

### System Manager

Validation minimale :

- liste des systèmes accessible ;
- fiche système accessible ;
- zone / sous-zone visibles ;
- documents associés consultables ;
- QR code ou lien direct système fonctionnel ;
- prise de poste utilisable sur téléphone ;
- photo système utilisable lors de création ou modification.

La réservation avancée n’est pas bloquante pour la RC.

### PedaShop

Validation minimale :

- liste des articles / ressources accessible ;
- stock consultable ;
- fiche article accessible ;
- documents et médias consultables ;
- magasin ou emplacement visible ;
- recherche simple utilisable.

## Non bloquant pour V0.0.1-RC1

- PFMP complet et cartes avancées ;
- TP Manager complet ;
- Safety Manager complet ;
- réservation avancée par blocs ;
- statistiques avancées ;
- perfection mobile de tous les écrans.

## Passage RC1 vers V0.0.1 finale

La version peut passer en V0.0.1 finale si :

- aucune erreur 500 sur les pages principales des trois modules prioritaires ;
- installation PostgreSQL complète validée ;
- migrations automatiques validées ;
- sauvegarde complète créée ;
- restauration `restore_last_backup.sh --dry-run` validée ;
- ToolMag, System Manager et PedaShop sont exploitables en conditions réelles.
