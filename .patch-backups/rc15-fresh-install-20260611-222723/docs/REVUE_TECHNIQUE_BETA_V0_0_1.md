# Revue technique — LP Gestion Atelier EP Suite Bêta V0.0.1

## Corrections réalisées

- Passage à une passerelle unique `lp-gateway` au lieu d’un accès principal par ports séparés.
- Ajout du routage Nginx par chemins : `/toolmag/`, `/safety/`, `/pedashop/`, `/system/`, `/tpmanager/`.
- Ajout d’un mode local HTTP et d’un mode production HTTPS/DuckDNS.
- Centralisation du certificat dans le volume `ssl` et dans le conteneur Nginx.
- Ajout de l’import manuel `fullchain.pem` / `privkey.pem` depuis LP Core.
- Modification du challenge HTTP-01 pour utiliser le webroot Nginx au lieu d’un conteneur standalone qui entre en conflit avec le port 80.
- Ajout du support `APP_URL_PREFIX` / `FORCE_SCRIPT_NAME` dans les modules Django.
- Ajout des règles de visibilité des modules dans LP Core.
- Correction du doublon PedaShop dans la synchronisation globale LP Core.
- Nettoyage de l’accueil : portail authentifié, fiche personnelle, modules visibles, administration regroupée.
- Homogénéisation des versions affichées en `Bêta V0.0.1`.
- Ajout d’une source commune `shared-camera/camera_upload.js` à recopier dans les modules quand le composant évolue.
- Ajout de `docs/README_DEVELOPPEUR.md` comme document vivant de philosophie de programmation, conventions et règles de maintenance.
- Ajout du composant transversal `camera_upload.js` pour fiabiliser la prise de photo depuis téléphone et conserver un choix galerie séparé.

## Points à tester après installation

1. Connexion `admin/admin` sur `http://localhost:9000/`.
2. Changement obligatoire du mot de passe LP Core.
3. Accès portail avec un élève démo `USR-0001/user0001`.
4. Vérification des modules visibles pour élève : ToolMag, Safety, PedaShop, System Manager.
5. Vérification que TP Manager reste visible pour professeur/admin ou selon règle explicite.
6. Vérification des fichiers statiques derrière `/toolmag/`, `/safety/`, `/pedashop/`, `/system/`, `/tpmanager/`.
7. En production : vérifier la redirection box 80/443 puis l’état certificat dans LP Core.

8. Vérification sur téléphone : bouton “Prendre une photo” sur les champs photo LP Core, ToolMag, PedaShop, System Manager et TP Manager.
9. Vérification sur téléphone : bouton “Choisir une photo” ouvrant la galerie sans bloquer la caméra.
10. Vérification du champ trace photo dans TP Manager après sélection du type de trace `photo`.

## Optimisations recommandées ensuite

- Mettre en place une vraie authentification SSO intermodules pour éviter une reconnexion dans chaque application.
- Remplacer progressivement les champs `rights` en texte `;` par une table ManyToMany de droits normalisée.
- Ajouter une page de diagnostic externe réelle DNS/port 80/443 depuis un service distant, car le serveur ne peut pas toujours tester sa propre accessibilité WAN.
- Ajouter des tests Django automatisés par module pour les routes critiques.
- Passer à PostgreSQL si le volume de données augmente fortement ou si plusieurs utilisateurs manipulent simultanément les stocks.
- Ajouter une politique de logs structurés avec rotation côté Docker.
- Distinguer installation complète, patch web simple et patch module dans le manifest des prochaines versions.


## RGPD / sauvegardes paramétrables

Ajout du cahier des charges RGPD et d’une politique de sauvegarde pilotée par LP Core : durée/heure paramétrables, 7 jours glissants par défaut pour les sauvegardes quotidiennes, sauvegardes manuelles sans suppression automatique, restauration web de sauvegardes serveur, sauvegarde pré-mise-à-jour obligatoire et blocage en cas d’échec selon paramétrage.
