# LP Gestion Atelier EP Suite V2.5 — Maintenance web et mises à jour ZIP

## Objectif

Cette version ajoute un **centre de maintenance web** dans LP Core afin de limiter le recours au SSH après la première installation.

Fonctions ajoutées :

- dépôt d’un ZIP de mise à jour depuis le navigateur ;
- analyse du ZIP avant installation ;
- calcul SHA-256 ;
- sauvegarde complète avant installation ;
- installation par script contrôlé ;
- lancement des migrations ;
- redémarrage Docker Compose ;
- boutons web pour appliquer les paramètres publics et gérer les certificats ;
- agent interne `suite-admin-agent`.

## Accès

Dans LP Core :

```text
Administration → URLs / HTTPS
Administration → Mises à jour
```

## Première installation

La première installation reste à faire en SSH :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
chmod +x install.sh start.sh stop.sh scripts/*.sh
./install.sh
```

Ensuite, les opérations courantes peuvent être déclenchées depuis LP Core.

## Agent de maintenance

Le service interne `suite-admin-agent` est ajouté dans `docker-compose.yml`.

Il n’est pas publié sur Internet. Il écoute uniquement dans le réseau Docker de la suite et accepte uniquement les actions prédéfinies :

- `apply_public_settings`
- `issue_cert`
- `renew_cert`
- `cert_status`
- `restart_services`
- `migrate_all`
- `backup_all`
- `install_update`

Il utilise le token interne `LP_CORE_API_TOKEN`.

## Chemin hôte obligatoire

L’agent doit connaître le chemin absolu du projet sur l’hôte pour appeler Docker Compose correctement via `/var/run/docker.sock`.

`install.sh` renseigne automatiquement :

```env
SUITE_HOST_ROOT=/home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
```

Si le projet est déplacé, mettre à jour cette variable dans `.env`.

## Mise à jour par navigateur

Dans LP Core → Mises à jour :

1. déposer le ZIP ;
2. vérifier le rapport d’analyse ;
3. cliquer sur **Installer** ;
4. l’agent lance `scripts/web_upgrade_from_zip.sh`.

Le script :

- refuse les chemins dangereux dans le ZIP ;
- recherche `docker-compose.yml` ;
- lance une sauvegarde ;
- copie les fichiers applicatifs ;
- préserve les dossiers de données ;
- reconstruit les conteneurs ;
- lance les migrations ;
- exécute le contrôle santé.

## Dossiers préservés

Le script n’écrase pas :

```text
.env
ssl/
backups/
logs/
updates/
lp-core-db/
toolmag-db/
safety-db/
pedashop-db/
system-manager-db/
tpmanager-db/
```

## Sécurité

Cette fonction doit rester réservée aux administrateurs LP Core.

En production, garder :

```env
SUITE_ALLOW_WEB_MAINTENANCE=1
```

Pour désactiver les actions serveur depuis l’interface :

```env
SUITE_ALLOW_WEB_MAINTENANCE=0
```

## HTTPS

La page URLs / HTTPS conserve les deux modes :

- HTTP local, sans alerte certificat ;
- HTTPS direct avec certificat Let’s Encrypt partagé.

Challenges disponibles :

- DNS-01 via DuckDNS ;
- HTTP-01 via port 80.
