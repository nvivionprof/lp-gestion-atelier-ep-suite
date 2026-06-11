# LP Gestion Atelier Suite V2.7 — Sauvegarde et restauration complète après crash

## Type de livraison

- Type de ZIP : installation complète de référence
- Depuis V2.6 : mise à jour web possible, mais une réinstallation complète est recommandée si l’installation est cassée
- Après V2.7 : les corrections mineures pourront à nouveau passer par LP Core > Mises à jour

## Objectif

Permettre, après crash serveur, de repartir d’un serveur Debian neuf :

1. installer Docker ;
2. déployer la suite ;
3. lancer `./install.sh` ;
4. ouvrir LP Core ;
5. aller dans **Sauvegardes** ;
6. déposer une sauvegarde journalière complète ;
7. restaurer ;
8. retrouver l’état avant crash.

## Contenu d’une sauvegarde complète

- `.env` ;
- bases et données des modules ;
- médias et fichiers joints ;
- certificats SSL ;
- imports ;
- logs techniques ;
- `manifest.json` ;
- `checksums.sha256`.

## Conservation

La conservation par défaut est de 90 jours : `BACKUP_RETENTION_DAYS=90`.

## Sauvegarde journalière

Le service Docker `suite-backup-scheduler` crée automatiquement une sauvegarde quotidienne à l’heure définie par `BACKUP_DAILY_HOUR=02`.
