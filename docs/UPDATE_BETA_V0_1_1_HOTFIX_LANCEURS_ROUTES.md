# Bêta V0.1.1 — hotfix lanceurs LP Core et routage portail

- Lanceurs LP Core affichés en 3 colonnes sur grand écran.
- Logos homogènes et centrés dans la zone image.
- Texte des cartes harmonisé.
- URLs des lanceurs reconstruites depuis LP_CORE_PUBLIC_URL pour éviter les croisements de variables.
- Routage gateway vérifié : /toolmag, /safety, /pedashop, /system, /tpmanager pointent vers les bons conteneurs.
- Ajout du script `scripts/verify_portal_routes.sh` pour contrôler les en-têtes `X-LP-Gateway-Module`.
