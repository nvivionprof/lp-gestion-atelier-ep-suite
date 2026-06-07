# Hotfix V0.4.0c — Domaine public, agent certificat et liens internes

## Objectif

Corriger deux situations :

1. `cert_manager.sh` lancé depuis LP Core échoue car l'environnement agent ne trouve pas `docker`.
2. Après passage d'une IP privée à un domaine DuckDNS, certains liens internes continuent d'utiliser l'ancienne IP.

## Corrections

- `suite-admin-agent` embarque Docker CLI, Docker Compose plugin et lego.
- DNS-01 DuckDNS utilise lego directement, sans dépendre de `docker run`.
- `apply_public_settings.sh` recrée les conteneurs applicatifs pour recharger `.env`.
- LP Core et System Manager reconstruisent les liens de navigation depuis le domaine réellement utilisé lorsque les anciennes variables contiennent une IP privée.
