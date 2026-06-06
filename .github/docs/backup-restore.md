# Sauvegarde et restauration complète

## Objectif

Permettre une restauration après crash serveur à partir d’une installation neuve.

Après réinstallation avec `install.sh`, LP Core devra pouvoir réinjecter une sauvegarde journalière complète afin de retrouver l’état exact avant crash.

## Éléments à sauvegarder

- Bases de données.
- Médias utilisateurs.
- Exports PDF/DOCX.
- Certificats.
- Fichier `.env`.
- Métadonnées de version.
- Paramètres des modules.
- Journaux utiles à la reprise.

## Règle de sécurité

Les sauvegardes contenant des données élèves ne doivent jamais être poussées sur GitHub.

## Fréquence cible

- Sauvegarde journalière automatique.
- Conservation courte par défaut : 7 jours.
- Export manuel avant mise à jour.

## Processus de restauration cible

```text
1. Réinstaller le serveur.
2. Cloner ou déployer la même version de LP Suite.
3. Lancer install.sh.
4. Ouvrir LP Core.
5. Importer l’archive de sauvegarde.
6. Restaurer bases, médias, certificats, .env et versions.
7. Redémarrer les services.
8. Contrôler les modules.
```
