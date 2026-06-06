# Reverse proxy

Le reverse proxy expose uniquement le port public `9000` côté hôte.

Les modules sont routés par chemins :

```text
/              → LP Core
/toolmag/      → ToolMag
/safety/       → Safety Manager
/systemes/     → System Manager
/tp/           → TP Manager
/pedashop/     → PedaShop
/pfmp/         → PFMP Manager
```

Les services Django restent sur le réseau Docker interne et écoutent typiquement sur `8000`.
