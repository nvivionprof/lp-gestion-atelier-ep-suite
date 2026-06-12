# V0.0.1-RC17 — PFMP Manager : édition web, prochaines actions et bilans par période

Type : upgrade classique PFMP Manager. Cette RC17 est complète : elle reprend les éléments RC16 et ajoute les corrections fonctionnelles demandées.

## Ajouts RC17

- Modification manuelle d’une entreprise depuis l’interface web.
- Modification manuelle d’un contact depuis la fiche entreprise.
- Ajout de la prochaine action dès l’ajout initial d’une entreprise à la recherche PFMP.
- Passage des libellés de formulaires PFMP en français.
- Bilan par période PFMP et par classe :
  - élèves avec accord ;
  - élèves sans accord ;
  - nombre d’entreprises sollicitées par élève ;
  - synthèse par classe ;
  - synthèse globale de la période.

## Pages ajoutées / renforcées

- `/pfmp/entreprises/<id>/modifier/`
- `/pfmp/entreprises/<id>/contacts/<id>/modifier/`
- `/pfmp/periodes/<id>/bilan/`
- `/pfmp/mes-recherches/`

## Remarques

La règle de confidentialité est conservée : côté élève, les contacts ne doivent afficher que l’adresse mail autorisée. Les adresses personnelles, téléphones et commentaires internes restent réservés aux professeurs / administrateurs.

Cette RC17 ne nécessite pas de migration supplémentaire par rapport à la RC16 : elle utilise les champs et tables créés par la migration `0002_rc16_pfmp_complete`.
