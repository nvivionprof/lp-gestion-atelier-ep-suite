# Changelog — Bêta 2

## V0.0.6

- Règle officielle : les bases de démonstration sont proposées uniquement en mode `install`.
- Chargement automatique des démos uniquement pendant l'installation neuve, après migrations.
- Blocage de `--demo` / `--no-demo` en modes `update` et `upgrade`.
- En `update` / `upgrade`, `LOAD_DEMO_DATA` est forcé à `0` pour éviter toute pollution des données existantes.
- Mise à jour de la politique de migration versionnée.

## V0.0.2

- Correction LP Core : choix du profil d’accès actif local / réseau / domaine extérieur.
- Conservation de la passerelle unique : un seul point d’entrée et chemins par module, pas de ports publics séparés par application.
- Correction photo / RGPD : ajout du statut droit à l’image dans Mon compte et positionnement cohérent lors de l’ajout d’une photo autorisée.
- Ajout migration `0012_beta2_access_modes_rgpd_photo.py`.

## V0.0.1

- Rebase propre depuis V0.4.0c.
- Préparation à la migration Git.
- Ajout des fichiers de suivi technique.
- Ajout de `.gitattributes`.
- Renforcement de `.gitignore`.
- Renommage global affiché en Bêta 2 V0.0.1.
- Simplification LP Core > URLs / HTTPS : suppression de la gestion des ports publics par module.
- Génération des liens publics uniquement par passerelle unique et chemins.
