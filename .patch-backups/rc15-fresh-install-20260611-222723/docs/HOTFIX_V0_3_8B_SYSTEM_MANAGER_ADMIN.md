# Hotfix V0.3.8b — System Manager admin

Correction du crash Django System Manager au démarrage :

```text
admin.E124 — list_editable[0] pointe vers le premier champ list_display.
```

Fichier corrigé :

```text
system-manager-app/system_manager/admin.py
```

Correction appliquée : ajout de `list_display_links = ('libelle',)` dans `DefaultCheckTemplateAdmin`.

Ce hotfix ne modifie pas les modèles ni les migrations.
