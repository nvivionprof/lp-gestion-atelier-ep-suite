# ToolMag V28 — fiche matériel enrichie + bon d’intervention

## Ajouts

- Affichage de l’emplacement sur la fiche matériel, sous le numéro de série.
- Ajout d’un champ `Descriptif matériel` sur les équipements.
- Recherche inventaire enrichie : code, nom, descriptif, marque, modèle, numéro de série, emplacement, catégorie.
- Colonne `Descriptif` ajoutée dans la page inventaire.
- Génération automatique du code matériel si le champ code est laissé vide dans l’administration Django : préfixe sur 3 lettres de la catégorie/type + indice sur 3 chiffres.
- Nouveau bouton `Bon d’intervention` visible pour le magasinier connecté sur la fiche matériel.
- Nouveau formulaire `/materiels/<CODE>/intervention/` pour tracer un contrôle, nettoyage, reconditionnement, vérification périodique ou maintenance légère, même si le matériel est disponible.
- Historique des bons d’intervention visible sur la fiche matériel.
- Le module réparation / dépannage reste conservé pour les matériels en maintenance, incomplets ou hors service.

## Mise à jour

```powershell
docker compose down
docker rm -f toolmag_web
docker compose build --no-cache
docker compose up -d
docker exec -it toolmag_web python manage.py migrate
docker exec -it toolmag_web python manage.py generate_qr
```

## Vérification

```powershell
docker exec -it toolmag_web cat VERSION.txt
```

Doit afficher :

```text
ToolMag V28 — fiche matériel enrichie + descriptif + bon d’intervention — 2026-05-17
```
