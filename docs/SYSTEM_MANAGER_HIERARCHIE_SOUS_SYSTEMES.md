# System Manager — hiérarchie système / sous-systèmes

## Principe

- Un `EducationalSystem` sans parent est un système principal.
- Un `EducationalSystem` avec `parent_system` est un sous-système.
- La documentation est stockée une seule fois sur le système principal.
- Le sous-système affiche cette documentation par héritage, sans copie de fichier.
- Les équipements restent locaux au système ou au sous-système concerné.
- `toolmag_code` est une référence métier facultative, sans clé étrangère inter-base.

## Restriction V1

Un seul niveau est autorisé : système principal → sous-système.

## Incidence LP Core

Aucune migration, table, vue ou API LP Core n'est modifiée. Le SSO et les
synchronisations utilisateurs, formations, classes, zones et blocs restent inchangés.
La migration concerne uniquement la base PostgreSQL `system_manager`.
