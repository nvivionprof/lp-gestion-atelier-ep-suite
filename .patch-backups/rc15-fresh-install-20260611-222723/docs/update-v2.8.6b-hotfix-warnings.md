# LP Gestion Atelier EP Suite v2.8.6b — Hotfix avertissements TP Manager

Correctifs :

- ajout de la migration `0007` pour supprimer l’avertissement Django indiquant que des changements de modèles ne sont pas reflétés dans une migration ;
- synchronisation des formations LP Core → TP Manager rendue idempotente pour éviter les erreurs `UNIQUE constraint failed: tp_manager_formation.code` ;
- dépendances HTTP TP Manager figées (`urllib3`, `charset-normalizer`, `chardet`) pour supprimer le `RequestsDependencyWarning` ;
- sauvegarde pré-upgrade plus propre : si un conteneur est en redémarrage, le dump SQLite correspondant est signalé comme ignoré au lieu d’afficher une erreur Docker brute.

Type : mise à jour SSH, compatible `upgrade_module.sh tpmanager`.
