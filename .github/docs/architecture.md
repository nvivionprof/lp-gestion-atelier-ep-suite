# Architecture technique cible

## Vue globale

LP Gestion Atelier EP Suite est pensée comme une suite modulaire. LP Core joue le rôle de socle commun : authentification, rôles, référentiels, navigation, sauvegardes et paramètres globaux.

Les modules ne sont pas publiés sur des ports séparés. L’accès utilisateur passe par un **seul point d’entrée public** :

```text
http://serveur:9000/
```

Les modules sont ensuite accessibles par chemins.

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

---

## Routage public

```text
:9000/              → LP Core
:9000/toolmag/      → ToolMag
:9000/safety/       → Safety Manager
:9000/systemes/     → System Manager
:9000/tp/           → TP Manager
:9000/pedashop/     → PedaShop
:9000/pfmp/         → PFMP Manager
```

> Les anciens ports publics dédiés aux modules sont supprimés.  
> Il ne doit donc plus y avoir d’accès utilisateur du type `:900x` par module

---

## Schéma réseau

```text
Navigateur utilisateur
        │
        ▼
http://serveur:9000
        │
        ▼
reverse-proxy
        │
        ├── /              → lp-core:8000
        ├── /toolmag/      → toolmag:8000
        ├── /safety/       → safety-manager:8000
        ├── /systemes/     → system-manager:8000
        ├── /tp/           → tp-manager:8000
        ├── /pedashop/     → pedashop:8000
        └── /pfmp/         → pfmp-manager:8000
```

Les ports internes `8000` sont réservés au réseau Docker. Ils ne doivent pas être publiés sur l’hôte.

---

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
- consommables pédagogiques si le module est retenu pour ce périmètre.

### PFMP Manager

Responsabilités à préciser :

- entreprises ;
- conventions ;
- périodes de stage ;
- suivis ;
- bilans ;
- compétences observées.

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
