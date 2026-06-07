# Suivi technique — LP Gestion Atelier EP Suite

## Base de rebase

- Nouvelle branche de travail : **Bêta 2 V0.0.2**
- Base technique reprise : **V0.4.0c propre consolidée**
- Objectif : repartir d’une arborescence unique, prête pour Git, et arrêter l’empilement de ZIP/hotfixs sans source de référence.

## Règles critiques à conserver

### Architecture

- Un seul point d’entrée public : `lp-gateway`.
- Un seul domaine ou une seule IP d’accès.
- Modules servis par chemins : `/toolmag`, `/safety`, `/pedashop`, `/system`, `/tpmanager`, `/pfmp`.
- Ne pas réintroduire de ports publics par module dans l’interface LP Core.

### Sessions / cookies

- Cookies de session et CSRF isolés par application.
- Ne pas revenir à `sessionid` / `csrftoken` communs à toute la suite.

### Données

- Les dossiers `*-db/data/` contiennent les bases et médias de production.
- Ils ne doivent pas être versionnés dans Git.
- Toute mise à jour doit préserver les bases sauf procédure de réinstallation explicitement assumée.

### System Manager

Corrections à ne pas casser :

- médias et documents servis via `/system/media/` ;
- affichage dynamique plein écran ;
- checks non précochés ;
- anomalies bloquantes en rouge uniquement ;
- téléchargement original limité aux profils autorisés ;
- conteneurs documentaires repliés par défaut ;
- menu Applications inter-modules ;
- références de modèles Django différées quand nécessaire (`'WorkshopBlock'`, etc.).

### PFMP Manager

Corrections à ne pas casser :

- templates avec blocs correctement fermés ;
- SSO/session isolés ;
- carte entreprises + filtrage distance.

### HTTPS / DuckDNS

- `PublicSuiteSettings` génère des URLs par passerelle unique.
- L’interface LP Core ne propose plus les ports par module.
- Le domaine peut contenir un port uniquement en local, ex. `localhost:9000`.
- En production, utiliser le domaine seul, ex. `stjoseph-lpsuite.duckdns.org`.

## Fichiers de suivi obligatoires

- `SUIVI_TECHNIQUE_SUITE.md` : décisions et points critiques.
- `MIGRATIONS_ETAT.md` : état des migrations par module.
- `CHECKLIST_TESTS.md` : tests minimum avant livraison.
- `GIT_MIGRATION.md` : procédure de passage Git.
- `CHANGELOG_BETA2.md` : historique de Bêta 2.

## Procédure de modification future

1. Créer une branche Git.
2. Modifier les sources.
3. Ajouter ou corriger les migrations.
4. Lancer les vérifications statiques.
5. Mettre à jour les fichiers de suivi.
6. Générer un ZIP seulement depuis la source Git propre.
7. Ne jamais modifier une archive sans reporter la modification dans la source.
