# ToolMag V18 — Inventaires utilisateur et terminaux autorisés

## Inventaire utilisateur de sortie
1. Connecter l'utilisateur : `/utilisateur/login/`.
2. Scanner ou ouvrir la page de contrôle du matériel : `/materiels/<CODE>/controle/`.
3. Cliquer sur **Faire l'inventaire utilisateur de sortie**.
4. L'utilisateur coche les composants présents/absents, indique l'état et soumet.
5. Le magasinier ouvre `/sortie/?equipment=<CODE>` : l'inventaire utilisateur est visible et préremplit la checklist.
6. Le magasinier valide la sortie. L'utilisateur reste l'auteur de l'inventaire, le magasinier reste l'auteur de la validation.

## Inventaire utilisateur de retour
1. Le matériel doit déjà être sorti au nom de l'utilisateur connecté.
2. L'utilisateur ouvre la page de contrôle et clique sur **Faire l'inventaire utilisateur de retour**.
3. Il soumet son contrôle.
4. Le magasinier ouvre `/retour/?equipment=<CODE>` : la checklist est préremplie.
5. Le magasinier statue : disponible, incomplet, maintenance ou hors service.

## Terminaux autorisés
1. Se connecter comme magasinier avec rôle `RESPONSABLE` ou `ADMIN`.
2. Depuis le PC ou la tablette à autoriser, ouvrir `/terminaux/enregistrer/`.
3. Donner un nom au terminal, par exemple `Tablette magasin 1`.
4. Cocher `Autoriser ouverture casiers` si le terminal peut ouvrir les casiers.
5. Valider : ToolMag génère un token et le stocke dans le navigateur.
6. Le terminal apparaît dans `/terminaux/` et dans l'administration.

Si les cookies du navigateur sont supprimés, le terminal doit être réenregistré.
