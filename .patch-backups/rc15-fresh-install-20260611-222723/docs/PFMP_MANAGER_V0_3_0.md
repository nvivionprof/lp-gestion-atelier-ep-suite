# PFMP Manager — Bêta V0.3.0

Ajout du module PFMP Manager intégré à LP Gestion Atelier EP Suite.

## V1 active
- entreprises, contacts par formation et visibilité ;
- carte/fiches entreprises type fiche synthétique ;
- périodes PFMP ;
- affectations élèves ;
- suivi des démarches CV, lettre, appel, mail, visite ;
- synchronisation LP Core ;
- aide et à propos cohérents avec la suite.

## Socle V2 préparé
- annonces entreprises : PFMP, alternance, emploi, job étudiant, événement ;
- champs de mobilité, permis, véhicule, transports, profil attendu ;
- statuts brouillon, attente, publiée, expirée, archivée.

## Portail
Route externe : `/pfmp/`.

Les scripts install.sh et upgrade.sh recréent désormais lp-core-app + lp-gateway et lancent verify_portal_routes.sh en fin d'installation/mise à jour.
