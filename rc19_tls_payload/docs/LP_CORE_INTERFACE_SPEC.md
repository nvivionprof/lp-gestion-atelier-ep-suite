# Spécification LP Core — Méthode certificats RC19

## Menu LP Core

Ajouter dans LP Core :

```text
Administration > Système > Certificats HTTPS
```

## Page de configuration

### Bloc état

Afficher :

```text
Mode actuel : manual / duckdns-acme / disabled / selfsigned
Domaine externe : stjo-lpsuite.duckdns.org
Certificat présent : oui/non
Sujet certificat
Émetteur
Date début
Date expiration
Nombre de jours restants
Correspondance certificat / clé : OK/KO
Dernière opération TLS
```

### Bloc mode manuel lycée

Champs :

```text
- upload fullchain.pem
- upload privkey.pem
- bouton Vérifier
- bouton Installer
```

Action serveur :

```bash
./scripts/tls-manual-install.sh <cert> <key>
```

### Bloc DuckDNS

Champs :

```text
- domaine DuckDNS : stjo-lpsuite
- domaine complet : stjo-lpsuite.duckdns.org
- token DuckDNS : masqué
- email Let's Encrypt
- délai DNS
- bouton Tester API DuckDNS
- bouton Générer certificat
- bouton Renouveler certificat
```

Actions serveur :

```bash
./scripts/tls-duckdns-issue.sh
./scripts/tls-duckdns-renew.sh
```

### Bloc test local

```text
- générer certificat auto-signé
```

À afficher avec avertissement fort : test uniquement.

## Droits LP Core

Prévoir :

```text
core_tls_view
core_tls_manage_manual
core_tls_manage_duckdns
core_tls_run_operations
```

## Journalisation

Chaque action doit créer une entrée :

```text
- utilisateur
- date
- mode
- action
- résultat
- sortie courte
- IP de l'utilisateur
```
