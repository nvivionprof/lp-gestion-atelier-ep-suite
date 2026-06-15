# Sécurité — TLS RC19

## Ne pas versionner

Ne jamais pousser sur GitHub :

```text
DUCKDNS_TOKEN
.env réel
privkey.pem
fullchain.pem
certs/acme/
```

## Risques DuckDNS

Le token DuckDNS permet de modifier les enregistrements DNS/TXT DuckDNS. Il doit être traité comme un secret fort.

## Recommandation établissement

Si le lycée dispose d'une autorité de certification interne, le mode recommandé en production établissement est :

```env
HTTPS_MODE=manual
```

Le mode DuckDNS est utile quand l'établissement ne fournit pas de certificat ou pour une instance accessible par domaine DuckDNS.

## Durée et renouvellement

Les certificats Let's Encrypt sont à durée courte. Le renouvellement doit être automatisé par cron/systemd avec :

```bash
./scripts/tls-duckdns-renew.sh
```

Exemple cron :

```cron
15 3 * * 1 cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite && ./scripts/tls-duckdns-renew.sh >> ./logs/tls-renew.log 2>&1
```
