# Architecture technique cible

## Vue globale

LP Gestion Atelier EP Suite est pensée comme une suite modulaire. LP Core joue le rôle de socle commun : authentification, rôles, référentiels, navigation, sauvegardes et paramètres globaux.

Les autres applications peuvent fonctionner comme services séparés mais doivent consommer les données communes exposées ou synchronisées par LP Core.

```text
lp-gestion-atelier-ep-suite/
├── services/
│   ├── lp-core/
│   ├── toolmag/
│   ├── safety-manager/
│   ├── system-manager/
│   ├── tp-manager/
│   ├── pedashop/
│   └── pfmp-manager/
├── infra/
│   ├── nginx/
│   └── certificates/
├── scripts/
├── docs/
└── .github/
```

## Services

### LP Core

Responsabilités :

- authentification globale ;
- rôles et permissions ;
- utilisateurs élèves/professeurs/magasiniers/administrateurs ;
- classes, formations, groupes, blocs atelier ;
- zones et sous-zones atelier ;
- sauvegarde/restauration complète ;
- interface d’administration commune ;
- menu global vers les modules.

### ToolMag

Responsabilités :

- matériel simple et composé ;
- inventaire ;
- sortie/retour outillage ;
- validation magasinier ;
- QR codes ;
- maintenance ;
- armoire sécurisée et casiers.

### Safety Manager

Responsabilités :

- DUERP ;
- unités de travail ;
- familles de risques ;
- évaluations de risques ;
- actions de prévention ;
- événements sécurité ;
- documents et versions.

### System Manager

Responsabilités :

- systèmes techniques ;
- machines d’atelier ;
- zones et sous-zones ;
- classeur numérique ;
- prise de poste QR code ;
- réservation professeur.

### TP Manager

Responsabilités :

- création de TP ;
- référentiels compétences/tâches/savoirs ;
- génération documents élèves/profs ;
- bilans de compétences ;
- droits temporaires élèves contributeurs ;
- listes paramétrables extensibles.

### PedaShop

Responsabilités :

- ressources pédagogiques ;
- documents ;
- médias ;
- éventuellement consommables pédagogiques.

### PFMP Manager

Responsabilités à préciser :

- entreprises ;
- conventions ;
- périodes de stage ;
- suivis ;
- bilans ;
- compétences observées.

---

## Réseau et ports

| Service | Port local | Usage |
|---|---:|---|
| lp-core | 9000 | portail principal |
| toolmag | 9001 | outillage |
| safety-manager | 9002 | sécurité |
| system-manager | 9003 | systèmes |
| tp-manager | 9004 | TP |
| pedashop | 9005 | ressources |

---

## Données persistantes

Les volumes Docker doivent contenir séparément :

- bases de données ;
- médias utilisateurs ;
- exports PDF/DOCX ;
- fichiers élèves importés ;
- certificats ;
- sauvegardes ;
- `.env` et métadonnées de version.

---

## Point d’attention sécurité

Ne jamais versionner :

- `.env` réel ;
- mots de passe ;
- certificats privés ;
- bases de données réelles ;
- sauvegardes contenant des données élèves ;
- médias élèves non anonymisés.
