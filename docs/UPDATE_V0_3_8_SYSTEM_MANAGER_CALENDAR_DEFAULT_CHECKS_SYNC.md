# V0.3.8 — System Manager : calendrier zones, checks par défaut, synchronisation encadrée

## Ajouts

- Filtre du calendrier par zone atelier et sous-zone.
- Cascade zone → sous-zone dans le calendrier.
- Conteneur `00 - Checks par défaut` masqué aux élèves sans droit de création/modification.
- Page `Paramétrage > Checks par défaut du module` : création, modification et suppression par lot.
- Les checks par défaut sont appliqués à chaque nouveau système créé.
- Téléchargement des originaux DOCX/XLSX/PPTX réservé aux professeurs, administrateurs ou créateurs/modificateurs autorisés.
- Prévisualisation PDF conservée pour la lecture navigateur.
- Deux boutons de synchronisation distincts avec confirmation : `LP Core → System Manager` et `System Manager → LP Core`.

## Remarque

La synchronisation `System Manager → LP Core` nécessite que LP Core expose l’API `/api/system-manager/referentials/import/`. Si l’API n’existe pas encore côté LP Core, l’action échoue proprement avec un message d’erreur sans modifier System Manager.
