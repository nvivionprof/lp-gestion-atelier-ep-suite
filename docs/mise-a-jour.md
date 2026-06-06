# Politique de mise à jour

## Types d’archives

Chaque future archive ZIP devra indiquer clairement son type :

### 1. Mise à jour web

Applicable depuis l’interface LP Core si :

- elle ne modifie pas l’installation Docker de base ;
- elle ne nécessite pas de reprise SSH ;
- elle est compatible avec la version installée ;
- elle embarque ses migrations et métadonnées de version.

### 2. Installation complète

Nécessite une reprise SSH si :

- elle modifie `docker-compose.yml` ;
- elle change les volumes ;
- elle change les variables d’environnement critiques ;
- elle remplace plusieurs services ;
- elle impose une restauration complète.

## Procédure type depuis `/home`

Exemple cible :

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite
cp /home/update-lp-suite.zip ./updates/
./scripts/apply-update.sh ./updates/update-lp-suite.zip
```

## Avant toute mise à jour

1. Vérifier la version courante.
2. Créer une sauvegarde complète.
3. Vérifier l’espace disque.
4. Lire les notes de version.
5. Appliquer la mise à jour.
6. Lancer les migrations.
7. Vérifier les services.

## Point connu à éviter

Ne pas dupliquer la clé suivante dans `docker-compose.yml` :

```yaml
PEDASHOP_INTERNAL_SYNC_URL
```

Un doublon provoque une erreur YAML de type :

```text
mapping key already defined
```
