# LP Gestion Atelier Suite — RC19 TLS Cert Manager

Paquet d'intégration pour ajouter dans **LP Core** une gestion des certificats HTTPS compatible :

- mode **DuckDNS + Let's Encrypt DNS-01** via `acme.sh` ;
- mode **certificat manuel établissement** fourni par le lycée / collectivité ;
- mode **auto-signé test local** ;
- statut certificat visible dans LP Core ;
- dépôt standardisé des certificats dans `./certs/manual/` ;
- aucun secret commité dans GitHub.

## Type de livraison

Cette évolution est une **installation complète / évolution SSH RC19**, pas une simple mise à jour web, car elle touche :

- la configuration TLS du reverse proxy ;
- le `.env` ;
- les scripts serveur ;
- l'interface LP Core ;
- les volumes Docker de certificats.

## Accès applicatif inchangé

La règle reste :

```text
https://<domaine-ou-ip>:9000/
https://<domaine-ou-ip>:9000/lpdisplaymanager
```

Pas de port applicatif additionnel pour les modules.

## Modes HTTPS prévus

```env
HTTPS_MODE=disabled        # HTTP local uniquement
HTTPS_MODE=manual          # certificat fourni par le lycée
HTTPS_MODE=duckdns-acme    # Let's Encrypt via DuckDNS DNS-01
HTTPS_MODE=selfsigned      # test local uniquement
```

## Fichiers sensibles à ne jamais pousser

```text
.env
certs/manual/fullchain.pem
certs/manual/privkey.pem
certs/acme/
```

Le fichier `.gitignore` fourni bloque ces éléments.
