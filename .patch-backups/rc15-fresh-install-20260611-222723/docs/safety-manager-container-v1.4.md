# Safety Manager V1.4 — conteneur séparé

Safety Manager n’est plus intégré dans LP Core. Il dispose de son propre conteneur `safety-app`, de son stockage `safety-db/data/` et de son port public par défaut `9002`.

## Accès

```text
LP Core : http://HOST:9000
ToolMag : http://HOST:9001
Safety : http://HOST:9002
```

## Synchronisation utilisateurs

Safety récupère les utilisateurs depuis l’API LP Core, comme ToolMag :

```bash
docker compose exec -T safety-app python manage.py sync_lp_core_users
```

Depuis l’interface Safety, un administrateur peut aussi utiliser le bouton `Synchroniser LP Core → Safety`.

## Upgrade-safe

`upgrade.sh` demande maintenant si les URL/ports doivent être conservés ou modifiés. Cela évite de rester bloqué sur une ancienne IP comme `192.168.104.15` lors d’un test local.

Pour tester sur la machine locale, choisir :

```text
Adresse ou nom DNS public : localhost
LP Core : 9000
ToolMag : 9001
Safety : 9002
```
