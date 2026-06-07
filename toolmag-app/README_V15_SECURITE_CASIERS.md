# ToolMag V15 — armoires sécurisées

## Principe

Les fiches matériel ne contiennent aucune URL de contrôleur. Elles contiennent seulement :

- stocké en armoire sécurisée : oui/non ;
- numéro d'armoire ;
- numéro de casier.

Le navigateur appelle ToolMag via `/api/casiers/ouvrir/`. ToolMag vérifie :

1. module armoires activé ;
2. magasinier connecté ;
3. terminal autorisé si l'option est active ;
4. IP publique autorisée si l'option est active ;
5. matériel stocké en armoire sécurisée ;
6. armoire/casier renseignés.

Ensuite seulement, ToolMag exécute le script serveur défini par `LOCKER_POST_SCRIPT`.

## Configuration du script

Créer un fichier `.env` ou définir dans Docker :

```env
LOCKER_POST_SCRIPT=/app/scripts/locker_post_example.py
```

Le script reçoit le JSON sur `stdin`.

## Sauvegarde automatique

Le service Docker `backup` exécute :

```bash
python manage.py backup_toolmag --loop --interval 86400 --retain-days 7
```

Il crée une sauvegarde toutes les 24 h et conserve 7 jours d'historique dans `/app/backups`.
