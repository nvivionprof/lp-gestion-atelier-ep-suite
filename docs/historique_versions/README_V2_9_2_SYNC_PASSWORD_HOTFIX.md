# LP Gestion Atelier EP Suite v2.9.2 — correctif synchronisation web + reset mot de passe

## Type de paquet
Installation complète / mise à jour SSH. Compatible avec `upgrade.sh` et avec la mise à jour ciblée selon les modules.

## Correctifs principaux

### LP Core
- Ajout d'un bloc **Réinitialisation du mot de passe** dans la fiche utilisateur.
- Réinitialisation possible par un utilisateur admin/professeur LP Core autorisé.
- Option de forçage de changement du mot de passe à la prochaine connexion LP Core.
- Option de resynchronisation immédiate du mot de passe vers les modules.
- La resynchronisation ciblée ne pousse que l'utilisateur concerné (`core_user_id`) et force le mot de passe uniquement pour cet utilisateur.

### Synchronisation inter-modules
- Timeout web porté à 90 secondes (`MODULE_SYNC_TIMEOUT_SECONDS=90`).
- Double transmission du jeton interne : en en-tête `X-API-Key` et en POST `token`.
- Rapports de synchronisation plus explicites module par module.
- Support des paramètres internes :
  - `core_user_id`
  - `force_password=1`

### ToolMag / PedaShop / Safety / System Manager / TP Manager
- Les endpoints de synchronisation acceptent les appels internes signés par jeton sans session navigateur.
- Les endpoints restent protégés par le jeton `LP_CORE_API_TOKEN`.
- Les synchronisations ciblées par utilisateur sont prises en charge.
- Le mot de passe peut être forcé lors d'une synchronisation ciblée.

## Procédure conseillée

### Mise à jour complète
```bash
./upgrade.sh /chemin/lp-gestion-atelier-ep-suite-v2.9.2-hotfix-sync-password-reset.zip
```

### Si tu veux corriger rapidement LP Core + TP Manager seulement
```bash
./upgrade_module.sh --skip-seed lp-core /chemin/lp-gestion-atelier-ep-suite-v2.9.2-hotfix-sync-password-reset.zip
./upgrade_module.sh --skip-seed tpmanager /chemin/lp-gestion-atelier-ep-suite-v2.9.2-hotfix-sync-password-reset.zip
```

## Après mise à jour
```bash
docker compose exec -T lp-core-app python manage.py check
docker compose exec -T tpmanager-app python manage.py check
```

## Réinitialiser PROF-0001
Dans LP Core :
1. Aller dans **Utilisateurs**.
2. Ouvrir `PROF-0001`.
3. Utiliser **Réinitialisation du mot de passe**.
4. Saisir `prof1234` deux fois.
5. Laisser coché **Resynchroniser immédiatement ce mot de passe vers les modules**.

