# LP Gestion Atelier EP Suite v2.9.3 — Sequence Manager V1

Type : mise à jour SSH complète, compatible avec upgrade par module `tpmanager`.

Cette version ajoute un module applicatif distinct `sequence_manager` dans le service `tpmanager-app`.

## Ajouts principaux

- Tableau de bord Sequence Manager.
- Calendrier global des séquences filtrable par zone et formation.
- Séquences avec zone principale, coloration, axe, durée en semaines, créneaux demi-journée.
- Blocs de rotation et créneaux hebdomadaires.
- Formations/classes concernées par séquence.
- Vagues de présence : groupe fixe, vague courte, parcours libre, PFMP.
- Groupes élèves : solo, binôme, trinôme, groupe, mixte, parcours libre.
- Planning de rotation : lignes = groupes/élèves, colonnes = séances datées.
- Affectations multiples par créneau : TP, système, zone, professeur, mode.
- Parcours libre : catalogue TP filtré par diplôme, thématique, compétence et système.
- Réservations systèmes de séquence côté Sequence Manager.
- Vue compétences travaillées par classe, en mode compact ou détaillé avec critères.
- Duplication de séquence : conserve structure, séances, TP et rotation ; réinitialise les élèves.

## Commandes

```bash
./upgrade.sh /chemin/lp-gestion-atelier-ep-suite-v2.9.3-sequence-manager-v1.zip
```

ou uniquement TP Manager / Sequence Manager :

```bash
./upgrade_module.sh tpmanager /chemin/lp-gestion-atelier-ep-suite-v2.9.3-sequence-manager-v1.zip
```

Puis :

```bash
docker compose exec -T tpmanager-app python manage.py migrate --noinput
docker compose exec -T tpmanager-app python manage.py seed_sequence_manager
docker compose exec -T tpmanager-app python manage.py check
```

## Accès

- `http://localhost:9005/sequence-manager/`
- `http://localhost:9005/sequence-manager/calendrier/`
- `http://localhost:9005/sequence-manager/sequences/`
