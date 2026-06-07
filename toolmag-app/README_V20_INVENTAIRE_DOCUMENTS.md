# ToolMag V20 — inventaire utilisateur sortie/retour + documents matériel

## Corrections / ajouts

- Le QR code matériel reste le point d'entrée unique utilisateur :
  - si le matériel composé est disponible, il envoie vers l'inventaire utilisateur de sortie ;
  - si le matériel composé est déjà sorti par l'utilisateur connecté, il envoie vers l'inventaire utilisateur de retour ;
  - si aucun utilisateur n'est connecté, ToolMag demande d'abord la connexion utilisateur puis revient au bon inventaire.
- L'inventaire utilisateur reste réservé aux matériels composés avec composants déclarés.
- La page d'inventaire utilisateur contient maintenant un lien direct vers la fiche matériel.
- La fiche matériel dispose maintenant d'un espace documents : notice constructeur, fiche de prise en main, consignes de sécurité, fiche maintenance, autre.
- Ces documents sont affichés sur la fiche matériel, la page contrôle et les pages d'inventaire utilisateur.

## Migration

```bash
python manage.py migrate
```

ou avec Docker :

```powershell
docker exec -it toolmag_web python manage.py migrate
```

## QR codes

Après mise à jour de `TOOLMAG_PUBLIC_BASE_URL`, regénérer les QR codes :

```powershell
docker exec -it toolmag_web python manage.py generate_qr
```
