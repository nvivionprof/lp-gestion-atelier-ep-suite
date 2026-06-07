# LP Gestion Atelier EP Suite — Bêta V0.3.1a hotfix PFMP template

## Objet

Correction ciblée du module PFMP Manager après l'installation de la V0.3.1 hotfix SSO/sessions/PFMP.

## Problème corrigé

Erreur Django sur `http://localhost:9000/pfmp/` :

```text
TemplateSyntaxError at /
Unclosed tag on line 1: 'block'. Looking for one of: endblock.
```

Cause : le fichier `pfmp-app/pfmp_manager/templates/pfmp_manager/dashboard.html` ouvrait le bloc `{% block content %}` sans le fermer avec `{% endblock %}`.

## Type d'installation

Hotfix PFMP uniquement. Aucune migration de base n'est nécessaire.

## Redémarrage conseillé

```bash
docker compose restart pfmp-app lp-gateway
```

Si le conteneur ne reprend pas la modification :

```bash
docker compose up -d --build pfmp-app lp-gateway
```
