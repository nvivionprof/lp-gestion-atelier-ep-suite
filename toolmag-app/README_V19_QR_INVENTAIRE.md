# ToolMag V19 — QR inventaire utilisateur automatique

Correctifs principaux :

- L'inventaire utilisateur est réservé aux matériels composés possédant des composants.
- Les matériels simples n'affichent plus les boutons d'inventaire utilisateur.
- Correction de l'erreur d'attribut matériel composé (`COMPOSITE`) : la détection se fait maintenant via les composants déclarés.
- Ajout de l'URL `/materiels/<CODE>/inventaire-utilisateur/` comme point d'entrée QR.
- Le QR code matériel envoie vers cette URL d'inventaire automatique.
- Si aucun utilisateur n'est connecté, ToolMag demande d'abord la connexion utilisateur.
- Si le matériel est disponible, l'utilisateur est envoyé vers l'inventaire de sortie.
- Si le matériel est sorti au nom de l'utilisateur connecté, il est envoyé vers l'inventaire de retour.
- Si le matériel est sorti au nom d'un autre utilisateur, l'inventaire de retour est refusé.

Pour générer les QR codes imprimables avec le bon domaine public :

```env
TOOLMAG_PUBLIC_BASE_URL=https://toolmag-atelier.duckdns.org
```

Puis :

```bash
python manage.py generate_qr
```
