# Composant caméra/photo mobile

`camera_upload.js` est la source de référence du composant utilisé dans tous les modules.

But : remplacer le comportement mobile peu fiable d'un simple champ `input type=file accept=image/* capture=environment` par deux actions explicites :

- **Prendre une photo** : active un champ fichier avec `capture=environment` ;
- **Choisir une photo** : active le champ fichier galerie classique.

Après modification de ce fichier, recopier la version dans :

```text
lp-core-app/core/static/core/camera_upload.js
toolmag-app/inventory/static/inventory/camera_upload.js
safety-app/safety_manager/static/safety_manager/camera_upload.js
pedashop-app/pedashop/static/pedashop/camera_upload.js
system-manager-app/system_manager/static/system_manager/camera_upload.js
tpmanager-app/tp_manager/static/tp_manager/camera_upload.js
```
