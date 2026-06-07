# ToolMag V21 — version corrigée

Cette version reprend la V20 et corrige l’affichage de version qui restait marqué V19 dans certains templates.

## Points inclus

- Inventaire utilisateur de sortie pour matériel composé disponible.
- Inventaire utilisateur de retour pour matériel composé déjà sorti.
- Lien vers la fiche matériel depuis les pages d’inventaire utilisateur.
- Documents associés au matériel : notice, fiche de prise en main, consignes de sécurité, maintenance, autre.
- QR code matériel orienté vers le parcours d’inventaire utilisateur.
- Affichage visible : ToolMag V21.

## Vérification

Après reconstruction Docker :

```powershell
docker exec -it toolmag_web cat VERSION.txt
```

Résultat attendu :

```text
ToolMag V21 — inventaire utilisateur sortie/retour + documents matériel + correction affichage version — 2026-05-17
```
