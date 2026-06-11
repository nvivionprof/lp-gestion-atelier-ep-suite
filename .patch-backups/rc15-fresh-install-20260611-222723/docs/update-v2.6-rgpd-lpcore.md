# LP Gestion Atelier Suite V2.6 - Corrections LP Core et socle RGPD

## Type de livraison

- Type : mise à jour simple depuis LP Core > Mises à jour
- Compatible depuis : V2.5
- SSH nécessaire : non, sauf erreur ou dépannage
- Sauvegarde : obligatoire avant application
- Migration Django : oui, légère, LP Core uniquement

## Principales évolutions

### Page d’accueil LP Core

- Correction des logos ToolMag et Safety dans les tuiles : conteneur 90 x 54 px, centrage, pas de déformation.
- Suppression du bouton redondant « Ouvrir ToolMag » sous « Importer une base Excel ».
- Ajout de boutons de synchronisation vers : ToolMag, PedaShop, Safety Manager, System Manager, TP Manager et tous modules.

### Magasins / droits / certifications

- Le formulaire de magasin standard ne demande plus le module : les magasins sont créés en portée globale.
- Ajout d’un référentiel de droits paramétrable.
- Ajout d’un référentiel de types de certifications/habilitations.
- Correction affichage case « Actif ».

### Droits et actions par lot

- Droits sélectionnables par cases à cocher sur 3 colonnes.
- Affichage dynamique selon l’action sélectionnée : droits, magasins, certifications, droit à l’image.
- Gestion par lot de l’opposition parentale et du blocage des uploads photo/documents.

### Profil utilisateur et RGPD

- Ajout photo d’identité facultative.
- Ajout email personnel et téléphone personnel facultatifs.
- Ajout documents personnels pour future PFMP : CV, lettre de motivation, attestation, document PFMP.
- Statut droit à l’image : non renseigné, autorisé, refus/opposition.
- Si opposition parentale ou refus : message « L’utilisateur n’a pas souhaité diffuser son image. »
- Blocage possible de l’ajout photo/documents par l’utilisateur.
- Journalisation des actions sensibles.

### Centre RGPD

- Nouvelle page LP Core > RGPD.
- Conservation des logs techniques : année scolaire.
- Conservation des sauvegardes : 90 jours.
- Note RGPD/CNIL ajoutée : `docs/note-rgpd-cnil-v2.6.pdf`.

## Après mise à jour

Lancer les migrations depuis la page de mise à jour ou via :

```bash
./scripts/migrate_all.sh
```

Puis lancer la synchronisation de LP Core vers tous les modules depuis la page d’accueil LP Core.
