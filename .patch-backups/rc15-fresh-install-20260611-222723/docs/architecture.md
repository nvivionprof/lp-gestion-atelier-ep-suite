# Architecture

```text
LP Gestion Atelier EP Suite
├── lp-core-app      port public 9000 par défaut
├── toolmag-app      port public 9001 par défaut
├── safety-app       port public 9002 réservé
├── consumables-app  port public 9003 réservé
├── inventory-app    port public 9004 réservé
└── tpmanager-app    port public 9005 réservé
```

Les ports publics sont configurés dans `.env` par le script `install.sh`.
Les applications Django restent exposées en interne sur `8000` dans chaque conteneur.
