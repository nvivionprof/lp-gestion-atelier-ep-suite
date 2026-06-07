# TP Manager V0.1

Module Django de base documentaire TP.

## Fonctions

- TP modèle unique avec code automatique `CODE_ZONE-CODE_FORMATION-CODE_THEME-INDICE`.
- Documents différenciés : PDF élève, DOCX professeur, corrigés, annexes.
- Filtres formation, niveau, zone, thème, compétence et temps estimé.
- Parcours élève indépendant du document source.
- Traces élèves : texte, photo, fichier, commentaire, réponse.
- Export DOCX brut du compte rendu élève.
- Séquences professeurs et affectation aux élèves.
- Évaluation simple des compétences.
- Liaison System Manager par synchronisation des systèmes pédagogiques.
- Import CSV de référentiel.

## Port

`http://localhost:9005` par défaut.

## Commandes

```bash
docker compose exec -T tpmanager-app python manage.py seed_tp_manager
docker compose exec -T tpmanager-app python manage.py sync_lp_core_users
docker compose exec -T tpmanager-app python manage.py sync_system_manager
```
