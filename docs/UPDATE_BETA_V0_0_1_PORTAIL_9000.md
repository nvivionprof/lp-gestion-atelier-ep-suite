# Bêta V0.0.1 — correctif portail unique port 9000

Ce correctif repart de l'archive `lp-gestion-atelier-ep-suite-beta-v0.0.1-rgpd-sauvegardes.zip`.

## Objectif

- Conserver la logique de portail unique de la bêta.
- Éviter le blocage du port 80/443 en mode production.
- Permettre un accès réseau du type `http://ADRESSE_SERVEUR:9000`.
- Rejouer les synchronisations LP Core → modules après le démarrage complet des conteneurs.

## Installation conseillée

Choisir le mode `reseau`, indiquer l'adresse IP ou le DNS du serveur, puis laisser le port `9000`.

Exemple :

```text
Mode de déploiement [local/reseau] : reseau
Adresse IP ou nom DNS du serveur : 192.168.101.19
Port externe du portail HTTP : 9000
```

Accès :

```text
http://192.168.101.19:9000
```

Modules :

```text
/toolmag
/safety
/pedashop
/system
/tpmanager
```
