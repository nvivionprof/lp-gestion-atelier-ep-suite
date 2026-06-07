# Checklist recette V0.0.1-RC1

## Installation

- [ ] `./install.sh --mode install` fonctionne.
- [ ] Le mot de passe PostgreSQL est demandé.
- [ ] Le compte admin LP Core est demandé.
- [ ] Les migrations passent sans erreur bloquante.
- [ ] La question base démo apparaît uniquement en `install`.
- [ ] `docker compose ps` ne montre pas de conteneur critique en échec.

## Sauvegarde / reprise

- [ ] `./scripts/full_backup.sh manual` fonctionne.
- [ ] `./scripts/restore_last_backup.sh --dry-run` fonctionne.
- [ ] La commande d’urgence est connue : `./scripts/restore_last_backup.sh --yes`.

## ToolMag

- [ ] Tableau de bord accessible.
- [ ] Liste matériel accessible.
- [ ] Fiche matériel accessible.
- [ ] Sortie matériel testée.
- [ ] Retour matériel testé.
- [ ] Inventaire utilisateur lisible sur téléphone.
- [ ] Photo matériel utilisable.
- [ ] Aucun écran principal en erreur 500.

## System Manager

- [ ] Tableau de bord accessible.
- [ ] Liste systèmes accessible.
- [ ] Fiche système accessible.
- [ ] Documents système consultables.
- [ ] Prise de poste téléphone testée.
- [ ] Photo système utilisable.
- [ ] QR code / lien direct testé.
- [ ] Aucun écran principal en erreur 500.

## PedaShop

- [ ] Tableau de bord accessible.
- [ ] Stock accessible.
- [ ] Liste articles accessible.
- [ ] Fiche article accessible.
- [ ] Documents / médias consultables.
- [ ] Recherche simple testée.
- [ ] Aucun écran principal en erreur 500.

## Décision

- [ ] Passage possible en V0.0.1 finale.
- [ ] Passage refusé : conserver V0.0.1-RC1 et corriger en V0.0.1-RC2.
