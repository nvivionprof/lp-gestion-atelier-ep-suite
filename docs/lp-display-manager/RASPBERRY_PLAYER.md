# Installation player Raspberry Pi

## Prérequis

- Raspberry Pi 3B ou supérieur ;
- Raspberry Pi OS avec environnement graphique ;
- réseau accessible vers LP Suite ;
- alimentation stable ;
- carte microSD fiable.

## Créer l'écran dans LP Display Manager

1. Aller dans `/lpdisplaymanager/screens/`.
2. Créer un écran.
3. Lui affecter un layout.
4. Copier le `player_token`.

## Installer le player

Sur le Raspberry :

```bash
sudo ./install-player.sh http://<serveur>:9000/lpdisplaymanager <TOKEN_PLAYER>
```

## Vérifier

```bash
systemctl status lp-display-agent.service
systemctl status lp-kiosk.service
```

## Logs

```bash
journalctl -u lp-display-agent.service -f
journalctl -u lp-kiosk.service -f
```
