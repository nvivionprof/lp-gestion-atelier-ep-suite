# QR actions LP Display Manager

## Principe

Un QR code pointe vers :

```text
http://<serveur>:9000/lpdisplaymanager/q/<TOKEN_QR>
```

Le token est associé en base à une action prédéfinie.

## Actions V0.1

### freeze

Fige l'affichage actuel pendant une durée déterminée.

Payload envoyé au player :

```json
{
  "action": "freeze",
  "payload": {
    "target": "all",
    "duration": 60
  }
}
```

### resume

Relance la rotation normale.

```json
{
  "action": "resume",
  "payload": {}
}
```

## Sécurité

Le QR code ne contient jamais les paramètres directs. Il contient uniquement un token.

À éviter :

```text
/lpdisplaymanager/freeze?screen=hall&duration=3600
```

À utiliser :

```text
/lpdisplaymanager/q/8xKf29LqPz
```
