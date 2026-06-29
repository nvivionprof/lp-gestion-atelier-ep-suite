# Player Raspberry LP Display Manager v0.1

Ce dossier contient un player minimal pour Raspberry Pi 3B.

## Principe

- `lp-kiosk.service` lance Chromium en plein écran.
- `lp-display-agent.service` envoie un heartbeat régulier.
- La page affichée est :

```text
http://<serveur>:9000/lpdisplaymanager/player/<TOKEN_PLAYER>/
```

## Installation

```bash
sudo ./install-player.sh http://<serveur>:9000/lpdisplaymanager <TOKEN_PLAYER>
```

Exemple :

```bash
sudo ./install-player.sh http://192.168.1.20:9000/lpdisplaymanager AbCdEf123456
```
