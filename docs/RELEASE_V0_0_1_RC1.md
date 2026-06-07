# Release V0.0.1-RC1

## Statut

Release candidate d’exploitation encadrée.

## Priorités

1. ToolMag.
2. System Manager en base système minimale.
3. PedaShop.

## Ergonomie

- Mobile uniquement pour : prise de poste, inventaire ToolMag, photo.
- PC/tablette pour le reste.

## Sécurité exploitation

- Mises à jour applicatives uniquement SSH/Git/wget GitHub.
- Sauvegarde/restauration bases possible depuis LP Core.
- Sauvegarde obligatoire avant update/upgrade.
- Commande de reprise : `./scripts/restore_last_backup.sh --yes`.

## Décision de sortie

Passage en V0.0.1 finale après validation de la checklist `CHECKLIST_RECETTE_RC_V0_0_1.md`.
