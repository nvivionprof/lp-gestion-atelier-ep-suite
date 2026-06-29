# Architecture LP Display Manager v0.1

```text
LP Core / reverse proxy :9000
 └─ /lpdisplaymanager
     └─ lp-display-manager-app:8000
```

## Flux player

```text
Raspberry Pi
 ├─ Chromium kiosk → /lpdisplaymanager/player/<token>/
 ├─ JS player → manifest toutes les 60 s
 ├─ JS player → commandes toutes les 3 s
 └─ agent Python → heartbeat toutes les 30 s
```

## Choix technique V0.1

- REST/polling plutôt que WebSocket.
- Pas de port externe dédié.
- Pas de SSH complet.
- Média image et web uniquement.
- Layout fixe duplicable.
