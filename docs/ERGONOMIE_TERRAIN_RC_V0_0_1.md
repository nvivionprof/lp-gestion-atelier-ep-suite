# Ergonomie terrain V0.0.1-RC1

## Règle générale

La suite n’a pas vocation à être entièrement optimisée téléphone pour la RC.

- **PC / tablette** : 99 % de l’usage de gestion.
- **Téléphone** : uniquement actions terrain rapides.

## Usage téléphone obligatoire

### System Manager — prise de poste

Le parcours téléphone doit permettre :

1. scanner ou ouvrir le QR code système ;
2. voir nom, code, photo et état du système ;
3. lancer la prise de poste ;
4. choisir l’état au démarrage ;
5. ajouter une observation courte ;
6. ajouter éventuellement une photo ;
7. valider.

Critère : la prise de poste doit être faisable en moins d’une minute.

### ToolMag — inventaire utilisateur

Le parcours téléphone doit permettre :

1. scanner ou ouvrir la fiche inventaire ;
2. voir le matériel et ses composants ;
3. cocher présent / absent / à contrôler ;
4. ajouter un commentaire ;
5. valider l’inventaire.

Critère : les boutons et cases doivent être lisibles et utilisables au doigt.

### Photos

Pour ToolMag et System Manager, les champs photo doivent proposer explicitement :

- **Prendre une photo** ;
- **Choisir une photo**.

Les champs photo doivent utiliser une logique compatible avec l’appareil photo mobile :

```html
<input type="file" accept="image/*" capture="environment">
```

ou le widget JS `camera_upload.js` déjà intégré.

## Usage PC / tablette

Sont prévus prioritairement sur PC / tablette :

- administration ;
- création complète des fiches ;
- paramétrage ;
- sauvegardes ;
- supervision ;
- PedaShop ;
- documents ;
- réservations ;
- imports.

## Non prioritaire mobile en RC

- PFMP ;
- TP Manager ;
- Safety Manager ;
- PedaShop complet ;
- supervision bases ;
- administration utilisateurs ;
- réservations avancées.
