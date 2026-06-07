# Checklist de tests avant livraison

## Démarrage

```bash
docker compose up -d --build
docker compose ps
```

Tous les services doivent être `Up`. Aucun module ne doit être en `Restarting`.

## Tests HTTP minimum

```bash
curl -I http://localhost:9000/
curl -I http://localhost:9000/toolmag/
curl -I http://localhost:9000/safety/
curl -I http://localhost:9000/pedashop/
curl -I http://localhost:9000/system/
curl -I http://localhost:9000/tpmanager/
curl -I http://localhost:9000/pfmp/
```

Acceptable : `200`, `302`, `403` selon authentification.  
Non acceptable : `500`, `502`.

## LP Core

- Connexion `admin/admin` au premier démarrage.
- Changement de mot de passe demandé.
- Page `URLs / HTTPS` accessible.
- Enregistrement domaine public sans ports par module.
- Génération des URLs par chemins : `/toolmag`, `/system`, etc.

## System Manager

- Liste systèmes accessible.
- Fiche système accessible.
- Documents visibles/téléchargeables selon droits.
- Affichage dynamique plein écran accessible.
- Checks de prise de poste non précochés.
- Restitution disponible si session ouverte.

## Médias

- Une photo système doit s’afficher.
- Un document PDF doit s’ouvrir via `/system/media/...`.
- Un document Office doit conserver l’original et générer une prévisualisation PDF si LibreOffice est disponible.

## Certificats / DuckDNS

- `suite-admin-agent` démarre.
- `cert_manager.sh status` ne doit pas échouer pour cause de commande absente.
- En production, vérifier les redirections 80/443 côté box/routeur.

## Logs à consulter en cas d’erreur

```bash
docker compose logs --tail=200 lp-core-app
docker compose logs --tail=200 system-manager-app
docker compose logs --tail=200 lp-gateway
docker compose logs --tail=200 suite-admin-agent
```
