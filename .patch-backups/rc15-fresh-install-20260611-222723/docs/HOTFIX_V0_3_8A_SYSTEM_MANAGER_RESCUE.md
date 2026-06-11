# Hotfix V0.3.8a — System Manager rescue migrations

Ce hotfix consolide la V0.3.8 lorsque System Manager reste en `Restarting` après une mise à jour interrompue ou incomplète.

Corrections :
- réintègre la chaîne complète de migrations System Manager 0001 → 0006 ;
- recopie l'application System Manager consolidée ;
- lance les checks/migrations avec `docker compose run --rm` pour éviter l'échec de `exec` sur un conteneur en boucle de redémarrage ;
- redémarre uniquement LP Core, System Manager et la passerelle.
