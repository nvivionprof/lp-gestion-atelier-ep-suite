# API LP Core

Toutes les routes API protégées utilisent l'en-tête :

```http
X-API-Key: valeur_de_LP_CORE_API_TOKEN
```

## Santé

```http
GET /api/health/
```

## Utilisateurs

```http
GET /api/users/
GET /api/users/{id}/
```

Exemple de réponse :

```json
{
  "results": [
    {
      "id": 1,
      "code": "MELEC-DUP-LUC",
      "username": "MELEC-DUP-LUC",
      "first_name": "Lucas",
      "last_name": "DUPONT",
      "formation_code": "MELEC",
      "class_name": "1MELEC",
      "group_name": "A",
      "role_principal": "utilisateur",
      "rights": "UTILISATEUR;MAGASINIER",
      "active": true
    }
  ]
}
```

## Classes et formations

```http
GET /api/classes/
GET /api/formations/
```
