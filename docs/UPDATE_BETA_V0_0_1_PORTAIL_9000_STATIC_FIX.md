# Correctif portail 9000 — redirections et CSS

Ce correctif stabilise le portail unique sur `http://localhost:9000` ou `http://IP:9000`.

## Corrections

- Redirections relatives `/toolmag -> /toolmag/`, sans perte du port externe.
- Transmission du host complet via `$http_host`, donc conservation de `:9000`.
- URLs publiques des modules avec slash final pour éviter les redirections inutiles.
- Fichiers statiques CSS/JS/images servis directement par `lp-gateway` depuis les dossiers `STATIC_ROOT` collectés :
  - LP Core : `/static/core/`
  - ToolMag : `/static/inventory/`
  - Safety : `/static/safety_manager/`
  - PedaShop : `/static/pedashop/`
  - System Manager : `/static/system_manager/`
  - TP Manager : `/static/tp_manager/`, `/static/evaluation_manager/`, `/static/sequence_manager/`

## Tests attendus

```bash
curl -I http://localhost:9000/toolmag
curl -I http://localhost:9000/toolmag/
curl -I http://localhost:9000/static/inventory/style.css
```

Résultats attendus :

- `/toolmag` : `301 Location: /toolmag/`
- `/toolmag/` : `200 OK` ou redirection de login selon session
- CSS : `200 OK`
