# LP Gestion Atelier EP Suite — V0.4.0 URLs publiques / DuckDNS / certificats

## Objectif

Cette évolution ajoute une page LP Core pour modifier les URLs publiques de toute la suite après installation. Elle sert notamment au passage d'une installation faite avec une adresse IP privée vers un domaine DuckDNS public.

Page LP Core :

```text
/parametres-publics/
```

## Fonctionnalités

- Domaine public centralisé : exemple `stjoseph-lpsuite.duckdns.org`.
- Choix HTTP / HTTPS.
- Choix du mode d'exposition : reverse proxy recommandé.
- Génération des URLs publiques pour :
  - LP Core
  - ToolMag
  - Safety Manager
  - PedaShop
  - System Manager
  - TP Manager
  - PFMP Manager
- Écriture d'un fichier `lp-core-db/data/cert-manager.env`.
- Bouton pour appliquer les URLs dans `.env`.
- Bouton pour générer / renouveler le certificat Let's Encrypt.
- Correction du script `cert_manager.sh` : message clair si Docker CLI est absent.
- Reconstruction de `suite-admin-agent` avec Docker CLI disponible.

## Procédure type

1. Installer le patch V0.4.0.
2. Ouvrir LP Core > URLs / HTTPS.
3. Renseigner le domaine DuckDNS, le protocole, l'e-mail Let's Encrypt et le token DuckDNS.
4. Enregistrer.
5. Cliquer sur `Appliquer les URLs dans .env`.
6. Cliquer sur `Générer le certificat`.
7. Redémarrer la suite si demandé.

## Remarque

Pour que la génération DNS-01 DuckDNS fonctionne depuis l'interface web, le conteneur `suite-admin-agent` doit avoir été reconstruit avec cette version.
