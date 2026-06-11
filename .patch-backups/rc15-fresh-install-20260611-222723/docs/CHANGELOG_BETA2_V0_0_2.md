# Bêta 2 V0.0.2 — Corrections LP Core avant migration Git

## Objectif

Cette version corrige deux points identifiés après la Bêta 2 V0.0.1 :

1. LP Core doit conserver un choix explicite entre les profils d'accès : local, réseau interne et domaine extérieur.
2. La gestion photo / RGPD ne doit pas laisser un profil incohérent avec une photo chargée mais un statut RGPD non renseigné sans information claire.

## URLs et profils d'accès

La suite reste derrière une passerelle unique. Les modules ne sont plus exposés par des ports publics séparés :

- `/toolmag/`
- `/safety/`
- `/pedashop/`
- `/system/`
- `/tpmanager/`
- `/pfmp/`

Mais LP Core permet maintenant de choisir le point d'entrée actif :

- Local : `localhost:9000`
- Réseau : `192.168.x.x:9000` ou nom DNS interne
- Domaine extérieur : `stjoseph-lpsuite.duckdns.org`

Les QR codes et liens internes sont générés depuis le profil actif.

## RGPD / photo

Corrections :

- le formulaire Mon compte permet de renseigner le statut droit à l'image ;
- si une photo est ajoutée sans opposition ni refus, LP Core positionne l'autorisation image lorsqu'elle était encore non renseignée ;
- si une photo est présente mais non visible, le message indique clairement que le profil RGPD est non renseigné.

## Migration

Ajout migration LP Core :

- `0012_beta2_access_modes_rgpd_photo.py`

Elle ajoute :

- `local_public_host`
- `network_public_host`
- `external_public_domain`

à `PublicSuiteSettings`.
