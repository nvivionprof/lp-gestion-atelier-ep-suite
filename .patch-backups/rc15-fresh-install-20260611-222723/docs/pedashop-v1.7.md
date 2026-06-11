# PedaShop V1.7 — bons, alertes et identité visuelle

## Identité visuelle

- Logo PedaShop intégré depuis le visuel fourni.
- Thème PedaShop bleu / vert avec accent orange.
- Bandeau supérieur cohérent avec ToolMag, mais différencié par un dégradé bleu nuit → vert.
- Tuile LP Core mise à jour avec le logo PedaShop fourni.

## Règles métier intégrées

### Visibilité

- Le stock est visible par tous les utilisateurs connectés.
- Les demandes, préparations, statuts, réclamations et retours attendus sont visibles par tous.
- Le traitement dépend du mode actif : utilisateur ou magasinier.

### Connexion

Un même élève peut se connecter :

- en mode utilisateur ;
- en mode magasinier s’il possède les droits correspondants.

### Bons multi-articles

Les demandes et bons acceptent plusieurs articles. La recherche article peut être filtrée par :

- texte ;
- fabricant ;
- catégorie ;
- sous-catégorie ;
- magasin ;
- numéro de marché ;
- disponibilité ;
- substituable.

### Pré-réservation professeur / projection pédagogique

Un professeur peut créer une pré-réservation liée à :

- un professeur ;
- un TP ;
- une classe ;
- une période ;
- un magasin ;
- un ou plusieurs articles.

Lorsqu’une demande élève correspond au même professeur + TP + magasin + article, elle consomme le solde de la pré-réservation au lieu de créer une double réservation.

### Alertes stock

Statuts calculés :

- `SOUS_STOCK_MINI` : jaune ;
- `ZERO_PAR_RESERVATION` : orange foncé ;
- `RUPTURE_TEMPORAIRE_RETOUR_PREVU` : orange foncé ;
- `RUPTURE_REELLE` : rouge ;
- `STOCK_NEGATIF_AVEC_RESERVATION` : rouge.

Commande :

```bash
python manage.py pedashop_recalculate_stock_alerts
```

### Consultation fournisseur

Depuis la page alertes :

1. filtrer les alertes ;
2. tout cocher / tout décocher dans le filtre ;
3. créer une consultation fournisseur ;
4. éditer les lignes ;
5. générer le PDF.

Le PDF contient uniquement :

- désignation ;
- fabricant ;
- référence constructeur ;
- quantité souhaitée ;
- équivalence possible oui/non.

## Migration

La version ajoute une migration :

```text
pedashop/migrations/0002_pedashop_v17_workflows_alerts.py
```

Les données existantes sont conservées. L’upgrade-safe protège toujours :

- `.env` ;
- `lp-core-db/data/` ;
- `toolmag-db/data/` ;
- `safety-db/data/` ;
- `pedashop-db/data/` ;
- `backups/` ;
- `imports/`.
